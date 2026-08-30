#!/usr/bin/env python3
"""Read-only alert monitor for EnterpriseGuard project logs.

This tool inspects the project activity and error logs, derives health trends,
and reports system severity without modifying protected implementation files.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = PROJECT_ROOT / "tools"
ACTIVITY_LOG_PATH = TOOLS_DIR / "activity_log.json"
ERROR_LOG_PATH = TOOLS_DIR / "errors.log"


def utc_timestamp() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def ensure_tools_dir() -> None:
    TOOLS_DIR.mkdir(exist_ok=True, parents=True)


def append_activity(event: str) -> None:
    ensure_tools_dir()
    try:
        if ACTIVITY_LOG_PATH.exists():
            with ACTIVITY_LOG_PATH.open("r", encoding="utf-8") as handle:
                try:
                    payload = json.load(handle)
                except json.JSONDecodeError:
                    payload = []
        else:
            payload = []

        if not isinstance(payload, list):
            payload = []

        payload.append({"timestamp": utc_timestamp(), "event": event})
        with ACTIVITY_LOG_PATH.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
    except Exception:
        pass


def log_error(message: str) -> None:
    ensure_tools_dir()
    try:
        with ERROR_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(f"[{utc_timestamp()}] {message}\n")
    except Exception:
        pass


def parse_timestamp(raw: str) -> datetime | None:
    try:
        return datetime.strptime(raw, "%Y-%m-%d %H:%M:%S %Z")
    except ValueError:
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            return None


def read_activity_log() -> list[dict[str, Any]]:
    if not ACTIVITY_LOG_PATH.exists():
        return []
    try:
        with ACTIVITY_LOG_PATH.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return payload if isinstance(payload, list) else []
    except Exception as exc:
        log_error(f"Unable to read activity log: {exc}")
        return []


def read_error_log() -> list[str]:
    if not ERROR_LOG_PATH.exists():
        return []
    try:
        with ERROR_LOG_PATH.open("r", encoding="utf-8") as handle:
            return [line.rstrip() for line in handle if line.strip()]
    except Exception as exc:
        log_error(f"Unable to read error log: {exc}")
        return []


def summarize_activity(entries: list[dict[str, Any]]) -> dict[str, Any]:
    if not entries:
        return {
            "total_events": 0,
            "recent_24h": 0,
            "events_last_7d": 0,
            "latest_event": "No activity recorded",
            "event_types": {},
        }

    now = datetime.now()
    recent_24h = 0
    recent_7d = 0
    event_types: Counter[str] = Counter()

    for entry in entries:
        event_name = str(entry.get("event", "unknown"))
        event_types[event_name] += 1
        ts_value = entry.get("timestamp")
        parsed = parse_timestamp(str(ts_value)) if ts_value else None
        if parsed is not None:
            delta = now - parsed
            if delta <= timedelta(days=1):
                recent_24h += 1
            if delta <= timedelta(days=7):
                recent_7d += 1

    latest_entry = entries[-1]
    return {
        "total_events": len(entries),
        "recent_24h": recent_24h,
        "events_last_7d": recent_7d,
        "latest_event": str(latest_entry.get("event", "No activity recorded")),
        "event_types": dict(event_types.most_common(10)),
    }


def summarize_errors(lines: list[str]) -> dict[str, Any]:
    now = datetime.now()
    recent_24h = 0
    total_errors = len(lines)
    recent_occurrences = []

    pattern = re.compile(r"\[(?P<timestamp>[^\]]+)\]")
    for line in lines:
        match = pattern.search(line)
        if not match:
            continue
        parsed = parse_timestamp(match.group("timestamp"))
        if parsed is None:
            continue
        delta = now - parsed
        if delta <= timedelta(days=1):
            recent_24h += 1
            recent_occurrences.append(line)

    return {
        "total_errors": total_errors,
        "recent_24h": recent_24h,
        "recent_occurrences": recent_occurrences,
    }


def determine_severity(error_summary: dict[str, Any], activity_summary: dict[str, Any]) -> str:
    recent_errors = error_summary["recent_24h"]
    total_errors = error_summary["total_errors"]
    recent_activity = activity_summary["recent_24h"]

    if total_errors >= 10 or recent_errors >= 5:
        return "ALERT"
    if total_errors >= 3 or recent_errors >= 2 or recent_activity == 0:
        return "NOTICE"
    return "HEALTHY"


def build_report() -> dict[str, Any]:
    activity_summary = summarize_activity(read_activity_log())
    error_summary = summarize_errors(read_error_log())
    severity = determine_severity(error_summary, activity_summary)

    report = {
        "severity": severity,
        "activity_summary": activity_summary,
        "error_summary": error_summary,
        "generated_at": utc_timestamp(),
    }
    return report


def print_report(report: dict[str, Any]) -> None:
    print("\n=== EnterpriseGuard Alert Monitor ===")
    print(f"Severity: {report['severity']}")
    print(f"Generated at: {report['generated_at']}")
    print("-----------------------------------")
    print(f"Total activity events: {report['activity_summary']['total_events']}")
    print(f"Activity in last 24h: {report['activity_summary']['recent_24h']}")
    print(f"Activity in last 7d: {report['activity_summary']['events_last_7d']}")
    print(f"Latest event: {report['activity_summary']['latest_event']}")
    print(f"Total logged errors: {report['error_summary']['total_errors']}")
    print(f"Errors in last 24h: {report['error_summary']['recent_24h']}")
    if report['error_summary']['recent_occurrences']:
        print("Recent error sample:")
        for item in report['error_summary']['recent_occurrences'][:3]:
            print(f"  - {item}")
    else:
        print("Recent error sample: none")

    if report['activity_summary']['event_types']:
        print("Top event types:")
        for name, count in report['activity_summary']['event_types'].items():
            print(f"  - {name}: {count}")

    print("===================================\n")


def main() -> int:
    ensure_tools_dir()
    report = build_report()
    print_report(report)

    append_activity(f"Alert monitor run: {report['severity']}")

    if report["severity"] == "ALERT":
        log_error(f"ALERT: Log spike detected by alerts_monitor. Error count in last 24h = {report['error_summary']['recent_24h']}.")
        print("Alert threshold exceeded: critical log spike detected.")
        return 1

    if report["severity"] == "NOTICE":
        print("Notice: elevated activity or error count detected; review logs for context.")
        return 0

    print("System health looks stable. No active alert conditions detected.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover
        log_error(f"Unexpected alert monitor execution error: {exc}")
        append_activity("Alert monitor run: FAILURE (unexpected execution error)")
        print(f"Unexpected error: {exc}")
        raise SystemExit(1)
