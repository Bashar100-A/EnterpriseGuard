# DECISION — CBOR Envelope Content Model (Stage 3A.5-B+SR2)

**Date:** 2026-10-07
**Stage:** 3A.5-B+SR2
**Decision ID:** DEC-3A.5-B+SR2-001
**Authority:** Commander

## Context

Reconnaissance for Stage 3A.5-B+ found that WIRE-FORMAT-0.2 §4.1
declares ten inner certificate fields as CBOR `map` while §7
requires all CBOR map keys to be unsigned integers, and §4 registers
no inner-key labels for those fields. Every existing DCP 2.0 / 2.1
certificate uses text keys inside those objects. The base document
cannot therefore describe how a real certificate is CBOR-encoded.

Three resolution paths were considered:

- **R1** — register inner integer labels for every nested key. A
  second label taxonomy, versioned and collision-prone. Rejected.
- **R3** — relax §7 to permit text keys in nested maps. Creates two
  map rules within one profile and re-opens DEFECT-021/027/028-class
  normalization hazards. Rejected.
- **R2** — carry nested objects as JCS byte strings. Adopted with
  one tightening (below).

## Decision

**R2+ is adopted.** Nested ADIE objects on the wire are carried as
**canonical JCS UTF-8 byte strings**, under deterministic CBOR
integer labels at the top level.

### Wire model

    Top-level CBOR map (integer-keyed, base §4.1)
      label 1   dcp_version  -> CBOR text
      label 2   claim_id     -> CBOR text
      labels 3-15 nested objects -> CBOR bstr (canonical JCS UTF-8)
      label 16  proofs       -> CBOR array  (native, retained)
      label 17  claim_root   -> CBOR bstr (32 raw bytes)
      label 18  signatures   -> CBOR array  (native, retained)

### Tightening over plain R2

- The JCS bytes are not "any JSON". They MUST satisfy A3 of
  AMENDMENT-2: valid UTF-8, single JSON object, canonical under
  RFC 8785, schema-conformant for the field, byte-stable under
  re-serialization. A verifier MUST reject on any failure.
- `binding` (label 12) is carried as JCS bytes like any other
  nested object. Its inner labels in base §4.3 remain normative for
  the JSON representation only.

### Preserved invariants

- `TBS = "ADIE-SIG-V2\0" || JCS(certificate_without_signatures)` is
  unchanged.
- Phase 1 / Phase 2 signatures remain valid.
- CBOR encoding does not redefine cryptographic identity.
- No COSE_Sign / COSE_Sign1 (Model B+, per AMENDMENT-1).
- COSE-native remains reserved for a future profile.

### Consequential requirement

A canonical vector corpus containing **real DCP 2.1 certificates**
(not toy scalars) MUST be produced before any B+ envelope
implementation can be declared conformant. See AMENDMENT-2 §A7.

## Status

ADOPTED. Frozen. Effective on commit of Stage 3A.5-B+SR2.
