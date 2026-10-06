# ADIE WIRE FORMAT v0.2

**Document:** WIRE-FORMAT-0.2
**Status:** Normative — Source of Truth for DCP 2.1 interchange encoding
**Date:** 2026-10-07
**Authority:** Commander Order 3A_LEVELS_GO (2026-10-07)
**Depends on:** HYBRID-CRYPTO-0.1, META-CONTRACT-0.1, DECISIONS-0.3, RFC 8949, RFC 9052, RFC 9964, RFC 8017, FIPS 204 (with July 2026 errata)
**Scope:** Phase 3, Gate 1 — DCP 2.1 binary interchange

## Section 0. Standing

This document is the normative source of truth for the binary
interchange encoding of DCP 2.1 certificates. It does not authorize
any implementation. It precedes all implementation.

Any disagreement between this document and an implementation is
resolved in favor of this document, or this document is amended
via a new version.

## Section 1. Scope

In scope:
- DCP 2.1 semantic data model (the fields and their meanings)
- Field registry with numeric labels
- Critical vs non-critical field policy
- Versioning rules
- ADIE CBOR data model (subset of RFC 8949)
- ADIE Deterministic CBOR Profile (a strict subset of RFC 8949)
- Malformed-input rejection matrix
- COSE structure (RFC 9052)
- ML-DSA-65 COSE mapping (RFC 9964)
- RS256 COSE mapping (RFC 9052)
- ADIE Hybrid Profile (composite classical + PQ)
- Algorithm/Key identity binding (Identity Binding Invariant)
- Downgrade resistance rules
- Canonical and negative vector requirements
- Interoperability requirements
- Fuzzing requirements

Out of scope:
- ZK proofs
- IVC / recursive accumulation
- FHE / SMPC / garbled circuits
- SLH-DSA
- TEE / HSM attestation
- Governance ceremony
- Revocation infrastructure
- Online verification

## Section 2. Terminology

- **DCP 2.1**: Decision Certificate Protocol, version 2.1.
- **Semantic contract**: the meaning of fields, independent of encoding.
- **Canonical TBS**: the byte string over which signatures are computed.
- **CBOR data model**: the set of values admitted by ADIE DCP 2.1.
- **Deterministic CBOR**: an encoding whose bytes are a pure function
  of the value, per RFC 8949 Section 4.2.
- **COSE**: CBOR Object Signing and Encryption (RFC 9052).
- **ADIE Hybrid Profile**: ADIE's profile combining RS256 + ML-DSA-65.
- **Identity Binding Invariant**: Algorithm + Key ID + Public Key +
  Fingerprint + TBS treated as one interconnected system.
- **Critical field**: a field whose absence or unknown type MUST cause
  rejection.
- **Non-critical field**: a field whose unknown extension MAY be
  ignored if the profile permits.

## Section 3. DCP 2.1 Semantic Data Model

DCP 2.1 extends DCP 2.0 by replacing the singular `signature` field
with an array `signatures`. The 13 named semantic fields are unchanged
from DCP 2.0:

| # | Field | Type | Required | Semantic role |
|---|---|---|---|---|
| 01 | issuer | map | yes | issuer DID + key_id |
| 02 | subject | map | yes | subject identification |
| 03 | request | map | yes | original request |
| 04 | context | map | yes | execution context |
| 05 | policy | map | yes | policy reference + AST |
| 06 | model | map | yes | model reference |
| 07 | data | map | yes | data commitment |
| 08 | runtime | map | yes | runtime measurement |
| 09 | output | map | yes | decision output |
| 10 | binding | map | yes | audience/purpose/resource |
| 11 | temporal | map | yes | issuance time |
| 12 | evidence | map | yes | attestations list |
| 13 | authoring | map | yes | ACL closure |

Plus two structural fields:

| Field | Type | Required | Purpose |
|---|---|---|---|
| dcp_version | text | yes | "2.1" for this document |
| claim_id | text | yes | unique per certificate |
| claim_root | bytes (32) | yes | Merkle root over 13 fields |
| signatures | array of maps | yes | RS256 + ML-DSA-65 |
| proofs | array | yes | (empty in Phase 2; reserved) |

Any field not in this table is treated per Section 5.

## Section 4. Field Registry

Numeric labels for CBOR map keys follow a stable registry. Once
assigned, a label is never reused (I34).

