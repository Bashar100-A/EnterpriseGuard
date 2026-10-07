# ADIE WIRE-FORMAT v0.2 — AMENDMENT 1

**Amendment ID:** WIRE-FORMAT-0.2-AMENDMENT-1
**Effective date:** 2026-10-07
**Status:** ADOPTED (frozen)
**Authority:** Commander decision, Stage 3A.5-SR
**Base document:** `spec/WIRE-FORMAT-0.2.md` (unchanged; still in force
except where this amendment explicitly overrides).
**Stage reference:** Phase 3, Gate 1, Stage 3A.5-SR

---

## A1. Purpose

Clarify the architectural model of the CBOR envelope used in DCP 2.1
and remove terminology that incorrectly implied compliance with
RFC 9052 `COSE_Sign` / `COSE_Sign1` signing structures.

This amendment is **additive**: it does not modify the base document
text; it overrides specific lines by explicit reference. The base
document remains available as the historical record.

## A2. Architectural Decision — Model B+

**ADIE DCP 2.1 adopts Model B+ — ADIE Native Hybrid CBOR Envelope.**

The CBOR envelope is a **deterministic CBOR encoding** of an
ADIE-native hybrid certificate. It is **NOT** a `COSE_Sign` and
**NOT** a `COSE_Sign1` object as defined in RFC 9052.

### A2.1 Chain of identity (unchanged from base §13)

    Semantic certificate (13 named fields + signatures array)
          ↓ JCS (RFC 8785)
    ADIE-SIG-V2\0 || JCS(certificate_without_signatures)   ← TBS
          ↓ RS256 + ML-DSA-65 (both sign the same TBS)
    signatures[]                                             ← ADIE-native signatures
          ↓ deterministic CBOR (RFC 8949 §4.2)
    ADIE Hybrid CBOR Envelope                                ← wire artifact

### A2.2 What the envelope is

- A deterministic CBOR encoding of the DCP 2.1 certificate.
- The signature objects inside `signatures[]` are **ADIE-native**:
  signatures computed by RS256 and ML-DSA-65 over the JCS-based TBS.
- The envelope is verifiable end-to-end against the TBS.

### A2.3 What the envelope is NOT

- **Not** `COSE_Sign` (RFC 9052 §4.1).
- **Not** `COSE_Sign1` (RFC 9052 §4.2).
- **Not** a signing structure per RFC 9052 `Sig_structure`.
- **Not** subject to RFC 9052 protected/unprotected header semantics.
- **No** compliance claim with any COSE signing profile or any
  composite-signature standard.

### A2.4 What remains COSE-referenced

- `COSE_Key` as the wire representation of the ML-DSA-65 public key
  (per RFC 9964 §3, AKP key type). This is a **key representation**,
  not a signing structure.
- Algorithm identifiers RS256 (`-257`) and ML-DSA-65 (`-49`) as
  registered IANA COSE Algorithms values. These are **number
  assignments**, reused for stability and cross-ecosystem legibility.
  The envelope itself does not perform COSE signing.

### A2.5 Why Model B+ (and not Model A) at this stage

Model A (COSE-native signing) would change the bytes over which
signatures are computed — from the JCS-based TBS to a COSE
`Sig_structure`. That is a change in cryptographic identity: every
signature produced under Phase 1 and Phase 2 would be invalidated,
and every published vector would require re-issuance.

Model B+ preserves the cryptographic identity chain unchanged
(Phase 1 → Phase 2 → DCP 2.1), and adds a deterministic binary
envelope above it. This protects historical verification artifacts.

A future COSE-native profile is **reserved** in §A6.

## A3. Normative Overrides to WIRE-FORMAT-0.2

This amendment overrides the following items by explicit reference.
All other sections of the base document remain in force, unchanged.

### A3.1 Base §10 title

**Base text:** `## Section 10. COSE Structure (RFC 9052)`
**Overridden to:** `## Section 10. ADIE Hybrid Signature Envelope`

### A3.2 Base §10, lines 274–276

**Base text:** "The certificate's signatures array uses COSE_Sign1
semantics for …"
**Overridden to:** "The certificate's signatures array uses **ADIE
Hybrid Signature Envelope semantics** for its CBOR encoding. It is
NOT a COSE_Sign1 object."

### A3.3 Base §10, line 289

**Base text:** "The protected header concept from COSE is deferred
to a future version of this document."
**Overridden to:** "COSE protected/unprotected header semantics do
**not** apply to this envelope. Profile-level metadata binding is
handled by the ADIE field registry (§4) and the identity binding
invariant (§14). COSE-native protected headers are reserved for a
future wire-profile/version (§A6)."

