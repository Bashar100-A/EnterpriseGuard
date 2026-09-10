#!/usr/bin/env python3
"""Native connectors for LangSmith and Langfuse to unified agent events."""

import os
import sys
import json
import base64
import requests
from datetime import datetime, timezone, timedelta

sys.dont_write_bytecode = True


def _sanitize(text, max_len=200):
    if not isinstance(text, str):
        return ""
    for key in ["api_key", "password", "secret", "token"]:
        text = text.replace(key, "***")
    return text[:max_len]


def _normalize_langfuse_observation(obs, trace_data=None):
    if trace_data is None:
        trace_data = {}
    metadata = trace_data.get("metadata", {}) or {}
    return {
        "timestamp": obs.get("startTime", ""),
        "agent_id": metadata.get("agent_id", "unknown"),
        "trace_id": obs.get("traceId", ""),
        "run_id": obs.get("id", ""),
        "command": obs.get("name", ""),
        "actor_type": "agent",
        "input_summary": _sanitize(str(trace_data.get("input", ""))),
        "output_summary": _sanitize(str(trace_data.get("output", ""))),
        "latency_ms": obs.get("latency", 0),
    }


def fetch_langfuse_traces(public_key=None, secret_key=None, base_url=None, limit=10):
    """Fetch recent observations from Langfuse v2 API."""
    public_key = public_key or os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = secret_key or os.environ.get("LANGFUSE_SECRET_KEY")
    base_url = base_url or os.environ.get("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        raise ValueError("Langfuse credentials missing")

    auth = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}"}
    to_time = datetime.now(timezone.utc)
    from_time = to_time - timedelta(hours=24)
    params = {"fromStartTime": from_time.isoformat(), "toStartTime": to_time.isoformat(), "limit": limit}
    url = f"{base_url}/api/public/v2/observations"
    resp = requests.get(url, params=params, headers=headers, timeout=20)
    resp.raise_for_status()
    data = resp.json().get("data", [])

    events = []
    for obs in data:
        trace_id = obs.get("traceId", "")
        trace_data = {}
        if trace_id:
            try:
                tr = requests.get(f"{base_url}/api/public/traces/{trace_id}", headers=headers, timeout=10)
                if tr.status_code == 200:
                    trace_data = tr.json()
            except Exception:
                pass
        events.append(_normalize_langfuse_observation(obs, trace_data))
    return events


def _normalize_langsmith_run(run):
    return {
        "timestamp": run.get("start_time", run.get("created_at", "")),
        "agent_id": run.get("metadata", {}).get("agent_id", "unknown"),
        "trace_id": run.get("trace_id", ""),
        "run_id": run.get("id", ""),
        "command": run.get("name", ""),
        "actor_type": "agent",
        "input_summary": _sanitize(str(run.get("inputs", {}))),
        "output_summary": _sanitize(str(run.get("outputs", {}))),
        "latency_ms": run.get("latency", 0),
    }


def fetch_langsmith_traces(api_key=None, project_name=None, limit=10):
    """Fetch recent runs from LangSmith API."""
    api_key = api_key or os.environ.get("LANGSMITH_API_KEY")
    project_name = project_name or os.environ.get("LANGSMITH_PROJECT", "default")
    if not api_key:
        raise ValueError("LangSmith API key missing")
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    # LangSmith API endpoint for listing runs (simplified; may need pagination)
    url = f"https://api.smith.langchain.com/runs?project_name={project_name}&limit={limit}"
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    runs = resp.json()
    # Structure may vary; assume list of runs
    events = [_normalize_langsmith_run(r) for r in runs]
    return events


def unified_fetch(source="auto", limit=10):
    """Fetch events from configured source."""
    source = source or os.environ.get("AAAC_TRACE_SOURCE", "auto")
    if source == "auto":
        # Try Langfuse first if keys present, else LangSmith
        if os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY"):
            source = "langfuse"
        elif os.environ.get("LANGSMITH_API_KEY"):
            source = "langsmith"
        else:
            raise ValueError("No trace source credentials configured")
    if source == "langfuse":
        return fetch_langfuse_traces(limit=limit)
    elif source == "langsmith":
        return fetch_langsmith_traces(limit=limit)
    else:
        raise ValueError(f"Unknown trace source: {source}")


if __name__ == "__main__":
    source = os.environ.get("AAAC_TRACE_SOURCE", "auto")
    events = unified_fetch(source=source, limit=5)
    print(f"Fetched {len(events)} events from {source}")
    if events:
        print(json.dumps(events[0], indent=2, ensure_ascii=False))