### 4.1 Top-level labels

| Label | Field | Type |
|---|---|---|
| 1 | dcp_version | text |
| 2 | claim_id | text |
| 3 | issuer | map |
| 4 | subject | map |
| 5 | request | map |
| 6 | context | map |
| 7 | policy | map |
| 8 | model | map |
| 9 | data | map |
| 10 | runtime | map |
| 11 | output | map |
| 12 | binding | map |
| 13 | temporal | map |
| 14 | evidence | map |
| 15 | authoring | map |
| 16 | proofs | array |
| 17 | claim_root | bytes |
| 18 | signatures | array |

### 4.2 Signature object labels

| Label | Field | Type |
|---|---|---|
| 1 | alg | text |
| 2 | key_id | text |
| 3 | value | bytes |

### 4.3 Binding object labels

| Label | Field |
|---|---|
| 1 | audience |
| 2 | purpose |
| 3 | resource |
| 4 | request_hash |
| 5 | nonce |
| 6 | certificate_id |

## Section 5. Critical vs Non-Critical Field Policy

Commander order 3A_LEVELS_GO Section 7:

- **Unknown critical field** -> REJECT.
- **Unknown non-critical field** -> behavior explicitly defined by
  this profile (default: ignore).
- **Version-breaking structure** -> REJECT.
- **Ambiguous interpretation** -> REJECT.

Concretely:

1. Top-level fields in Section 4.1 are all critical.
2. A top-level key not in Section 4.1 causes E_WIRE_UNKNOWN_CRITICAL.
3. A field inside `signatures[]`, `binding`, `issuer`, or `temporal`
   that is not in its section is critical.
4. A field inside `context`, `evidence`, or `authoring` not in its
   section is non-critical and MUST be preserved on round-trip.
5. A field whose type disagrees with Section 3 is critical and causes
   E_WIRE_TYPE_MISMATCH.
6. A field whose interpretation depends on external state not present
   in the certificate is critical and causes E_WIRE_AMBIGUOUS.

## Section 6. Versioning Rules

1. `dcp_version` is the only version token.
2. `dcp_version` MUST be exactly "2.1" for this specification.
3. Any other value causes E_WIRE_VERSION.
4. No silent upgrade or downgrade. A consumer knowing only "2.1" MUST
   reject "2.2" and MUST reject "2.0" when the semantics differ.
5. CBOR data model changes that alter semantics require a new
   `dcp_version`, not a patch.
6. Field registry additions that do not change existing semantics MAY
   occur within "2.1" if declared as non-critical (Section 5 rule 4).

## Section 7. ADIE CBOR Data Model

ADIE's CBOR data model is a **strict subset** of RFC 8949's general
data model.

Allowed types:
- unsigned integer (major type 0)
- negative integer (major type 1)
- byte string (major type 2)
- text string (major type 3) - MUST be valid UTF-8
- array (major type 4)
- map (major type 5) with integer keys only (labels per Section 4)
- simple values: false (0xF4), true (0xF5), null (0xF6)

**Map keys are unsigned integers** assigned by the field registry
(Section 4). Text-string keys, byte-string keys, and composite keys
are not admitted. This aligns with COSE (RFC 9052), which uses
integer labels for core COSE_Key and COSE_Sign1 fields.

Forbidden in the ADIE profile:
- floating-point (major type 7, additional 25/26/27)
- indefinite-length strings, arrays, or maps (additional 31)
- tags (major type 6)
- text-string keys
- byte-string keys
- composite keys (arrays/maps as keys)
- duplicate map keys
- NaN, Infinity, undefined (0xF7)
- overlong integer encodings (RFC 8949 Section 3.4.3 preferred
  serialization)

## Section 8. ADIE Deterministic CBOR Profile

ADIE's profile is layered over RFC 8949 Section 4.2.1.

Determinism requirements (all normative):

1. **Integer encoding**: shortest form. No overlong encoding.
2. **Map key ordering**: map keys are unsigned integers (Section 4).
   They are sorted by their encoded bytes. For ADIE's integer-keyed
   maps with canonical (shortest-form) integer encoding, RFC 8949's
   "bytewise lexicographic order of the encoded key" reduces to
   numeric ascending order.
3. **Definite-length**: all strings, arrays, and maps MUST use
   definite-length encoding. Indefinite-length (0x1F, 0x5F, 0x7F,
   0x9F, 0xBF) is rejected.
