# Component: genesis_seed.py

**Path:** `tools/genesis_seed.py`
**Purpose:** Proves the system did not originate from nothing.
**Status:** Working (7/7 tests passed)

---

## What It Does

Generates genesis_hash = sha256(external_seed + identity_key).
Binds system origin to the physical hardware on which it was born.
Time-independent (verifiable by any third party).

## Inputs

- external_seed (priority: genesis_seed.txt > git HEAD > --seed CLI)
- identity_key (from hardware_identity.json)

## Outputs

- tools/genesis_baseline.json (chmod 0444)

## Key Functions

| Function | Purpose |
|----------|---------|
| utc_now_iso() | Return UTC ISO 8601 timestamp |
| get_seed_from_file() | Read genesis_seed.txt |
| get_seed_from_git() | Read git rev-parse HEAD |
| read_identity_key() | Load identity from hardware_identity.json |
| generate_genesis_hash() | Compute SHA-256 |
| write_genesis_baseline() | Save JSON with 0444 |
| log_genesis_event() | Log to DECISIONS_LOG.md |
| main() | CLI |

## Security

- File permissions: 0444 (read-only)
- Cannot be overwritten without --force
- Time-independent hash (clock not used)
- Requires hardware_identity.json to exist

## Tests

- tests/test_genesis_seed.py (7 tests, passing)

## Used By

- distributed_proof.py
- innocence_chain.py

**End of Component Doc**
