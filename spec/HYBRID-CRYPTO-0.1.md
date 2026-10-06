# ADIE-HYBRID-CRYPTO v0.1 — Specification

**Status:** Normative (specification-only, no implementation yet)
**Branch:** vOmega
**Date:** 2026-10-06
**Depends on:** META-CONTRACT-0.1, ACL-0.1, AUTHORING-0.1, ERROR-REGISTRY-0.1
**Scope:** Phase 2 — hybrid RS256 + ML-DSA-65 signatures
**Supersedes:** DCP 2.0 signature field (via DCP 2.1, see §4)

## §0. Standing

This document defines the wire, semantic, and verification contract for
hybrid signatures in ADIE. No implementation may begin until this
document is committed on `vOmega`.

## §1. Scope

In scope:
- Definition of DCP 2.1 signature field (array)
- Domain separation for the To-Be-Signed bytes
- Algorithm registry: RS256, ML-DSA-65
- Key identity and fingerprint computation for both algorithms
- Hybrid policy: AND (default), OR (migration only)
- Downgrade resistance rules
- Failure codes
- Cross-language determinism requirements
- Library selection criteria

Out of scope (§13):
- SLH-DSA
- ML-KEM (key encapsulation)
- CBOR / COSE wire encoding
- Signature aggregation
- Zero-knowledge proofs of signature correctness

## §2. Trusted Computing Base statement

**Correction to earlier draft language:**

The ML-DSA primitive implementation (library or module) is part of
the ADIE Trusted Computing Base for this profile. Trust in it is:

(a) explicit — it is named, versioned, and pinned
(b) subject to independent audit before any production claim
(c) subject to cross-implementation differential testing
(d) replaceable without protocol change
(e) not extendable to claims the library does not itself provide

The protocol specification is the reference; the library is the
implementation. Both are subject to verification.

**What we do NOT claim:**
- That the library is bug-free
- That the library is side-channel immune
- That the library is free from future cryptanalysis
- That agreement between libraries implies correctness

**What we DO claim:**
- That ADIE's use of the library is limited to its published API
- That ADIE controls all framing, domain separation, key identity,
  fingerprinting, and hybrid policy around the library
- That a compromised library can be replaced without changing the
  wire format or the semantic contract

## §3. Algorithm registry

| alg_id | Standard | Primitive | Security level | Wire pubkey | Wire sig |
|---|---|---|---|---|---|
| `RS256` | RFC 8017 | RSASSA-PKCS1-v1_5 + SHA-256 | 2048-bit modulus | SPKI DER | raw signature |
| `ML-DSA-65` | FIPS 204 | ML-DSA (n=65 params) | NIST Cat 3 | raw pk bytes | raw signature |

**Version pinning:**
- RS256: unchanged from Phase 1
- ML-DSA-65: FIPS 204 (2024-08-13) with the 2026 errata applied
- Library versions pinned in §12

## §4. Wire format — DCP 2.1

DCP 2.1 replaces the `signature` (singular, object) field with
`signatures` (plural, array). DCP 2.0 remains valid read-only.

**DCP 2.1 required fields:**
```
dcp_version: "2.1"
...  (same 13 semantic fields)
signatures: [ {"alg": "...", "key_id": "...", "value": "..."}, ... ]
```

**DCP 2.0 compatibility:**
- DCP 2.0 certs MUST still verify under DCP 2.0 rules.
- A DCP 2.0 cert has exactly one signature with `alg: "RS256"`.
- A DCP 2.1 cert has 1 or more signatures.

**Signatures array rules:**
- Minimum length: 1
- Maximum length: 3 (RS256 + ML-DSA-65 + one future alg)
- No duplicate `alg` in one array
- Order is not significant for verification, but SHOULD be sorted
  by `alg` for canonical emission

**Signature object:**
```
{
  "alg":    "<alg_id>",
  "key_id": "sha256:<64 hex>",
  "value":  "base64:<base64 of raw signature bytes>"
}
```

## §5. To-Be-Signed (TBS)

The message signed by every algorithm is byte-identical:

```
TBS = "ADIE-SIG-V2\0" || JCS(certificate_without_signatures)
```

