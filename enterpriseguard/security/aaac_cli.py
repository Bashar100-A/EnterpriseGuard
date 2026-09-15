#!/usr/bin/env python3
"""AAAC CLI: unified pipeline to fetch traces, store events, and extend chain."""

import os
import sys
import json
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.native_connectors import unified_fetch
from tools.compliance_engine import enrich_event_with_compliance

RING_STORAGE_PATH = ROOT / "tools" / "ring_storage.jsonl"

def load_existing_trace_ids():
    """Return set of trace_ids already stored in ring_storage.jsonl."""
    ids = set()
    if RING_STORAGE_PATH.exists():
        try:
            with open(RING_STORAGE_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            event = json.loads(line)
                            tid = event.get("trace_id")
                            if tid:
                                ids.add(tid)
                        except json.JSONDecodeError:
                            continue
        except OSError:
            pass
    return ids



def append_event_to_ring_storage(event: dict) -> None:
    """Append one event as JSONL with fsync."""
    RING_STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RING_STORAGE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def main() -> int:
    source = os.environ.get("AAAC_TRACE_SOURCE", "auto")
    limit = int(os.environ.get("AAAC_FETCH_LIMIT", "10"))
    print(f"Fetching traces from source={source} limit={limit}...")
    try:
        events = unified_fetch(source=source, limit=limit)
    except Exception as e:
        print(f"Fetch failed: {e}", file=sys.stderr)
        return 1

    if not events:
        print("No new events fetched.")
        return 0

    existing_ids = load_existing_trace_ids()
    new_events = []
    for event in events:
        tid = event.get("trace_id")
        if tid and tid in existing_ids:
            print(f"Skipping duplicate trace_id: {tid}")
            continue
        new_events.append(event)

    for event in new_events:
        enriched = enrich_event_with_compliance(event)
        append_event_to_ring_storage(enriched)

    print(f"Stored {len(new_events)} new events to {RING_STORAGE_PATH}")

    # Generate new ring
    from tools import innocence_chain
    try:
        ring = innocence_chain.generate_ring()
        print(f"Generated new ring: {ring.get('ring_hash', '')[:16]}...")
    except Exception as e:
        print(f"Ring generation failed: {e}", file=sys.stderr)
        return 2

    # Verify chain
    valid = innocence_chain.verify_chain()
    if valid:
        print("Chain verification: VERIFIED_OK")
        return 0
    else:
        print("Chain verification failed", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
