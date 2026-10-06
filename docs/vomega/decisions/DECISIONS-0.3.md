# ADIE vOmega - Decision Record 0.3

**Date:** 2026-10-07
**Authority:** Project Lead
**Status:** Binding
**Extends:** DECISIONS-0.1, DECISIONS-0.2

## Preamble

Establishes discipline for numeric claims and prohibitions on
unsubstantiated statements. Applies to all documents, commits, and
external communications.

## Decision 1 - Three-bucket accounting

Test results MUST be reported in separate, non-overlapping buckets:

    REGRESSION_TOTAL              (Phase 1 regression suites)
    PHASE2_ADIE_PYTHON            (Phase 2 Python suites)
    PHASE2_ADIE_JAVASCRIPT        (Phase 2 JavaScript suites)
    ACVP_VECTOR_EXECUTIONS        (NIST ACVP executions across languages)
    ACVP_UNIQUE_VECTORS           (unique vectors, counted once)

The buckets MUST NOT be summed into a single "total" without stating
that the sum includes non-overlapping categories.

Authority for these numbers: tests/account.py

## Decision 2 - Forbidden phrases

Forbidden until stated precondition is met:

| Phrase | Precondition |
|---|---|
| "NIST Certified" | Formal CAVP validation path completed |
| "Zero errors" | Use "no open defects at closure" |
| "Production-grade PQC framework" | 3E+3A+3B+3C+fuzz+external review+key custody |
| "Standards-compliant" without qualification | Cite exact standard and profile |
| "Independently verified" | Name the independent party |

## Decision 3 - Approved claim forms

    "N/M regression tests passed"
    "N/M ADIE Phase-2 tests passed"
    "N/M NIST ACVP vector executions passed (55 unique x N languages)"
    "Two independent implementations agree byte-for-byte on vector set V"
    "GAP-N documented: precise description"
    "DEFECT-N closed: precise description"

## Decision 4 - DEFECT and GAP discipline

Every DEFECT must include:
- date, commit_found, commit_fixed
- category (code | test | spec | process)
- root_cause (mechanism, not symptom)
- fix (what changed)
- lesson (generalizable rule)

Every GAP must include:
- paths tried (with commands and exit codes)
- consequence (what is lost)
- resolution path (Phase N + approach)
- status (open | resolved | retracted)

## Decision 5 - RFC 9964 adoption for COSE/ML-DSA

ML-DSA in COSE uses the IANA-registered algorithm identifiers
(ML-DSA-65 = -49). ADIE does not invent COSE representations that
RFC 9964 already specifies. See Phase 3A.

## Decision 6 - CBOR philosophy

ADIE does NOT write generic CBOR implementations from scratch.
ADIE defines an ADIE Deterministic CBOR Profile layered over
RFC 8949, with strict validation, rejection rules, and a
differential test corpus. Reference implementation in Rust;
adapters in Python and JavaScript.

Rationale: RFC 8949 encodes deterministic rules, but parser
differential risk is real. Reinventing a general CBOR parser
in three languages creates three chances for the same class of bug.
See DECISIONS-0.2 philosophy.

## Decision 7 - Phase 3 gate order

    Gate 0: 3E  Rust Full Hybrid Verifier
    Gate 1: 3A.1 DCP 2.1 Wire Format Specification
    Gate 2: 3A.2-3A.7 Deterministic CBOR + COSE
    Gate 3: 3B  Governance Ceremony
    Gate 4: 3C  Revocation / Offline Status
    Gate 5: 3D  SLH-DSA Diversity

No gate may be skipped. Phase 4 may not begin until Gate 5 closes.

## Decision 8 - Commit message numbers

No number appears in a commit message unless it was copied verbatim
from the stdout of tests/account.py at commit time. This is a
consequence of DEFECT-014.

---



## Decision 9 - RSA library selection (Gate 0)

For Phase 3 Gate 0 (Rust full hybrid verifier), the RSA implementation
is `sad-rsa = "=0.10.2"`.

Rationale:
- mainline `rsa 0.9.6` has RUSTSEC-2023-0071 (Marvin) unpatched and
  partial RFC 8017 length validation.
- mainline `rsa 0.10.x` is still RC.
- `sad-rsa 0.10.2` mitigates Marvin, applies complete RFC 8017
  length validation, and enhances zeroization.

Constraints:
- `sad-rsa` is invoked ONLY from `rust/adie-primitives/src/rsa_verify.rs`.
- No direct calls from `verifier.rs` or anywhere else.
- Cargo.lock pins `=0.10.2`; checksum verified.
- RISK-3.1 and RISK-3.2 recorded in DEFECTS-LOG.md.

Reconsideration trigger:
- If mainline `rsa` ships 0.10.x stable with Marvin mitigation, swap
  to mainline in one commit (API is compatible with sad-rsa 0.10.x).
- If sad-rsa becomes unmaintained, revert to `rsa 0.9.6` + explicit
  offline-only usage boundary.

---

**End of DECISIONS-0.3 (with amendment)**
