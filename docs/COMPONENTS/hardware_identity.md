# hardware_identity.py

**Purpose:** Generate a stable, hardware-derived identity key for the host
machine running EnterpriseGuard. Used as a trust anchor for the Sovereign
Reference Core.

**Location:** `tools/hardware_identity.py`
**Output:** `tools/hardware_identity.json` (chmod 0600)
**Related:** `tools/audit_chain.py`, `tools/time_utils.py`

## Inputs
- `/etc/machine-id` or `/var/lib/dbus/machine-id` (read-only)
- `uuid.getnode()` (MAC-derived, may vary in VMs)
- `platform.processor()`, `platform.machine()`, `os.cpu_count()`

## Outputs
JSON file with:
- `identity_key` -- SHA-256 of joined hardware fingerprints
- `generated_at` -- UTC ISO 8601
- `regenerated` -- boolean flag
- `schema_version` -- currently `"1.0"`

## CLI
- `--generate` -- create identity (fails if exists unless `--force`)
- `--regenerate --confirm REGEN` -- replace existing identity (requires explicit confirmation string)
- No args -- print usage

## Invariants
- **Never** reads or writes protected directories (`adie/`, `intelligence/`, or their `src/` equivalents).
- File is written **atomically** via `tempfile.mkstemp` + `os.replace`, with `0600` permissions.
- Regeneration requires an explicit `--confirm REGEN` string -- no silent overwrite.
- Every generation event is appended to `tools/activity_log.json` (audit trail).
- Fails **closed**: if `hardware_identity.json` exists, `--generate` exits with code 1.

## Why it matters
The identity key is bound to the physical host and cannot be forged by a
remote attacker. It underpins chain-of-trust operations in the Sovereign
Reference Core.
