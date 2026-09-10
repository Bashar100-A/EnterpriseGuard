# Component: integrity_monitor.py

**Path:** `tools/integrity_monitor.py`
**Purpose:** Validate file baselines against SHA-256 sentinels.
**Status:** Working (used in all integrity checks)

---

## What It Does

Monitors file integrity by comparing current SHA-256 hashes
against stored baselines. Two baselines:
- tools/integrity_baseline.json (per-file hashes)
- tools/TRUSTED_BASELINE.json (protected critical files)

Each baseline has a sentinel that stores its own SHA-256.

## Inputs

- Project files in tools/
- Baseline JSON files
- Sentinel files

## Outputs

- Status output: PASS / FAIL
- Exit code: 0 (PASS) or 1 (FAIL)
- errors.log on failure

## Key Functions

| Function | Purpose |
|----------|---------|
| check_integrity() | Verify all files vs baseline |
| get_integrity_status() | Return PASS/FAIL |
| main() | CLI: --check |

## Baseline Structure

tools/integrity_baseline.json:
    {
      "file.py": "sha256hash...",
      ...
    }

Sentinel:
    {
      "baseline_sha256": "hash of baseline file itself"
    }

## Dynamic Files Excluded

These files change frequently and are NOT monitored:
- tools/activity_log.json
- tools/errors.log
- tests/TEST_RESULTS.md
- continuity/CURRENT_STATE.md

## Security

- Every baseline has a sentinel for tamper detection
- Detects: modification, deletion, unexpected files
- Fail-secure: on error, exits with status 1
- Used by innocence_chain to produce integrity_status

## Failure Handling

| Scenario | Behavior |
|----------|----------|
| Baseline missing | FAIL |
| Sentinel mismatch | FAIL (baseline tampered) |
| File hash mismatch | FAIL (file tampered) |
| File missing | FAIL |
| Unexpected file | FAIL |

## Tests

- Tested indirectly via integration tests
- Used by test_innocence_chain (integrity_status source)

## Used By

- innocence_chain.py (via run_integrity_check)
- checklist.py
- command_center.py
- audit_chain.py (indirectly)

**End of Component Doc**
