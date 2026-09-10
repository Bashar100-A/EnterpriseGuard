# Component: audit_chain.py

**Path:** `tools/audit_chain.py`
**Purpose:** Tamper-evident hash chain protecting activity_log.json.
**Status:** Working (used in all components)

---

## What It Does

Provides append-only activity logging with hash chaining.
Each entry links to the previous entry's hash.
Any modification to an old entry breaks all subsequent hashes.

## Inputs

- event_type (string)
- details (dict)
- activity_log path (default: tools/activity_log.json)

## Outputs

- tools/activity_log.json (append-only, dynamic)
- Each entry contains: timestamp, event_type, details, prev_hash, entry_hash

## Key Functions

| Function | Purpose |
|----------|---------|
| append_activity() | Add a new entry to the log |
| load_activity_log() | Load all entries |
| verify_chain() | Verify hash chain integrity |

## Chain Structure

Each entry:
    {
      "timestamp": "2026-09-10T20:00:00Z",
      "event_type": "storage.write",
      "details": {...},
      "prev_hash": "<sha256 of previous entry>",
      "entry_hash": "<sha256 of this entry>"
    }

## Security

- Hash algorithm: SHA-256
- Chain cannot be modified without detection
- File excluded from integrity baseline (dynamic)
- Audit chain verified during checklist and integrity_monitor runs

## Dynamic File Note

activity_log.json is explicitly excluded from:
- integrity_baseline.json
- TRUSTED_BASELINE.json

Reason: it changes on every operation, would cause false drift.

## Failure Handling

| Scenario | Behavior |
|----------|----------|
| Missing log file | Start with empty chain |
| Corrupted JSON | Raise error |
| Hash chain mismatch | Raise error on verify_chain() |
| append_activity unavailable | Fallback to local logger.warning |

## Tests

- Tested indirectly through all components' tests
- No dedicated test file currently

## Used By

- All tools that log events
- checklist.py (periodic chain verification)
- integrity_monitor.py (chain check on --check)

**End of Component Doc**