4. **No floats**: additional info 25/26/27 is rejected.
5. **No tags**: major type 6 is rejected.
6. **UTF-8 normalization**: text strings MUST be valid UTF-8. NFC
   normalization is NOT applied by the encoder; certificates carry
   NFC-normalized text by construction (see META-CONTRACT-0.1).
7. **Duplicate keys**: rejected before decoding.
8. **Trailing bytes**: any byte after the top-level CBOR item is
   rejected.

These rules are the ADIE Deterministic CBOR Profile. They are a
subset of RFC 8949's "deterministic encoding" but are stricter:
they forbid tags and floats entirely.

## Section 9. Malformed-Input Rejection Matrix

Every input to a DCP 2.1 CBOR decoder MUST be classified into one of:

| Category | Meaning | Action |
|---|---|---|
| well-formed + valid + expected | conforms to Sections 7-8 and Section 3 | ACCEPT |
| well-formed + valid + unexpected | conforms to Sections 7-8 but violates Section 3 (missing required field, unknown critical) | REJECT (specific code) |
| well-formed + invalid | violates Section 8 (noncanonical) | REJECT E_WIRE_NONCANONICAL |
| malformed | does not parse as CBOR | REJECT E_WIRE_MALFORMED |

Specific codes:

| Code | Condition |
|---|---|
| E_WIRE_MALFORMED | CBOR parse failure |
| E_WIRE_TRAILING | bytes after top-level item |
| E_WIRE_INDEFINITE | indefinite-length item |
| E_WIRE_FLOAT | float encoding present |
| E_WIRE_TAG | tag present |
| E_WIRE_DUP_KEY | duplicate map key |
| E_WIRE_NONCANONICAL_INT | overlong integer |
| E_WIRE_NONCANONICAL_MAP | map keys not sorted |
| E_WIRE_INVALID_UTF8 | text string not valid UTF-8 |
| E_WIRE_TYPE_MISMATCH | field type differs from Section 3 |
| E_WIRE_MISSING_FIELD | required field absent |
| E_WIRE_UNKNOWN_CRITICAL | unknown critical field |
| E_WIRE_VERSION | dcp_version not "2.1" |
| E_WIRE_AMBIGUOUS | interpretation requires external state |

## Section 10. COSE Structure (RFC 9052)

The certificate's signatures array uses COSE_Sign1 semantics for
each entry, but they are carried inside the DCP 2.1 wrapper, not
as a separate top-level COSE object.

Each signature object encodes as a CBOR map with three integer keys
(Section 4.2):

    1: alg     (text)
    2: key_id  (text)
    3: value   (bytes)

The `value` field contains the raw signature bytes (not base64).
In JSON they are represented as "base64:<standard-base64>"; in CBOR
they are raw bytes.

The protected header concept from COSE is deferred to a future
version of this document. In DCP 2.1 the signature object is
flat: three fields, no nested protected/unprotected headers.

## Section 11. ML-DSA-65 Mapping (RFC 9964)

ML-DSA-65 algorithm identifier:

- **COSE alg value**: -49 (per RFC 9964 / IANA COSE Algorithms)
- **JOSE alg value**: "ML-DSA-65" (per RFC 9964)
- **Public key encoding (COSE)**: AKP (Algorithm Key Pair) with
  parameter -1 = pub as a byte string of exactly 1952 bytes.
- **Private key seed**: 32 bytes (FIPS 204 Seed).
- **Signature**: raw bytes, exactly 3309 bytes.
- **Signing context (`ctx`)**: MUST be empty. ADIE domain separation
  occurs in the TBS prefix (Section 13.2), not in the ML-DSA ctx.

**Conformance statement:** ADIE's ML-DSA-65 usage conforms to FIPS 204
(2024-08-13) with the July 2026 errata applied, and follows the COSE
identifier from RFC 9964. ADIE does not redefine ML-DSA representation.

## Section 12. RS256 Mapping (RFC 9052)

RS256 algorithm identifier:

- **COSE alg value**: -257
- **Public key encoding**: SPKI DER wrapped as COSE_Key or as a
  byte string containing SPKI DER (see Section 14.3)
- **Signature**: raw bytes, exactly 256 bytes for RSA-2048
- **Hash**: SHA-256
- **Padding**: PKCS#1 v1.5 (RSASSA-PKCS1-v1_5)

