#!/usr/bin/env python3
"""Collect events from auditd, syslog, or a synthetic fallback."""

import argparse
import json
import os
import pathlib
import subprocess
import sys
import time

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.paths_config import REALTIME_EVENTS_PATH, ACTIVITY_LOG_PATH


def _timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_auditd_events() -> list[dict]:
    """Read recent AVC events from auditd when ausearch is available."""
    try:
        result = subprocess.run(
            ["ausearch", "-m", "avc", "-ts", "recent"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (FileNotFoundError, OSError, subprocess.SubprocessError):
        return []

    if result.returncode != 0:
        return []

    events = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line:
            events.append(
                {
                    "timestamp": _timestamp(),
                    "event_type": "AUDITD_AVC",
                    "message": line,
                    "source": "auditd",
                }
            )
    return events


def read_syslog_events() -> list[dict]:
    """Read the last 100 syslog lines when /var/log/syslog exists."""
    syslog_path = pathlib.Path("/var/log/syslog")
    if not syslog_path.exists():
        return []

    try:
        result = subprocess.run(
            ["tail", "-n", "100", str(syslog_path)],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (FileNotFoundError, OSError, subprocess.SubprocessError):
        return []

    if result.returncode != 0:
        return []

    events = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line:
            events.append(
                {
                    "timestamp": _timestamp(),
                    "event_type": "SYSLOG",
                    "message": line,
                    "source": "syslog",
                }
            )
    return events


def generate_synthetic_event() -> dict:
    """Return a safe event for environments without a readable event source."""
    return {
        "timestamp": _timestamp(),
        "event_type": "SYNTHETIC",
        "message": "No real event source was available",
        "source": "event_source_adapter",
    }


def write_events(events: list[dict]) -> int:
    """Append events as JSONL using an O_APPEND file descriptor."""
    if not events:
        return 0

    path = pathlib.Path(REALTIME_EVENTS_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    written = 0
    try:
        descriptor = os.open(path, flags, 0o600)
        try:
            for event in events:
                payload = (json.dumps(event, sort_keys=True) + "\n").encode("utf-8")
                os.write(descriptor, payload)
                written += 1
        finally:
            os.close(descriptor)
    except OSError:
        return written
    return written


def log_activity(event: str, event_count: int = 0) -> None:
    """Record adapter lifecycle activity in the chained activity log."""
    try:
        from tools.audit_chain import append_activity
        from tools.time_utils import utc_now

        append_activity(
            {
                "timestamp": utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "activity_type": "event_source_adapter",
                "event": event,
                "details": f"{event}; event_count={event_count}",
                "status": "success",
            },
            ACTIVITY_LOG_PATH,
        )
    except Exception as exc:
        print(f"WARNING: failed to log adapter activity: {exc}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect EnterpriseGuard source events")
    parser.add_argument("--mode", choices=("auto", "auditd", "syslog", "synthetic"), default="auto")
    args = parser.parse_args()

    log_activity(f"adapter_start mode={args.mode}")
    events = []
    if args.mode in ("auto", "auditd"):
        events = read_auditd_events()
    if not events and args.mode in ("auto", "syslog"):
        events = read_syslog_events()
    if not events and args.mode in ("auto", "synthetic"):
        events = [generate_synthetic_event()]

    written = write_events(events)
    log_activity("adapter_stop", written)
    return 0


if __name__ == "__main__":
    sys.exit(main())