Where:
- `"ADIE-SIG-V2\0"` is an ASCII domain separation tag (13 bytes + NUL).
  Exact bytes: `41 44 49 45 2D 53 49 47 2D 56 32 00`
- `JCS(...)` is RFC 8785 canonical JSON.
- `certificate_without_signatures` = the DCP object with the
  `signatures` field removed (not nulled, removed).
- For DCP 2.0 legacy certs, `signature` (singular) is removed instead.

**Normative:** No signature may sign the output of another signature.
No signature may sign a canonicalized version that includes any
signature field.

**Cross-language requirement:** Python, JavaScript, and Rust MUST
produce byte-identical TBS for the same certificate.

## §6. Key identity and fingerprint

**Universal rule:** `key_id = "sha256:" + hex(SHA-256(pubkey_encoding))`

| Algorithm | pubkey_encoding |
|---|---|
| RS256 | SPKI DER (RFC 5280) |
| ML-DSA-65 | SPKI DER with OID id-ml-dsa-65 (RFC 9964) |

**Signature computation:**
- RS256: `RSASSA-PKCS1-v1_5(sk, SHA-256, TBS)` → 256 bytes
- ML-DSA-65: `ML-DSA.Sign(sk, TBS)` per FIPS 204 → 3309 bytes

**Base64 encoding:**
- All signature values use `base64:` prefix (standard, not URL-safe).
- No line breaks.
- No padding omitted.

## §7. Hybrid policy

**Default policy: AND.**
```
Verify_H(cert) = AND over required algorithms
```

**Migration policy: OR (explicit opt-in).**
- Only permitted when the relying party's policy explicitly selects it.
- MUST be recorded as a decision event in the manifest.
- Not the default. Not inferred.

**Required algorithms** are declared in the manifest universe
(`algorithms` field). A verifier knowing the manifest knows which
algorithms are required.

**Semantics:**
- If `required = [RS256, ML-DSA-65]` and cert has both valid → PASS
- If either fails → FAIL with the corresponding code
- If cert has only RS256 → FAIL with `E_SIGNATURE_DOWNGRADE`
- If cert has only ML-DSA-65 (future) → FAIL with
  `E_SIGNATURE_DOWNGRADE` if RS256 is required

## §8. Downgrade resistance

**Rule:** A verifier with a manifest declaring `required = X` MUST
reject any certificate that does not contain a valid signature for
every `alg` in `X`.

**Failure code:** `E_SIGNATURE_DOWNGRADE`

**No silent fallback.** A hybrid verifier MUST NOT accept a
certificate with only RS256 when ML-DSA-65 is required, even if
RS256 verifies.

**No silent upgrade.** A verifier that does not support ML-DSA-65
MUST return `E_SIGNATURE_UNKNOWN_ALG`, not a downgrade.

## §9. Failure codes (additions to ERROR-REGISTRY-0.1)

| Code | Condition | Terminal |
|---|---|---|
| `E_SIGNATURE_HYBRID_MISSING` | A required algorithm's signature absent | YES |
| `E_SIGNATURE_HYBRID_INVALID` | A required signature fails verification | YES |
| `E_SIGNATURE_DOWNGRADE` | Required alg missing; only weaker present | YES |
| `E_SIGNATURE_UNKNOWN_ALG` | `alg` not in registry | YES |
| `E_SIGNATURE_DUPLICATE_ALG` | Same `alg` twice in one cert | YES |
| `E_SIGNATURE_KEY_MISMATCH` | `key_id` doesn't match registry entry | YES |
| `E_SIGNATURE_TBS_DIVERGENCE` | Cross-language TBS bytes differ (test-only) | YES |

## §10. Cross-language determinism requirements

For every vector in the Phase 2 test suite:

1. TBS bytes are byte-identical across Python, JavaScript, Rust.
2. Given the same sk and TBS, the signature bytes are byte-identical
   for RS256 (deterministic) and byte-identical for ML-DSA-65
   (deterministic per FIPS 204 §3.6.3 — no randomized mode in v0.1).
3. The verification verdict is byte-identical across the three
   languages for every certificate and every manifest policy.
4. Error codes and messages are byte-identical for every failure case.

**Failure to meet any of the above blocks Phase 2.**

## §11. Test vector requirements

Phase 2 exit gate requires:

