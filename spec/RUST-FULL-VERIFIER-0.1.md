# ADIE-RUST-FULL-VERIFIER v0.1 - Gate 0 Specification

**Status:** Normative (specification only, no implementation yet)
**Date:** 2026-10-07
**Depends on:** HYBRID-CRYPTO-0.1, META-CONTRACT-0.1, DECISIONS-0.3
**Scope:** Phase 3, Gate 0 - Rust verifies full DCP 2.1 certificates

## Section 0. Purpose

Close the gap between Python/JS (which verify full DCP 2.1 hybrid
certificates) and Rust (which verifies keygen + sigver but not the
full certificate path).

Exit criterion: For every DCP 2.1 certificate produced by the
Phase 2 E2E pilot, Rust and Python MUST return byte-identical
assurance vectors (including error codes and messages).

## Section 1. What Rust MUST verify

For a given (cert_with_signatures, public_keys):

1. Parse DCP 2.1 structure: required fields present, dcp_version == 2.1
2. Recompute ClaimRoot over the 13 named fields (existing capability)
3. Check ClaimRoot against declared value
4. Check Binding:
   - binding.audience == expected_audience (if expected given)
   - binding.request_hash == SHA-256(H_A(request, JCS(request)))
5. Check authoring closure:
   - 6 required keys present
   - SHA-256 digests well-formed
   - acl_version == 0.1
6. Compute TBS: domain tag || JCS(cert_without_signatures)
7. For each signature in signatures (sorted by alg):
   - Check alg in {RS256, ML-DSA-65}
   - Check key_id matches expected for provided public key
   - Verify signature over TBS
8. Check hybrid policy: every required alg present and valid
9. Emit assurance vector with status VALID|INVALID, code, message

## Section 2. What Rust does NOT verify (unchanged)

- Revocation status (Phase 3C)
- Governance manifest chain (Phase 3B)
- Hardware attestation (Phase 5+)
- ZK proofs (Phase 4+)

## Section 3. RSA verification policy

RSA-2048 verification uses the rsa crate (RustCrypto family, same
ecosystem as ml-dsa). This follows DECISIONS-0.2 trusted-library
policy: primitive from library, protocol from us.

RISK-3.1: rsa crate MSRV and audit status MUST be checked and
recorded before commit. If MSRV > 1.75 or audit status is unclear,
fallback is ring crate (native, more audited, heavier dependency).

RISK-3.2: RSA verification must reject all malformed padding
strictly. Test vectors from RFC 8017 MUST be included.

## Section 4. TBS and domain separation

Same as spec/HYBRID-CRYPTO-0.1 Section 5. Rust MUST compute TBS from
the same byte-identical canonical form as Python and JS. Verified
by differential on all E2E vectors.

## Section 5. Error code parity

Error codes and messages MUST match Python verify_hybrid exactly:

| Code | Condition |
|---|---|
| E_SIGNATURE_HYBRID_MISSING | signatures empty or required pub key missing |
| E_SIGNATURE_DUPLICATE_ALG | same alg appears twice |
| E_SIGNATURE_UNKNOWN_ALG | alg not in registry |
| E_SIGNATURE_DOWNGRADE | required alg absent |
| E_SIGNATURE_HYBRID_INVALID | any signature fails |
| E_SIGNATURE_KEY_MISMATCH | key_id does not match pub key |
| E_CLAIM_ROOT_MISMATCH | recomputed root differs from declared |
| E_BINDING_REQUEST_HASH | request_hash mismatch |
| E_BINDING_AUDIENCE_MISMATCH | expected audience mismatch |
| E-META-20 | authoring closure malformed |
| E-META-14 | acl_version wrong |

Message slicing: Rust MUST replicate Python message format exactly.
This was a source of DEFECT-006 and DEFECT-012. Every error path is
verified byte-for-byte.

## Section 6. CLI surface

Binary name: adie-hybrid-verify

stdin:
    {certificate_json, public_keys: {RS256, ML-DSA-65}, expected_audience}

stdout: canonical JSON assurance vector

public_keys format:
    RS256: PEM string
    ML-DSA-65: hex-encoded 1952-byte raw pk

## Section 7. Differential test

For every certificate produced by tests/vomega/hybrid/test_e2e.py:
1. Run Python verify_hybrid -> assurance vector A
2. Run Rust adie-hybrid-verify -> assurance vector B
3. Assert A == B byte-for-byte after canonical JSON serialization

Plus: all 20 negative vectors from test_verify.py MUST produce
matching error codes and messages.

## Section 8. GAP-8 status

GAP-8 (Rust sigGen not covered by ACVP due to seed-only API) remains
open. Gate 0 does NOT close GAP-8. Gate 0 closes the verifier path.

Resolving GAP-8 requires either:
- A future RustCrypto API exposing sign-from-encoded-sk
- Or an ADIE adapter that reconstitutes the RustCrypto internal key
  format from FIPS 204 standard sk encoding

This is deferred to Phase 3.5 (or later), tracked separately.

## Section 9. Exit criteria

Gate 0 is closed when:

- All E2E pilot vectors (11) produce byte-identical Python/Rust
  assurance vectors
- All negative vectors (20) produce byte-identical error codes
- RISK-3.1 and RISK-3.2 are documented in DEFECTS-LOG.md
- New Rust binary built and committed
- No regression in Phase 1 (633) or Phase 2 (70) suites

## Section 10. Not covered by this spec

- Signing (see GAP-8)
- CBOR/COSE wire (Gate 2, spec/WIRE-FORMAT-0.2.md)
- Revocation, governance, hardware
- Any cryptographic primitive not present in the certificate

---

**End of ADIE-RUST-FULL-VERIFIER-0.1**
