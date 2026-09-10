# Component: hardware_identity.py

**Path:** `tools/hardware_identity.py`
**Purpose:** Binds system identity to physical hardware fingerprints.
**Status:** Working (6/6 tests passed)

---

## What It Does

Generates a deterministic `identity_key` (SHA-256) from hardware fingerprints.
The key changes if any hardware component changes - preventing system cloning.

## Inputs

- Hardware attributes (UUID, CPU, machine ID, machine-id file)

## Outputs

- `tools/hardware_identity.json` (chmod 0600)
  - Contains: `identity_key`, `generated_at`, `sources`

## Key Functions

| Function | Purpose |
|----------|---------|
| `utc_now_iso()` | Return UTC ISO 8601 timestamp |
| `get_machine_id()` | Read /etc/machine-id |
| `generate_identity_key()` | Compute SHA-256 from hardware attributes |
| `write_identity_file()` | Save to JSON with 0600 permissions |
| `log_identity_event()` | Log to DECISIONS_LOG.md |
| `main()` | CLI: `--generate`, `--regenerate --confirm` |

## Security

- File permissions: 0600 (owner-only)
- Key derivation: SHA-256 over multiple hardware sources
- Regeneration requires explicit `--confirm` flag
- Regeneration is logged in `DECISIONS_LOG.md`

## Tests

- `tests/test_hardware_identity.py` (6 tests)
- All passing as of 2026-09-10

## Dependencies

- `hashlib`, `json`, `platform`, `uuid`, `pathlib`

## Used By

- `genesis_seed.py` (identity binding)
- `innocence_chain.py` (chain identity)
- `distributed_proof.py` (proof source)

**End of Component Doc**
