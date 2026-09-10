#!/usr/bin/env python3
"""
Dimensional Collector - Collects all 7 dimensions from existing components.
Spatial, Identity, Temporal, Relational, Behavioral, Negentropic, Syntropic.
Dynamic dimensions based on live metrics for temporal, relational, behavioral, syntropic.
Uses centralized paths from tools.paths_config.
Reads only; does not modify original components.
"""

import json
import math
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.paths_config import (
    ACTIVITY_LOG_PATH,
    RELATIONAL_MEMORY_PATH,
    INNOCENCE_CHAIN_PATH,
    HARDWARE_IDENTITY_PATH,
    DIMENSIONAL_STATE_PATH,
)
from tools.time_utils import utc_now

INTEGRITY_MONITOR_SCRIPT = ROOT / "tools" / "integrity_monitor.py"


def _load_json(path: Path):
    """Safely load JSON file, return None on any error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _parse_iso_timestamps(items):
    """Return sorted list of datetime objects from items with 'timestamp' field."""
    timestamps = []
    for item in items:
        ts = item.get("timestamp")
        if ts:
            try:
                ts_clean = ts.replace("Z", "+00:00")
                dt = datetime.fromisoformat(ts_clean)
                timestamps.append(dt)
            except ValueError:
                continue
    timestamps.sort()
    return timestamps


def _count_recent_events(data: list, minutes: int = 10) -> int:
    """Count events with timestamp within the last `minutes` minutes."""
    if not data:
        return 0
    now = utc_now()
    cutoff = now - timedelta(minutes=minutes)
    count = 0
    for item in data:
        ts = item.get("timestamp")
        if ts:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if dt >= cutoff:
                    count += 1
            except ValueError:
                continue
    return count


# ---------------- Dimension collectors ----------------

def collect_spatial():
    """Run integrity_monitor --check and return (score, details).
    Score is 1.0 only if the check passes, 0.0 otherwise.
    """
    cmd = [sys.executable, "-B", str(INTEGRITY_MONITOR_SCRIPT), "--check"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
        output = (result.stdout or "").strip()
        if not output:
            return 0.0, {"source": "integrity_monitor --check", "operational": False, "reason": "empty_output"}

        # Try strict JSON parsing first
        try:
            data = json.loads(output)
            if isinstance(data, dict) and data.get("status") in ("PASS", "FAIL"):
                score = 1.0 if data["status"] == "PASS" else 0.0
                return score, {"source": "integrity_monitor --check", "operational": False,
                               "reason": f"status_{data['status'].lower()}"}
        except json.JSONDecodeError:
            pass

        # Fallback to textual check, avoiding the "FAIL" inside "FAILURE" trap.
        upper = output.upper()
        if "FAILURE: 0" in upper:
            return 1.0, {"source": "integrity_monitor --check", "operational": False, "reason": "ok"}
        elif "FAILURE:" in upper and "FAILURE: 0" not in upper:
            return 0.0, {"source": "integrity_monitor --check", "operational": False, "reason": "check_failed"}
        else:
            # Unknown output format: treat as failure to be safe
            return 0.0, {"source": "integrity_monitor --check", "operational": False, "reason": "unrecognized_output"}

    except (subprocess.TimeoutExpired, Exception):
        return 0.0, {"source": "integrity_monitor --check", "operational": False, "reason": "exception"}


def collect_identity():
    """Check hardware_identity.json for identity_key."""
    if not HARDWARE_IDENTITY_PATH.exists():
        return 0.0, {"source": "hardware_identity.json", "operational": False, "reason": "file_missing"}
    data = _load_json(HARDWARE_IDENTITY_PATH)
    if data is None:
        return 0.0, {"source": "hardware_identity.json", "operational": False, "reason": "invalid_json"}
    if "identity_key" in data and data["identity_key"]:
        return 1.0, {"source": "hardware_identity.json", "operational": False, "reason": "ok"}
    return 0.0, {"source": "hardware_identity.json", "operational": False, "reason": "missing_key"}


def collect_temporal():
    """
    Temporal dimension: time since last event in activity_log.
    Score decreases as time since last event increases.
    Threshold: 6 hours (21600 seconds) maps to 0.0, fresh event maps to 1.0.
    """
    if not ACTIVITY_LOG_PATH.exists():
        return 0.5, {"source": "activity_log.json", "operational": True, "reason": "file_missing"}
    data = _load_json(ACTIVITY_LOG_PATH)
    if not isinstance(data, list) or len(data) == 0:
        return 0.0, {"source": "activity_log.json", "operational": True, "reason": "no_events"}

    timestamps = _parse_iso_timestamps(data)
    if not timestamps:
        return 0.0, {"source": "activity_log.json", "operational": True, "reason": "no_timestamps"}

    last_ts = timestamps[-1]
    now = utc_now()
    delta_seconds = (now - last_ts).total_seconds()
    score = max(0.0, 1.0 - (delta_seconds / 21600.0))
    return score, {"source": "activity_log.json", "operational": False, "reason": f"last_event_{delta_seconds:.0f}s_ago"}


def collect_relational():
    """
    Relational dimension: ratio of live nodes to 100 (soft max).
    Score = min(1.0, count / 100.0)
    """
    if not RELATIONAL_MEMORY_PATH.exists():
        return 0.0, {"source": "relational_memory.json", "operational": True, "reason": "file_missing"}
    data = _load_json(RELATIONAL_MEMORY_PATH)
    if data is None:
        return 0.0, {"source": "relational_memory.json", "operational": True, "reason": "invalid_json"}
    nodes = data.get("nodes", []) if isinstance(data, dict) else data
    if not isinstance(nodes, list):
        nodes = []
    count = len(nodes)
    score = min(1.0, count / 100.0)
    return score, {"source": "relational_memory.json", "operational": False, "reason": f"{count}_nodes"}


def collect_behavioral():
    """
    Behavioral dimension: number of events in last 10 minutes.
    Score = min(1.0, recent_count / 20.0)
    """
    if not ACTIVITY_LOG_PATH.exists():
        return 0.0, {"source": "activity_log.json", "operational": True, "reason": "file_missing"}
    data = _load_json(ACTIVITY_LOG_PATH)
    if not isinstance(data, list):
        return 0.0, {"source": "activity_log.json", "operational": True, "reason": "invalid_json"}

    recent = _count_recent_events(data, minutes=10)
    score = min(1.0, recent / 20.0)
    return score, {"source": "activity_log.json", "operational": False, "reason": f"{recent}_recent_events"}


def collect_negentropic():
    """
    Negentropic dimension: verify innocence_chain.json via verify_chain.
    Returns 1.0 if chain is valid, 0.0 otherwise.
    """
    if not INNOCENCE_CHAIN_PATH.exists():
        return 0.0, {"source": "innocence_chain.json", "operational": False, "reason": "file_missing"}

    try:
        # Import verify_chain to perform full verification
        from tools.innocence_chain import verify_chain
        if verify_chain():
            return 1.0, {"source": "innocence_chain.json", "operational": False, "reason": "ok"}
        else:
            return 0.0, {"source": "innocence_chain.json", "operational": False, "reason": "chain_tampered"}
    except Exception:
        return 0.0, {"source": "innocence_chain.json", "operational": False, "reason": "verification_error"}


def collect_syntropic():
    """
    Syntropic dimension: coefficient of variation (CV) of inter-event intervals
    among recent events (last 30 minutes).
    Thresholds: CV < 1.5 -> 1.0, 1.5-2.5 -> 0.5, >2.5 -> 0.0.
    """
    if not ACTIVITY_LOG_PATH.exists():
        return 0.0, {"source": "activity_log.json", "operational": True, "reason": "file_missing"}
    data = _load_json(ACTIVITY_LOG_PATH)
    if not isinstance(data, list):
        return 0.0, {"source": "activity_log.json", "operational": True, "reason": "invalid_json"}

    timestamps = _parse_iso_timestamps(data)
    if len(timestamps) < 3:
        return 0.5, {"source": "activity_log.json", "operational": True, "reason": "insufficient_timestamps"}

    now = utc_now()
    cutoff = now - timedelta(minutes=30)
    recent_timestamps = [ts for ts in timestamps if ts >= cutoff]
    if len(recent_timestamps) < 3:
        return 0.5, {"source": "activity_log.json", "operational": True, "reason": "insufficient_recent"}

    diffs = []
    for i in range(1, len(recent_timestamps)):
        diff = (recent_timestamps[i] - recent_timestamps[i-1]).total_seconds()
        if diff > 0:
            diffs.append(diff)

    if len(diffs) < 2:
        return 0.5, {"source": "activity_log.json", "operational": True, "reason": "insufficient_diffs"}

    mean = sum(diffs) / len(diffs)
    if mean <= 0:
        return 0.5, {"source": "activity_log.json", "operational": True, "reason": "zero_mean"}

    variance = sum((d - mean) ** 2 for d in diffs) / len(diffs)
    std = math.sqrt(variance)
    cv = std / mean

    if cv < 1.5:
        return 1.0, {"source": "activity_log.json", "operational": False, "reason": "regular"}
    elif cv < 2.5:
        return 0.5, {"source": "activity_log.json", "operational": False, "reason": "moderate_variation"}
    else:
        return 0.0, {"source": "activity_log.json", "operational": False, "reason": "high_variation"}


def main():
    sys.path.insert(0, str(ROOT))
    from tools.dimensional_state import DimensionalState

    state = DimensionalState()
    print("Collecting all 7 dimensions...")

    score, details = collect_spatial()
    print(f"Spatial score: {score}")
    state.report("spatial", score, details)

    score, details = collect_identity()
    print(f"Identity score: {score}")
    state.report("identity", score, details)

    score, details = collect_temporal()
    print(f"Temporal score: {score}")
    state.report("temporal", score, details)

    score, details = collect_relational()
    print(f"Relational score: {score}")
    state.report("relational", score, details)

    score, details = collect_behavioral()
    print(f"Behavioral score: {score}")
    state.report("behavioral", score, details)

    score, details = collect_negentropic()
    print(f"Negentropic score: {score}")
    state.report("negentropic", score, details)

    score, details = collect_syntropic()
    print(f"Syntropic score: {score}")
    state.report("syntropic", score, details)

    print("All dimensions collected.")
    print(json.dumps(state.current_tick_data, indent=2))


if __name__ == "__main__":
    main()
