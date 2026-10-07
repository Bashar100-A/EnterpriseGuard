# DECISION — COSE Architectural Model (Stage 3A.5-SR)

**Date:** 2026-10-07
**Stage:** 3A.5-SR
**Decision ID:** DEC-3A.5-SR-001
**Authority:** Commander

## Context

During reconnaissance for Stage 3A.5 (COSE + Hybrid Wire Integration),
a normative contradiction was identified between:

- `spec/WIRE-FORMAT-0.2.md` §13.2, which mandates a JCS-based TBS
  and explicitly states that CBOR/COSE is a transport encoding that
  does not alter the bytes over which signatures are computed;
- the initial Commander Order for 3A.5 §3, which suggested Model A —
  COSE signing where signatures are computed over the COSE
  `Sig_structure`.

Additionally, WIRE-FORMAT-0.2 §10 lines 274–289 uses `COSE_Sign1
semantics` terminology, while Commander Order §2 mandates avoiding
COSE_Sign1 in favor of multi-signature COSE_Sign. This produced a
terminological mismatch independent of the cryptographic question.

## Decision

**Architectural Model B+ is adopted.**

- **TBS unchanged:** `ADIE-SIG-V2\0 || JCS(certificate_without_signatures)`.
- **Signatures unchanged:** ADIE-native RS256 + ML-DSA-65 over the
  JCS-based TBS.
- **Wire artifact:** deterministic CBOR encoding of the ADIE-native
  hybrid certificate. It is NOT a `COSE_Sign` or `COSE_Sign1` object.
- **Terminology correction:** the base document's `COSE_Sign1
  semantics` phrasing and `COSE Structure` section title are
  overridden by explicit reference in
  `spec/WIRE-FORMAT-0.2-AMENDMENT-1.md`.
- **COSE-native signing (Model A) reserved** for a future
  wire-profile version (working name WIRE-FORMAT-0.3), with a new
  domain tag (`ADIE-SIG-V3\0`) and a standards-interoperable
  `Sig_structure` flow.

## Rationale

1. **Historical integrity:** Phase 1 and Phase 2 signatures remain
   valid. Model A would invalidate them.
2. **Cryptographic identity:** the current TBS is the ADIE chain of
   identity. Changing it in-place is a protocol break, not a
   refinement.
3. **Standards honesty:** claiming COSE signing while signing the
   JCS-based TBS would be a semantic falsehood. B+ avoids the claim.
4. **RFC 9052 respects application authority:** RFC 9052 §4.1 does
   not force the multi-signature interpretation, and RFC 9964 covers
   the ML-DSA-65 key representation and algorithm ID without
   requiring the wire container to be COSE_Sign.

## Scope of changes

- New file: `spec/WIRE-FORMAT-0.2-AMENDMENT-1.md`.
- No modification to `spec/WIRE-FORMAT-0.2.md`.
- No code change in this decision (Stage 3A.5-SR is spec-only).
- Code implementing B+ (deterministic CBOR envelope) is reserved for
  Stage 3A.5-B+ (next stage, after SR closure).

## Migration boundary

Documents under WIRE-FORMAT-0.2 (B+) and WIRE-FORMAT-0.3 (COSE-native,
future) are distinguished by their TBS domain tag
(`ADIE-SIG-V2\0` vs `ADIE-SIG-V3\0`). Cross-context signature reuse
is prohibited. Both profiles remain verifiable under their own frozen
rules.

## Status

ADOPTED. Frozen. Effective on commit of Stage 3A.5-SR.
