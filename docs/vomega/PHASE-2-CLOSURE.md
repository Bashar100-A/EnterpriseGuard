# ADIE vΩ — Phase 2 Closure

**Date:** 2026-10-07
**Status:** Phase 2 formally closed
**Predecessor:** PHASE-1-CLOSURE.md

## §1. Scope closed

Phase 2 covered hybrid cryptographic signatures: RS256 + ML-DSA-65.
The semantic layers (Phase 1) are unchanged and remain green.

## §2. Specifications

| Spec | Lines | Status |
|---|---|---|
| HYBRID-CRYPTO-0.1 | ~415 | Normative |
| MLDSA-XLANG-001 | 60 | Test vector |
| ACVP KAT (keygen/siggen/sigver) | 55 vectors | Derived from NIST |

## §3. Implementations

| Module | Language | Purpose |
|---|---|---|
| protocol/hybrid/tbs.py | Python | TBS builder |
| protocol/hybrid/tbs.mjs | JavaScript | TBS builder mirror |
| protocol/hybrid/sign.py | Python | RS256 + ML-DSA-65 signer |
| protocol/hybrid/verify.py | Python | Hybrid verifier |
| protocol/hybrid/certificate.py | Python | DCP 2.1 assembler |
| rust/adie-primitives/src/mldsa.rs | Rust | ML-DSA wrapper (ctx-aware) |
| rust/adie-primitives/src/bin/adie-mldsa.rs | Rust | ML-DSA CLI |
| js/run_acvp_kat.mjs | JavaScript | ACVP KAT runner |

## §4. Conformance

### Phase 2 suites (all PASS)

| Suite | Count | Detail |
|---|---|---|
| test_tbs.py | 12 | Python TBS |
| test_tbs.mjs | 11 | JS TBS |
| TBS differential | 5 | py ≡ js |
| test_sign.py | 16 | Hybrid signer |
| test_verify.py | 20 | Hybrid verifier |
| test_e2e.py | 11 | End-to-end DCP 2.1 |
| **Phase 2 total** | **75** | all pass |

### NIST ACVP ML-DSA-65 (pure)

| Language | keygen | siggen | sigver | Total |
|---|---|---|---|---|
| Python (dilithium-py 1.4.0) | 25/25 | 15/15 | 15/15 | 55/55 |
| JavaScript (@noble 0.7.1) | 25/25 | 15/15 | 15/15 | 55/55 |
| Rust (RustCrypto ml-dsa 0.1.1) | 25/25 | GAP-8 | 15/15 | 40/40 |
| **ACVP total** | | | | **150/150** |

### MLDSA-XLANG-001 (cross-language byte equality)
seed = 0x42*32, TBS = "ADIE-SIG-V2\0" || '{"test":"vector"}', ctx = b""
Python ≡ JS ≡ Rust: pk, sig, byte-identical

## §5. Phase 1 regression

All 633 Phase 1 tests remain green:
- frozen 51, vΩ 12, META 40, REGISTRY 20, ACL 40, AUTHORING 20, PILOT 15, Rust 435

## §6. Defects closed in Phase 2

| ID | Category | Summary |
|---|---|---|
| DEFECT-010 | process | pqcrypto has no deterministic sign/keygen → verify-only |
| DEFECT-011 | code | ML-DSA wrapper hard-coded ctx=b"" |
| DEFECT-012 | code | Rust decode errors should be Ok(false), not Err |
| DEFECT-013 | spec | Domain tag byte-count typo (13→12) |

## §7. Gaps opened in Phase 2

| GAP | Summary | Status |
|---|---|---|
| GAP-8 | Rust sigGen not covered (seed-only API) | Documented |
| GAP-9 | ML-DSA key_id uses raw pk, not SPKI | Documented |

## §8. Risks

| RISK | Summary | Status |
|---|---|---|
| 2.1 | ml-dsa 0.1.1 unaudited (self-declared) | Active, isolated |
| 2.2 | pqcrypto wrapper unaudited | Active, verify-only |
| 2.3 | @noble pre-1.0, audit undisclosed | Active |

## §9. NOT covered by Phase 2

- SPKI wrapping for ML-DSA (GAP-9)
- Rust sigGen from raw sk (GAP-8)
- SLH-DSA
- ML-KEM
- Hybrid KEM (key exchange)
- CBOR/COSE wire encoding
- Signature aggregation
- ZK proofs of signature correctness
- Hardware attestation (TEE)
- Independent security audit

## §10. Precondition for Phase 3

- Phase 2 committed on vOmega
- 758 (unique) tests (648 + 75) all green
- No open code DEFECT
- Target spec for Phase 3 exists

## §11. Candidate Phase 3 topics (to be decided)

- **3A:** DCP 2.1 wire format (CBOR/COSE) — encoding the hybrid cert
- **3B:** Governance ceremony — manifest thresholds, key rotation
- **3C:** Revocation infrastructure — CRL, offline semantics
- **3D:** SLH-DSA family diversity (FIPS 205)
- **3E:** Rust full hybrid verifier (extend Phase 1.12-lite)

Recommendation (from Phase-1 & Phase-2 lessons): **3A first**, because
wire format determines whether Phase 4 can distribute certificates
across languages without ambiguity.

---

**End of PHASE-2-CLOSURE**


---

## §12. Correction (2026-10-07)

An earlier draft of this document claimed "723/723 tests." That
number was computed incorrectly. Real, measured numbers:

| Bucket | Count | Source |
|---|---|---|
| Phase 1 regression | 633 | tests/account.py |
| Phase 2 Python ADIE | 59 | tests/account.py |
| Phase 2 JavaScript ADIE | 11 | tests/account.py |
| ACVP vector executions | 150 | 3 languages × 50 avg |
| ACVP unique vectors | 55 | 25 keygen + 15 siggen + 15 sigver |
| **Grand total (unique)** | **758** | regression + py + js + acvp-unique |

DEFECT-014 records the process failure.

See `tests/account.py` for the authoritative source. Any external
claim MUST cite numbers from that tool, never from memory or from
a commit message.
