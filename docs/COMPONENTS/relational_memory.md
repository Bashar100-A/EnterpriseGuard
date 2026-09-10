# Component: relational_memory.py

**Path:** `tools/relational_memory.py`
**Purpose:** Stores causal links between events (forgetting without denial).
**Status:** Working (5/5 tests passed)

---

## What It Does

Stores associative nodes linking events:
each node has event_id, prev_event, next_event, cause, effect, timestamp.
When archived, relational links remain intact.

## Inputs

- Event ID (string)
- prev_event, next_event (strings or null)
- cause, effect (strings)
- timestamp (UTC ISO 8601)

## Outputs

- tools/relational_memory.json (chmod 0600)
- tools/relational_memory_archive.json.gz (rotation)

## Rotation Policy

- Max 1000 nodes in active memory
- Oldest 500 compressed to archive when limit reached
- Archive is never deleted

## Security

- File permissions: 0600
- Duplicate event_id rejected
- Empty fields rejected

## Tests

- tests/test_relational_memory.py (5 tests, passing)

**End of Component Doc**
