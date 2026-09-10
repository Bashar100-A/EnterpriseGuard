#!/usr/bin/env python3
"""EnterpriseGuard Relational Memory.

Stores associative event nodes with causal links, providing
forgetting without denial. Events can be archived, but their
relational nodes remain until explicit rotation.

Design:
- Live memory: tools/relational_memory.json (chmod 600)  [production: DATA_DIR]
- Archive: tools/relational_memory_archive.json.gz (created on rotation)
- Max nodes: 1000
- Rotation: when max exceeded, oldest 500 are moved to archive
"""

from __future__ import annotations

import sys

# Must be set before any other imports.
sys.dont_write_bytecode = True

import argparse
import gzip
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.paths_config import RELATIONAL_MEMORY_PATH, ACTIVITY_LOG_PATH

# Live and archive paths (archive is derived from live path parent)
LIVE_PATH = RELATIONAL_MEMORY_PATH
ARCHIVE_PATH = LIVE_PATH.parent / "relational_memory_archive.json.gz"
MAX_NODES = 1000
ARCHIVE_COUNT = 500


def utc_now_iso() -> str:
    """Return current UTC timestamp using the project's canonical time util."""
    sys.path.insert(0, str(ROOT))
    from tools.time_utils import utc_now

    return utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def load_live_memory() -> list[dict]:
    """Load the live relational nodes from disk."""
    if not LIVE_PATH.exists():
        return []
    try:
        data = json.loads(LIVE_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data.get("nodes", [])
        if isinstance(data, list):
            return data
    except Exception:
        return []
    return []


def save_live_memory(nodes: list[dict]) -> None:
    """Atomically write the live memory with chmod 600."""
    payload = {
        "schema_version": "1.0",
        "nodes": nodes,
        "last_updated": utc_now_iso(),
    }
    LIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        prefix=".relational_memory.",
        suffix=".tmp",
        dir=str(LIVE_PATH.parent),
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
            f.write("\n")
        os.chmod(tmp, 0o600)
        os.replace(tmp, LIVE_PATH)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def archive_old_nodes(nodes: list[dict]) -> list[dict]:
    """Move oldest ARCHIVE_COUNT nodes to gzip archive."""
    if len(nodes) <= MAX_NODES:
        return nodes

    to_archive = nodes[:ARCHIVE_COUNT]
    remaining = nodes[ARCHIVE_COUNT:]

    existing = []
    if ARCHIVE_PATH.exists():
        try:
            with gzip.open(ARCHIVE_PATH, "rt", encoding="utf-8") as f:
                data = json.load(f)
                existing = data.get("nodes", [])
        except Exception:
            existing = []

    combined = existing + to_archive
    payload = {
        "schema_version": "1.0",
        "nodes": combined,
        "last_archived": utc_now_iso(),
    }

    ARCHIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        prefix=".relational_memory_archive.",
        suffix=".tmp.gz",
        dir=str(ARCHIVE_PATH.parent),
    )
    try:
        with os.fdopen(fd, "wb") as f:
            with gzip.GzipFile(fileobj=f, mode="wb") as gz:
                gz.write(json.dumps(payload, indent=2, sort_keys=True).encode("utf-8"))
        os.chmod(tmp, 0o600)
        os.replace(tmp, ARCHIVE_PATH)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise

    return remaining


def record_event(
    event_id: str,
    prev_event: str,
    next_event: str,
    cause: str,
    effect: str,
) -> dict:
    """Append a new relational node and return it.

    Raises ValueError if any field is empty or event_id already exists.
    """
    fields = {
        "event_id": event_id,
        "prev_event": prev_event,
        "next_event": next_event,
        "cause": cause,
        "effect": effect,
    }
    for key, value in fields.items():
        if not value or not value.strip():
            raise ValueError(f"{key} must not be empty")
        fields[key] = value.strip()

    if event_exists(fields["event_id"]):
        raise ValueError(f"event_id already exists: {fields['event_id']}")

    nodes = load_live_memory()
    node = {
        "event_id": fields["event_id"],
        "prev_event": fields["prev_event"],
        "next_event": fields["next_event"],
        "cause": fields["cause"],
        "effect": fields["effect"],
        "timestamp": utc_now_iso(),
    }
    nodes.append(node)

    if len(nodes) > MAX_NODES:
        nodes = archive_old_nodes(nodes)

    save_live_memory(nodes)
    _log_event(node["event_id"])
    return node


def _log_event(event_id: str) -> None:
    """Append relational event to activity log, warning on failure."""
    try:
        from tools.audit_chain import append_activity
        from tools.time_utils import utc_now

        append_activity(
            {
                "timestamp": utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "activity_type": "relational_memory",
                "status": "success",
                "details": f"relational_event_recorded: {event_id}",
            },
            ACTIVITY_LOG_PATH,
        )
    except Exception as exc:
        print(f"WARNING: failed to log relational event: {exc}", file=sys.stderr)


def event_exists(event_id: str) -> bool:
    """Check if an event with the given ID already exists."""
    nodes = load_live_memory()
    return any(node.get("event_id") == event_id for node in nodes)


def main() -> int:
    parser = argparse.ArgumentParser(description="EnterpriseGuard Relational Memory")
    parser.add_argument(
        "--record",
        nargs=5,
        metavar=("EVENT_ID", "PREV", "NEXT", "CAUSE", "EFFECT"),
        help="Record a relational event",
    )
    parser.add_argument(
        "--count",
        action="store_true",
        help="Print number of live nodes",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List up to 10 most recent live nodes (IDs only)",
    )
    args = parser.parse_args()

    if args.record:
        try:
            node = record_event(*args.record)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(node, indent=2, sort_keys=True))
        return 0

    if args.count:
        nodes = load_live_memory()
        print(len(nodes))
        return 0

    if args.list:
        nodes = load_live_memory()
        for node in nodes[-10:]:
            print(node.get("event_id"))
        return 0

    parser.print_usage(sys.stderr)
    print("error: one of --record, --count, or --list is required", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
