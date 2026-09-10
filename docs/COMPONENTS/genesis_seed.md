# Component: genesis_seed.py

**Path:** `tools/genesis_seed.py`
**Purpose:** Proves the system did not originate from nothing.
**Status:** Working (7/7 tests passed)

---

## What It Does

Generates `genesis_hash` from an external seed + hardware identity + UTC time.
Binds system origin to the physical hardware on which it was born.

## Inputs

- `external_seed` (from `genesis_seed.txt`, Git HEAD, or CLI)
- `identity_key` (from `hardware_identity.json`)
- UTC timestamp

## Outputs

- `tools/genesis_baseline.json` (chmod 0444)

## Key Functions

| Function | Purpose |
|----------|---------|
| `generate_genesis_hash()` | Compute genesis SHA-256 |
| `read_identity_key()` | Load identity from hardware_identity.json |
| `write_genesis_baseline()` | Save to JSON (0444) |
| `main()` | CLI: `--generate`, `--force` |

## Security

- File permissions: 0444 (read-only)
- Cannot be overwritten without `--force`
- Time-independent (hash does not include system clock; UTC only for metadata)

## Tests

- `tests/test_genesis_seed.py` (7 tests, passing)

## Used By

- `distributed_proof.py`
- `innocence_chain.py` (genesis reference)

**End of Component Doc**