### A3.4 Base §3, line 200

**Base text:** "integer labels for core COSE_Key and COSE_Sign1
fields."
**Overridden to:** "integer labels for core ADIE Hybrid Signature
Envelope fields (consistent with the integer-keyed wire model
established in §7)."

### A3.5 Base §13.2, lines 351–353

**Base text:** "CBOR/COSE is a transport encoding introduced at the
wire layer; it does not alter the bytes over which signatures are
computed."
**Overridden to:** "The deterministic CBOR envelope is a wire
encoding introduced at the transport layer. It does not alter the
bytes over which signatures are computed (the JCS-based TBS)."

### A3.6 Every remaining "COSE_Sign1 semantics" phrase in §10

**Overridden to:** "ADIE Hybrid Signature Envelope semantics".

## A4. TBS — Explicitly Unchanged

    TBS = "ADIE-SIG-V2\0" || JCS(certificate_without_signatures)

- The 12-byte domain tag `ADIE-SIG-V2\0` is unchanged.
- JCS (RFC 8785) canonicalization is unchanged.
- The same TBS is signed by every algorithm present in `signatures[]`.
- **No CBOR-canonical TBS is adopted in this amendment.**

Phase 1 and Phase 2 signatures remain valid against this TBS.

## A5. Signatures — Explicitly Unchanged

- `signatures[]` is an array of ADIE signature objects.
- Each object carries `alg`, `kid`, `value` (raw bytes, not base64).
- RS256: PKCS#1 v1.5 + SHA-256, 256-byte signature.
- ML-DSA-65: FIPS 204 deterministic, 3309-byte signature.
- Both sign the same TBS (§A4).
- Hybrid policy: VALID ⟺ RS256 VALID **AND** ML-DSA-65 VALID.
  (Unchanged from base §13.3.)

## A6. Future COSE-Native Profile — Reserved

A future wire profile (working name: **WIRE-FORMAT-0.3**) MAY adopt
a standards-interoperable COSE-native signing structure, at which
point:

- Signatures would be computed over RFC 9052 `Sig_structure`, NOT
  over the JCS-based TBS.
- **A new domain tag** (e.g., `ADIE-SIG-V3\0`) would be required.
  The current `ADIE-SIG-V2\0` MUST NOT be reused under a different
  signing context.
- `COSE_Sign` (multi-signature container per RFC 9052 §4.1) would
  replace the ADIE-envelope's signing semantics.
- COSE protected headers would carry algorithm/profile identity.
- RFC 9964 would then govern the ML-DSA-65 COSE representation as
  the authoritative standard, including the `AKP` key type, `pub`
  parameter, and `-49` algorithm identifier.

**Migration boundary:**

- Documents signed under WIRE-FORMAT-0.2 (Model B+) remain
  verifiable under their own frozen rules.
- Documents signed under WIRE-FORMAT-0.3 are distinguished by the
  new domain tag.
- **No cross-context signature reuse is permitted.** A signature
  valid under `ADIE-SIG-V2\0` (JCS-TBS) MUST NOT be accepted as
  valid under any COSE-native profile, and vice versa.

**This amendment does NOT implement the future profile.** It only
declares its reserved status and the migration boundary.

## A7. Non-Changes — What Remains Frozen from WIRE-FORMAT-0.2

The following sections of the base document remain in force,
unchanged, and are reaffirmed by this amendment:

- §4  Field Registry
- §5  Critical vs Non-Critical Field Policy
- §6  Versioning Rules (`dcp_version` = "2.1")
- §7  ADIE CBOR Data Model
- §8  ADIE Deterministic CBOR Profile
- §9  Malformed-Input Rejection Matrix
- §11 ML-DSA-65 Mapping (RFC 9964)
- §12 RS256 Mapping (RFC 9052)
- §13.1 The Hybrid Signature
- §13.2 TBS (as clarified by §A4 above)
- §13.3 Hybrid Policy
- §14 Identity Binding Invariant
- §15 Downgrade Resistance
- §16 Canonical Vectors
- §17 Negative Vectors
- §18 Interoperability Requirements
- §19 Fuzzing Requirements
- §20 Exit Gate for 3A.1

## A8. Status

This amendment is **ADOPTED and FROZEN** as part of the
WIRE-FORMAT-0.2 specification corpus. Together with the base
document, it constitutes the normative reference for DCP 2.1.

Any future change to §A2, §A4, §A5, or §A6 requires a new amendment
or a new wire-profile version. Silent modification is prohibited.

---

*End of WIRE-FORMAT-0.2-AMENDMENT-1.*
