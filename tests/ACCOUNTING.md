# ADIE Test Accounting

**Authority:** `tests/account.py`
**Rule:** Every external claim about test counts MUST cite this file
or the output of `tests/account.py`. No numbers from memory.

## How to reproduce

    cd ~/Desktop/EnterpriseGuard
    .venv/bin/python tests/account.py

## Current numbers (2026-10-07)

Four non-overlapping buckets:

| Bucket | Count | Definition |
|---|---|---|
| REGRESSION_TOTAL | 633 | Phase 1 suites (adversarial, vomega, meta, registry, acl, authoring, pilot, rust) |
| PHASE2_ADIE_PYTHON | 59 | Phase 2 hybrid suites in Python |
| PHASE2_ADIE_JAVASCRIPT | 11 | Phase 2 hybrid suites in JavaScript |
| ACVP_UNIQUE_VECTORS | 55 | NIST ACVP ML-DSA-65 (25 keygen + 15 siggen + 15 sigver) |
| ACVP_VECTOR_EXECUTIONS | 150 | Same 55 vectors x 3 languages |

**Grand total (unique, non-overlapping):** 633 + 59 + 11 + 55 = 758

## Approved claim forms

    633/633 regression tests passed.
    59/59 ADIE Phase-2 Python suites passed.
    11/11 ADIE Phase-2 JavaScript suites passed.
    150/150 NIST ACVP vector executions passed (55 unique x 3 languages).

## Forbidden claim forms

    "723/723 tests passed"             -- unverified, historical error
    "75 Phase-2 tests passed"          -- conflates Python + JS
    "NIST Certified"                   -- not applicable (no CAVP validation)
    "Zero errors"                      -- 14 DEFECTs logged; say "no open defects"
    "Production-grade PQC framework"   -- preconditions not met

## When to update

After any new suite is added:
1. Run `tests/account.py`
2. Copy the numbers verbatim into this file
3. Do NOT compute totals by hand

## History

| Date | Event | Numbers |
|---|---|---|
| 2026-10-06 | Phase 1 closed | (claimed 648; actual 633) |
| 2026-10-07 | Phase 2 closed | (claimed 723/75; actual 70 + ACVP-55) |
| 2026-10-07 | DEFECT-014 logged | tool created, numbers authoritative |
