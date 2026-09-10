# Component: realtime_monitor.py

**Path:** `tools/realtime_monitor.py`
**Purpose:** Inotify-based real-time file monitoring to mitigate TOCTOU.
**Status:** Working (used in TOCTOU tests)

---

## What It Does

Uses Linux inotify to detect file modifications, attribute changes,
deletions, and movements in real time.
Events are logged to tools/realtime_events.jsonl.
Innocence chain includes realtime_events_hash in ring computation.

## Inputs

- Directory paths to monitor
- inotify events (kernel)

## Outputs

- tools/realtime_events.jsonl (append-only)
- Each entry: timestamp, event_type, path, details

## Key Functions

| Function | Purpose |
|----------|---------|
| start_monitor() | Begin monitoring a path |
| process_event() | Handle inotify event |
| log_event() | Append to realtime_events.jsonl |

## Security

- Mitigates TOCTOU (time-of-check to time-of-use) attacks
- Detects:
  - IN_MODIFY: file content changed
  - IN_ATTRIB: metadata changed
  - IN_DELETE: file deleted
  - IN_MOVED_FROM/TO: file moved
  - IN_CREATE: new file created
- Events captured before operation completes

## TOCTOU Test Result

From tests/ADVANCED_SECURITY_TESTS.md:
- Test: modify file between check and use
- Result: PASS (detected via realtime log, ring includes hash)
- Note: Requires background monitor running

## Integration with Innocence Chain

Each ring includes:
- realtime_events_hash = SHA-256 of last line in realtime_events.jsonl
- If no events: hash = "none"
- This anchors the chain to the current monitoring state

## Dynamic File Note

realtime_events.jsonl is a dynamic file.
Excluded from integrity baseline.

## Tests

- Tested indirectly via advanced security tests
- Used in TOCTOU mitigation tests

## Used By

- innocence_chain.py (via get_last_realtime_event_hash)
- Advanced security test suite

**End of Component Doc**
