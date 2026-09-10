#!/usr/bin/env python3
"""
EnterpriseGuard ADIE - Dimensional History Recorder

Appends the current dimensional state to a JSONL history file.
Uses centralized paths from tools.paths_config.
Reads only from dimensional_state.json, never modifies it.

Governed by DC-072 (pending).
"""

from __future__ import annotations

import sys

# Mandatory: prevent bytecode generation
sys.dont_write_bytecode = True

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.paths_config import (
    DIMENSIONAL_HISTORY_PATH,
    DIMENSIONAL_STATE_PATH,
    ACTIVITY_LOG_PATH,
)
from tools.time_utils import utc_now

# Try to import logical clock; fallback gracefully
try:
    from tools.logical_clock import get_logical_time
except ImportError:
    def get_logical_time() -> str:
        """Fallback when logical_clock is not available."""
        return utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def _append_line_to_file(line: str, path: Path) -> None:
    """Append a single line to a JSONL file with 0600 permissions."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # Ensure file exists with correct permissions
    if not path.exists():
        path.touch(mode=0o600)
        os.chmod(path, 0o600)

    fd = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(line + "\n")
    os.chmod(path, 0o600)


def record_current_state() -> dict:
    """
    Read current dimensional_state.json and append a history record.

    Returns the record that was appended.
    """
    if not DIMENSIONAL_STATE_PATH.exists():
        raise FileNotFoundError("dimensional_state.json not found")

    # Read current state (read-only)
    with open(DIMENSIONAL_STATE_PATH, "r", encoding="utf-8") as f:
        state = json.load(f)

    dimensions = state.get("dimensions")
    if not isinstance(dimensions, dict) or not dimensions:
        raise ValueError("dimensional_state.json missing valid dimensions")

    record = {
        "timestamp": utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "logical_time": get_logical_time(),
        "updated_at": state.get("updated_at"),
        "dimensions": dimensions,
    }

    line = json.dumps(record, sort_keys=True)
    _append_line_to_file(line, DIMENSIONAL_HISTORY_PATH)

    # Log to activity log (correct path)
    try:
        from tools.audit_chain import append_activity

        append_activity(
            {
                "timestamp": utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "activity_type": "dimensional_history",
                "status": "success",
                "details": "dimensional_state_recorded",
            },
            ACTIVITY_LOG_PATH,
        )
    except Exception as exc:
        print(f"WARNING: failed to log history event: {exc}", file=sys.stderr)

    return record


def get_history(limit: int | None = None) -> list[dict]:
    """Return up to `limit` most recent history records."""
    if not DIMENSIONAL_HISTORY_PATH.exists():
        return []
    records = []
    with open(DIMENSIONAL_HISTORY_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    if limit is not None:
        records = records[-limit:]
    return records


def main() -> int:
    try:
        record = record_current_state()
        print(json.dumps(record, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