## Section 13. ADIE Hybrid Profile

ADIE uses COSE per the relevant standards profiles (RFC 9052 for
COSE_Key structure and algorithm binding; RFC 9964 for ML-DSA-65
algorithm identifiers). ADIE does not claim to be RFC 9964, nor
does it claim compliance with any composite-signature standard.
ADIE Hybrid Profile is an ADIE-defined profile that uses those
standards as building blocks.

ADIE does not claim compliance with any composite ML-DSA draft
(currently an Internet-Draft in the RFC Editor process). If such a
draft becomes an RFC, ADIE MAY adopt it and record the exact
revision in this document.

### 13.1 The Hybrid Signature

A DCP 2.1 certificate contains a `signatures` array of at least one
element and at most three. Every element signs the same TBS.

### 13.2 TBS (To-Be-Signed)

    TBS = "ADIE-SIG-V2\0" || JCS(certificate_without_signatures)

Where:
- "ADIE-SIG-V2\0" is the exact 12-byte domain tag
  (41 44 49 45 2D 53 49 47 2D 56 32 00).
- JCS(...) is RFC 8785 canonical JSON of the certificate with the
  `signatures` field removed (not nulled).
- The same TBS is signed by every algorithm in `signatures[]`.

**TBS is independent of wire encoding.** ADIE computes TBS from the
JSON representation using JCS. CBOR/COSE is a transport encoding
introduced at the wire layer; it does not alter the bytes over which
signatures are computed. Wire encoding must not silently redefine
cryptographic identity.

The JCS-based TBS is the same TBS used in Phase 1 and Phase 2. This
document does not change it. Introducing a CBOR-canonical TBS would
require a new domain tag and a new TBS definition; that is not
adopted in WIRE-FORMAT-0.2.

### 13.3 Hybrid Policy

- Default: AND. Every algorithm declared in the manifest's
  `required_algs` MUST be present and valid.
- Alternative: OR (explicit, declared by the relying party in its
  own policy; not default; not inferred).
- Downgrade: if any `required_algs` is missing, REJECT with
  E_SIGNATURE_DOWNGRADE.
- Silent fallback: forbidden.

## Section 14. Algorithm/Key Identity Binding (Identity Binding Invariant)

Per Commander order, DEFECT-017 is upgraded to an architectural
invariant:

    Algorithm + Key ID + Public Key + Fingerprint + TBS

is one interconnected system.

### 14.1 key_id derivation

| Algorithm | key_id |
|---|---|
| RS256 | sha256:hex(SHA-256(SPKI-DER(public_key))) |
| ML-DSA-65 | sha256:hex(SHA-256(raw_pk_1952_bytes)) |

GAP-9 (Phase 2): the two derivations use different encodings. This
is documented and does not affect the invariant: each algorithm's
key_id is a pure function of that algorithm's public key.

### 14.2 Binding check order

A verifier MUST perform, in this order:

1. Parse the certificate.
2. Extract `signatures[]`.
3. For each required algorithm:
   a. Check that a signature for this algorithm exists.
   b. Compute key_id from the provided public key.
   c. Compare with the signature object's key_id.
   d. If mismatch, REJECT E_SIGNATURE_KEY_MISMATCH before any
      cryptographic operation.
4. Only then verify the signature bytes.

Rationale: a valid signature is not sufficient evidence if the
identity of the key used does not match the expected identity for
the protocol. DEFECT-017 demonstrated this in Rust.

### 14.3 Public key representation

Public keys appear at three layers, with distinct roles:

| Layer | RS256 | ML-DSA-65 |
|---|---|---|
| Wire (COSE container) | COSE_Key with kty / alg / n | AKP (RFC 9964) with parameter -1 = pub (byte string of 1952 bytes) |
| Cryptographic material | SPKI DER bytes | raw FIPS 204 public key bytes (1952 bytes) |
| key_id derivation source | SPKI DER bytes | raw FIPS 204 public key bytes (1952 bytes) |

The COSE_Key / AKP representation is a **wire container**. The
cryptographic material is what determines the fingerprint and
key_id. A verifier MUST use the cryptographic material, not the
container, when computing key_id.

`COSE_Key` is a representation. `raw pk` is cryptographic material.
The two are not interchangeable, and COSE_Key is never hashed
directly to derive a key_id under this profile.

