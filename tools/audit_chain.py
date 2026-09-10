import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.time_utils import utc_now

from tools.time_utils import utc_now

ACTIVITY_LOG_ROOT_TYPE = "list"

def _write_atomic_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent), delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        temp_path = Path(handle.name)
    os.replace(temp_path, path)

def load_activity_log(path: Path) -> list:
    global ACTIVITY_LOG_ROOT_TYPE
    if not path.exists():
        ACTIVITY_LOG_ROOT_TYPE = "list"
        return []

    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    if isinstance(raw, list):
        ACTIVITY_LOG_ROOT_TYPE = "list"
        return raw
    if isinstance(raw, dict) and isinstance(raw.get("activities"), list):
        ACTIVITY_LOG_ROOT_TYPE = "dict"
        return raw["activities"]
    raise ValueError(f"Malformed activity log at {path}: expected a list or an object with an 'activities' list.")

def compute_entry_hash(entry: dict, prev_hash: str) -> str:
    data = {key: value for key, value in entry.items() if key not in {"prev_hash", "current_hash"}}
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest_input = canonical + str(prev_hash)
    return hashlib.sha256(digest_input.encode("utf-8")).hexdigest()

def append_activity(entry_data: dict, path: Path) -> dict:
    entries = load_activity_log(path)
    prev_hash = "GENESIS"
    if entries:
        prev_hash = str(entries[-1].get("current_hash") or "GENESIS")

    new_entry = dict(entry_data)
    new_entry.setdefault("timestamp", utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"))
    new_entry.setdefault("activity_type", "command_center_action")
    new_entry.setdefault("status", "success")
    new_entry.setdefault("details", "n/a")
    new_entry["prev_hash"] = prev_hash
    new_entry["current_hash"] = compute_entry_hash(new_entry, prev_hash)
    entries.append(new_entry)

    payload = entries if ACTIVITY_LOG_ROOT_TYPE == "list" else {"activities": entries}
    _write_atomic_json(path, payload)
    return new_entry

def verify_activity_chain(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, f"File missing: {path}"

    entries = load_activity_log(path)
    if not entries:
        return True, "Chain valid"

    previous_hash = "GENESIS"
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            return False, f"Entry at index {index} is not an object"

        stored_prev = str(entry.get("prev_hash", "GENESIS"))
        if index > 0 and stored_prev != previous_hash:
            return False, f"Hash mismatch at index {index}"

        computed_hash = compute_entry_hash(entry, stored_prev)
        stored_current = str(entry.get("current_hash", ""))
        if computed_hash != stored_current:
            return False, f"Hash mismatch at index {index}"
        previous_hash = stored_current

    return True, "Chain valid"

def migrate_activity_log(path: Path) -> int:
    if not path.exists():
        return 0

    entries = load_activity_log(path)
    if not entries:
        return 0

    previous_hash = "GENESIS"
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError(f"Entry in {path} is not an object and cannot be migrated.")
        data = {key: value for key, value in entry.items() if key not in {"prev_hash", "current_hash"}}
        entry["prev_hash"] = previous_hash
        entry["current_hash"] = compute_entry_hash(data, previous_hash)
        previous_hash = entry["current_hash"]

    payload = entries if ACTIVITY_LOG_ROOT_TYPE == "list" else {"activities": entries}
    _write_atomic_json(path, payload)
    return len(entries)