- **KATs**: NIST ACVP ML-DSA-65 keygen/sign/verify test vectors
  (subset, ~20 keygen + ~20 sign + ~20 verify)
- **Cross-lang signatures**: same sk + same TBS → same signature
  bytes across Python/JS/Rust (10 vectors)
- **Hybrid valid**: RS256 + ML-DSA-65 both valid (10 vectors)
- **Hybrid invalid**: each signature fails independently (20 vectors)
- **Downgrade rejected**: RS256-only against hybrid manifest (5 vectors)
- **Unknown alg rejected** (5 vectors)
- **Duplicate alg rejected** (5 vectors)
- **Key mismatch rejected** (5 vectors)
- **TBS divergence test**: deterministic generation of TBS bytes,
  compared across three languages (10 vectors)

**Total minimum: 100 new vectors.**
**All 435 existing tests must remain green.**

## §12. Library selection criteria

For each language, the ML-DSA library MUST satisfy:

1. **Standard conformance**: FIPS 204 (with 2026 errata applied).
2. **Deterministic signing**: no randomized nonce in the v0.1 profile.
3. **Published test vector compliance**: NIST ACVP KATs pass.
4. **Version pinned**: exact version in lockfile (Cargo.lock,
   package-lock.json, requirements.txt with ==).
5. **Audit status disclosed**: the spec MUST record whether the
   library has undergone independent security audit. If not,
   this is a **documented risk**, not a hidden one.
6. **Replaceable**: the wrapper MUST isolate the library behind
   ADIE's own interface (no direct calls from protocol code).

**Candidate libraries (to be finalized in Block B):**

| Language | Candidate | Audit status |
|---|---|---|
| Rust | `ml-dsa` (RustCrypto) | Not independently audited (self-declared) |
| Python | `pycryptodome` or `pqcrypto` | TBD |
| JavaScript | `@noble/post-quantum` | TBD |

**If any library lacks audit**, the spec MUST state:
```
"Library <name> <version> has not undergone independent
security audit as of <date>. This is a documented risk.
The library is isolated behind <wrapper>, is replaceable,
and is not relied upon for correctness of ADIE's
semantic contract."
```

## §13. Non-goals

Explicitly NOT in Phase 2:
- SLH-DSA (reserved for Phase 2.5 if needed)
- ML-KEM key encapsulation
- Signature aggregation
- ZK proofs of signature correctness
- Side-channel resistance claims
- Timing-attack resistance claims
- Protection against compromised library
- Multi-signature schemes (threshold, ring)
- CBOR / COSE wire encoding
- Post-quantum key exchange

## §14. Exit gate

Phase 2 is complete when:

- All Phase 2 test vectors pass (§11)
- All 435 pre-existing tests remain green
- Three-language differential agreement on every vector
- DEFECTS-LOG.md is complete (no open defects)
- CONTINUITY.md records the library versions used
- No code was written before this spec was committed

## §15. Amendment

This document is append-only. Any change:
- requires a new version (0.2, 0.3, ...)
- is committed on vOmega
- does not modify META-CONTRACT-0.1, ACL-0.1, AUTHORING-0.1,
  REGISTRY-0.1, or any existing test vector

**End of ADIE-HYBRID-CRYPTO-0.1**

---

## §12.1. Library selection (Block B, 2026-10-06)

**Candidate libraries — final selection:**

| Language | Package | Version | Pinned by | Audit status |
|---|---|---|---|---|
| Rust | `ml-dsa` (RustCrypto) | 0.1.1 | Cargo.lock | **Unaudited** (self-declared) |
| Python (A) | `pqcrypto` | 1.0.0 | requirements.txt | Wraps PQClean; wrapper unaudited |
| Python (B) | `dilithium-py` | 1.4.0 | requirements.txt | Pure-Python reference, independent |
| JavaScript | `@noble/post-quantum` | 0.7.1 | package-lock.json | Pre-1.0; audit status undisclosed |
| Python (RS256) | `pycryptodome` | 3.24.0 | requirements.txt | Already used in Phase 1 |

**Rationale for two Python implementations:**
- `pqcrypto` (fast, C-backed) is the production path
- `dilithium-py` (pure Python, independent lineage) is the cross-check
- Agreement on NIST ACVP KAT vectors between the two
  establishes that no single Python wrapper's bugs are silently trusted

