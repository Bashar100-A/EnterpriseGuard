# ADIE vOmega - Phase 3 Gate 0 Closure

**Date:** 2026-10-07
**Gate:** 3E - Rust Full Hybrid Verifier
**Status:** CLOSED

## 1. Scope

Close the gap between Python/JS (which verify full DCP 2.1 hybrid
certificates) and Rust (which previously verified only keygen +
sigver for ML-DSA, and nothing for RSA).

## 2. What was built

| Artifact | Path | Lines |
|---|---|---|
| Gate 0 spec | spec/RUST-FULL-VERIFIER-0.1.md | 143 |
| RSA wrapper | rust/adie-primitives/src/rsa_verify.rs | 90 |
| Hybrid verify binary | rust/adie-primitives/src/bin/adie-hybrid-verify.rs | ~280 |
| Parity test suite | tests/vomega/hybrid/test_rust_parity.py | ~210 |

## 3. Decision record

DECISIONS-0.3 Decision 9 (amended): RSA library = `rsa = "=0.9.6"`
with `features = ["sha2"]`.

Original decision (superseded): `sad-rsa = "=0.10.2"`. Amended after
DEFECT-015 (sad-rsa 0.10.2 does not build against pkcs1 0.8.0-rc.5).

## 4. Conformance

**Parity suite: 13/13 PASS.**

Every certificate produced by Python verify_hybrid and Rust
adie-hybrid-verify returns byte-identical JSON, including error codes
and messages. Cases covered:

| # | Case | Result |
|---|---|---|
| R01 | happy path both VALID | PASS |
| R02 | checks maps equal | PASS |
| R03 | RS256-only required | PASS |
| R04 | ML-DSA-only required | PASS |
| R05 | duplicate alg rejected | PASS |
| R06 | unknown alg rejected | PASS |
| R07 | downgrade rejected | PASS |
| R08 | tampered output INVALID | PASS |
| R09 | tampered output codes match | PASS |
| R10 | tampered ML-DSA sig INVALID | PASS |
| R11 | tampered RS256 sig INVALID | PASS |
| R12 | wrong keys codes match | PASS |
| R13 | empty signatures rejected | PASS |

## 5. Defects closed in Gate 0

- **DEFECT-015:** sad-rsa 0.10.2 fails to compile against pkcs1 0.8.0-rc.5.
- **DEFECT-016:** rsa 0.9.6 requires explicit `sha2` feature.
- **DEFECT-017:** Rust verifier did not check `key_id` before signature.

## 6. Risks documented

- **RISK-3.1:** `rsa 0.9.6` + RUSTSEC-2023-0071 (Marvin). Applies to
  PKCS#1 v1.5 DECRYPTION oracles targeting the private key. ADIE
  performs public-key VERIFICATION only, offline. Not applicable.
- **RISK-3.2:** dependency surface ~30 crates. Justified by mainline
  status (RustCrypto) and MIT/Apache-2.0 licensing.

## 7. Test accounting (source: tests/account.py)

| Bucket | Count |
|---|---|
| REGRESSION_TOTAL (Phase 1) | 633 |
| PHASE2_ADIE_PYTHON | 59 |
| PHASE2_ADIE_JAVASCRIPT | 11 |
| PHASE3_GATE0_RUST_PARITY | 13 |
| ACVP_UNIQUE_VECTORS | 55 |
| ACVP_VECTOR_EXECUTIONS | 150 |
| **Grand total (unique)** | **771** |

## 8. Not covered by Gate 0

- Wire format (CBOR/COSE) - Gate 2
- Governance ceremony - Gate 3
- Revocation infrastructure - Gate 4
- SLH-DSA diversity - Gate 5
- Online verification (uses offline semantics only)

## 9. Precondition for Gate 1

- Gate 0 committed on vOmega
- 771 unique tests green
- No open code DEFECTs
- spec/WIRE-FORMAT-0.2.md drafted

## 10. Next gate

**Gate 1: 3A.1 - DCP 2.1 Wire Format Specification.**

Central artifact: `spec/WIRE-FORMAT-0.2.md`.

Layering (per DECISIONS-0.3 Decision 6):

    DCP semantic model
      -> ADIE Canonical TBS
      -> DCP 2.1 CBOR data model
      -> Deterministic CBOR (RFC 8949 profile)
      -> COSE (RFC 9052)
      -> Hybrid certificate

Reference implementation: Rust.
Adapters: Python + JS.
Differential test corpus: 100 positive + 100 negative vectors minimum.

Algorithm identifiers follow RFC 9964 (ML-DSA-65 = -49, RS256 = -257).

---

**End of Phase 3 Gate 0 Closure**
