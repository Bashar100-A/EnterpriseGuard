#!/usr/bin/env python3
"""Logical clock based on the activity log hash chain and a local monotonic counter.

This module is intentionally independent from the OS clock. It supplements UTC
timestamps for ordering analysis and emits warnings when the logical ordering and
UTC diverge, but it does not replace the UTC record.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

sys.dont_write_bytecode = True


def load_chain_state(activity_log_path: Path) -> dict:
    """Load the current hash-chain state from the activity log."""
    if not activity_log_path.exists():
        return {"chain_hash": "", "last_timestamp_utc": None, "entry_count": 0, "status": "MISSING_OR_MALFORMED"}
    try:
        data = activity_log_path.read_bytes()
        payload = json.loads(data.decode("utf-8"))
    except Exception:
        return {"chain_hash": "", "last_timestamp_utc": None, "entry_count": 0, "status": "MISSING_OR_MALFORMED"}

    entry_count = 0
    last_entry = None
    if isinstance(payload, dict):
        entries = payload.get("activities")
        if isinstance(entries, list):
            entry_count = len(entries)
            if entries:
                last_entry = entries[-1]
    elif isinstance(payload, list):
        entry_count = len(payload)
        if payload:
            last_entry = payload[-1]

    if last_entry and isinstance(last_entry, dict):
        chain_hash = last_entry.get("current_hash") or hashlib.sha256(data).hexdigest()
        last_timestamp_utc = last_entry.get("timestamp")
    else:
        chain_hash = hashlib.sha256(data).hexdigest() if data else ""
        last_timestamp_utc = None

    return {
        "chain_hash": chain_hash,
        "last_timestamp_utc": last_timestamp_utc,
        "entry_count": entry_count,
        "status": "OK",
    }


class LogicalClock:
    """A monotonic logical clock driven by the activity log hash chain."""

    def __init__(self, activity_log_path: Path, counter_start: int = 0):
        self.path = Path(activity_log_path)
        self._counter = int(counter_start)
        self._initial_state = load_chain_state(self.path)

    def tick(self) -> dict:
        self._counter += 1
        state = load_chain_state(self.path)
        chain_hash = state.get("chain_hash") or self._initial_state.get("chain_hash") or ""
        logical_time = hashlib.sha256(f"{chain_hash}:{self._counter}".encode("utf-8")).hexdigest()
        return {"chain_hash": chain_hash, "counter": self._counter, "logical_time": logical_time}

    def compare(self, event_a: dict, event_b: dict) -> int:
        a_chain = event_a.get("chain_hash") or ""
        b_chain = event_b.get("chain_hash") or ""
        if a_chain != b_chain:
            a_entry_count = int(event_a.get("entry_count") or 0)
            b_entry_count = int(event_b.get("entry_count") or 0)
            return -1 if a_entry_count < b_entry_count else 1 if a_entry_count > b_entry_count else 0
        a_counter = int(event_a.get("counter") or 0)
        b_counter = int(event_b.get("counter") or 0)
        if a_counter < b_counter:
            return -1
        if a_counter > b_counter:
            return 1
        return 0

    def verify_utc_consistency(self, tolerance_seconds: int = 60) -> dict:
        state = load_chain_state(self.path)
        last_ts = state.get("last_timestamp_utc")
        if not last_ts:
            return {"status": "WARNING", "message": "Logical clock/UTC drift exceeds tolerance"}
        try:
            parsed = datetime.strptime(last_ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            return {"status": "WARNING", "message": "Logical clock/UTC drift exceeds tolerance"}
        now = datetime.now(timezone.utc)
        if abs((now - parsed).total_seconds()) > tolerance_seconds:
            return {"status": "WARNING", "message": "Logical clock/UTC drift exceeds tolerance"}
        return {"status": "PASS", "message": "Logical clock and UTC are consistent"}


def _main_check(activity_log_path: Path) -> dict:
    state = load_chain_state(activity_log_path)
    result = {
        "entry_count": state.get("entry_count", 0),
        "chain_hash": state.get("chain_hash", ""),
        "last_timestamp_utc": state.get("last_timestamp_utc"),
    }
    if not activity_log_path.exists():
        result["warning"] = "No activity log found; logical clock unavailable."
        return result
    clock = LogicalClock(activity_log_path)
    ticks = []
    for _ in range(3):
        ticks.append(clock.tick())
    result["ticks"] = ticks
    result["utc_consistency"] = clock.verify_utc_consistency()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Logical clock check")
    parser.add_argument("--check", action="store_true", help="Run the logical clock verification")
    args = parser.parse_args()

    activity_log_path = Path(__file__).resolve().parent / "activity_log.json"
    if args.check:
        summary = _main_check(activity_log_path)
        if not activity_log_path.exists():
            print(json.dumps({"status": "WARNING", "message": "No activity log found; logical clock unavailable."}, sort_keys=True))
            return 0
        print(json.dumps(summary, sort_keys=True, indent=2))
        return 0

    parser.print_usage(sys.stderr)
    print(f"{parser.prog}: error: --check is required", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