**Recorded risks:**

```
RISK-2.1: ml-dsa 0.1.1 is pre-1.0 and not independently audited.
Mitigation: isolated behind ADIE's own wrapper; replaceable;
protocol commit does not depend on its internals.

RISK-2.2: pqcrypto 1.0.0 wrapper not audited; PQClean itself is
community-maintained but has not been through formal FIPS 204
validation that we can verify from this environment.
Mitigation: cross-checked against dilithium-py.

RISK-2.3: @noble/post-quantum 0.7.1 is pre-1.0, audit status
undisclosed by author.
Mitigation: isolated; replaceable; verified against Python/Rust
on every test vector.

RISK-2.4: Exact wheel availability for Python 3.12 unknown until
Block C attempts installation. If pqcrypto wheel is missing,
fallback is dilithium-py alone (documented degradation).
```

**What is NOT claimed:**
- That any of these libraries is bug-free
- That any of them resists side-channels
- That absence of audit is acceptable for production indefinitely
- That agreement between two implementations implies correctness

**What IS claimed:**
- Each library's role is explicit and replaceable
- Each library is pinned by exact version
- Each library is wrapped by ADIE code (no direct protocol use)
- Every library is cross-verified against the others on KAT vectors

## §12.2. Installation gate

No installation occurs until §12.1 is committed on `vOmega`.

After commit, Block C:
1. Installs each library with its exact pin.
2. Runs NIST ACVP ML-DSA-65 KAT vectors.
3. Records SHA-256 of each downloaded wheel/crate in
   `spec/HYBRID-CRYPTO-0.1.md §12.3` (to be added).
4. Any KAT failure → STOP; do not proceed to hybrid signing.

## §12.3. Downloaded artifact hashes

(To be filled during Block C. Left empty in Block B.)

---

## §12.3. Downloaded artifact hashes

### Python (C.1 — 2026-10-06)

| Package | Wheel filename | SHA-256 |
|---|---|---|
| dilithium-py 1.4.0 | `dilithium_py-1.4.0-py3-none-any.whl` | `dda3ae43e6e3d212ae1fe1b30d5b6dffe5e25a1f389d1fea26faad4afdc33ff8` |
| pqcrypto 1.0.0 | `pqcrypto-1.0.0-cp39-abi3-manylinux_2_34_x86_64.whl` | `7068532dbc1225a9d668d59940bd96dc13f40175a757b2e31c69aa697781f4d0` |

Installed into: `.venv/`
Python version: 3.12.3
cryptography in venv: 50.0.1

### Rust (C.2 — pending)

(To be recorded.)

### JavaScript (C.3 — pending)

(To be recorded.)

### Verification notes

- `pqcrypto.sign.ml_dsa_65` imports cleanly
- `dilithium_py.ml_dsa.ML_DSA_65` imports cleanly
- Both verified to have identical module path structure for the ML-DSA-65 variant

### GAP-5-CORRECTED: Rust ML-DSA is enabled

**Date:** 2026-10-06
**Supersedes:** earlier GAP-5 entry (now known incorrect, committed in 56717dc)

**History:**
- First attempt: `cargo fetch` failed because Cargo 1.75.0 (from apt)
  does not support `edition2024`, required by `crypto-common 0.2.2`.
- Second attempt: `rustup` official channel installed rustc 1.99.0
  and cargo 1.99.0. `ml-dsa 0.1.1` then fetched and built cleanly
  in 45 seconds. `adie-primitives` rebuilt under 1.99.0 and its
  435/435 conformance suite remained green.

**Consequence:**
- Rust ML-DSA is available. GAP-5 is retracted.
- Block C.2 proceeds with `ml-dsa = "=0.1.1"` added to
  `rust/adie-primitives/Cargo.toml`.

**Note on prior commitment 56717dc:**
An earlier commit recorded GAP-5 as a permanent deferral. That
commit was based on the first-attempt failure and did not anticipate
the successful retry. DEFECT-007 is logged for the process error:
advancing state on partial information before re-verification.

**Not retracted:** RISK-2.1 (ml-dsa 0.1.1 is pre-1.0 and unaudited).
This risk is independent of whether it builds.