### 14.4 Fingerprint Source Invariant

The key_id and any related fingerprint are computed over exactly
defined public-key material:

- RS256: SPKI DER bytes.
- ML-DSA-65: raw FIPS 204 public key bytes (1952 bytes).

The fingerprint MUST NOT change if the wire container changes shape,
field order, or wrapping. In particular:

- Reordering the fields of a COSE_Key MUST NOT change key_id.
- Moving the raw public key between different CBOR envelopes MUST
  NOT change key_id.
- Adding or removing optional COSE_Key metadata MUST NOT change
  key_id.

This invariant is a direct consequence of DEFECT-017: identity is
not decorative metadata. It is part of the trust system.

## Section 15. Downgrade Resistance

1. A verifier with manifest declaring `required_algs = X` MUST reject
   any certificate that does not contain a valid signature for every
   element of X.
2. `E_SIGNATURE_DOWNGRADE` is emitted when a required algorithm is
   absent.
3. `E_SIGNATURE_UNKNOWN_ALG` is emitted when an algorithm appears in
   the certificate but is not in the registry.
4. `E_SIGNATURE_DUPLICATE_ALG` is emitted when the same algorithm
   appears twice.
5. Silent classical-only acceptance is forbidden when ML-DSA-65 is
   declared required.

## Section 16. Canonical Vectors

The conformance corpus MUST contain at least:

- 100 **valid** canonical vectors: certificate -> deterministic CBOR
  -> byte string. Each vector is generated **once the Rust reference
  implementation (3A.2) is available**. This specification defines
  the format; vectors are produced in 3A.2 and validated across
  Python and JS/WASM adapters in 3A.3 and 3A.4.

- Each valid vector is accompanied by its JSON form and its CBOR
  bytes as hex, plus the semantic digest (SHA-256 of the canonical
  CBOR). The TBS for each vector continues to be JCS-based
  (Section 13.2); the CBOR bytes are for wire representation only.

## Section 17. Negative Vectors

The conformance corpus MUST contain at least:

- 100 **malformed or noncanonical** vectors. Categories:
  - trailing bytes after top-level item
  - indefinite-length string/array/map
  - float encoding present
  - tag present
  - duplicate map key
  - overlong integer
  - map keys out of order
  - invalid UTF-8 in text string
  - missing required field
  - unknown critical field
  - wrong type for a known field
  - wrong dcp_version
  - unknown algorithm ID in signatures
  - wrong key_id format
  - wrong signature length
  - tampered claim_root
  - noncanonical bytes for a well-formed value
  - top-level array instead of map
  - null at a required position
  - oversized byte string declared but truncated

Each vector MUST produce a specific error code from Section 9.

## Section 18. Interoperability Requirements

One normative protocol, multiple implementation paths.

- **Rust**: reference implementation of the CBOR encoder and decoder.
- **Python**: adapter validated against the Rust reference.
- **JavaScript / WASM**: adapter validated against the Rust reference.

The three implementations MUST agree on:

- Positive convergence: for every valid vector, all three produce
  byte-identical CBOR.
- Negative convergence: for every malformed vector, all three produce
  the same error code.

Positive convergence alone is insufficient. Negative convergence is
the stronger requirement and is mandatory.

## Section 19. Fuzzing Requirements

Fuzzing is required from 3A.1 onward, not deferred to a later phase.

Required:
- structured mutation of valid vectors
- property tests: encode(decode(x)) == x for canonical inputs
- parser differential fuzzing: Python adapter vs Rust reference
  on the same random inputs
- corpus minimization when a divergence is found
- regression preservation: any divergence found becomes a permanent
  negative vector

The fuzzing harness is not part of the wire format spec. It is
documented in a separate operational document.

## Section 20. Exit Gate for 3A.1

3A.1 is closed when:

- This document is committed on vOmega.
- 14 items from Section 1 are all present and reviewed.
- Amendments from Commander order (Sections 5, 7, 8, 9, 11, 15) are
  incorporated.
- Commander approves the completion of WIRE-FORMAT-0.2.md.

**Status token upon closure:**

    GATE 1 / 3A.1 — CLOSED
    Specification approved and frozen for implementation.

No implementation may begin (no cbor.rs, no cbor.py, no cbor.mjs)
before this document is approved and this status token is emitted.

---

**End of WIRE-FORMAT-0.2**
