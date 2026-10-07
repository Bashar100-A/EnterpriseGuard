# ADIE WIRE-FORMAT v0.2 — AMENDMENT 2

**Amendment ID:** WIRE-FORMAT-0.2-AMENDMENT-2
**Effective date:** 2026-10-07
**Status:** ADOPTED (frozen)
**Authority:** Commander decision, Stage 3A.5-B+SR2
**Base document:** `spec/WIRE-FORMAT-0.2.md` (unchanged)
**Prior amendment:** `spec/WIRE-FORMAT-0.2-AMENDMENT-1.md`
**Stage reference:** Phase 3, Gate 1, Stage 3A.5-B+SR2

---

## A1. Purpose

Resolve a normative gap in the base document: §4.1 declares ten
top-level certificate fields (`issuer`, `subject`, `request`,
`context`, `policy`, `model`, `data`, `runtime`, `output`, `binding`,
`temporal`, `evidence`, `authoring`) to be of CBOR type `map`, and
§7 requires that every CBOR map in the ADIE profile use **unsigned
integer** keys. §4 does not, however, register integer labels for
the inner keys of those maps.

Every existing DCP 2.0 / 2.1 certificate uses **text** keys in those
inner maps (see `protocol/pilot/issue_cli.py` and
`protocol/hybrid/certificate.py`). The base document therefore
cannot describe how a real certificate is encoded as CBOR without
either (a) inventing a large inner-key registry, (b) permitting
text keys in violation of §7, or (c) violating §7 by other means.

This amendment adopts option R2+ (see DECISION-0.4): the outer DCP
envelope is deterministic, integer-keyed CBOR; the inner ADIE
objects are carried as **canonical JCS UTF-8 byte strings**.

## A2. Wire Model (Normative)

The DCP 2.1 wire artifact is a deterministic CBOR map with the
top-level labels registered in base §4.1. The content carried under
each label is:

| Label | Field         | Content on the wire                                                        |
|-------|---------------|----------------------------------------------------------------------------|
| 1     | dcp_version   | CBOR **text** (`"2.1"`).                                                   |
| 2     | claim_id      | CBOR **text**.                                                             |
| 3     | issuer        | CBOR **byte string** containing canonical JCS UTF-8 bytes.                 |
| 4     | subject       | CBOR **byte string** containing canonical JCS UTF-8 bytes.                 |
| 5     | request       | CBOR **byte string** containing canonical JCS UTF-8 bytes.                 |
| 6     | context       | CBOR **byte string** containing canonical JCS UTF-8 bytes.                 |
| 7     | policy        | CBOR **byte string** containing canonical JCS UTF-8 bytes.                 |
| 8     | model         | CBOR **byte string** containing canonical JCS UTF-8 bytes.                 |
| 9     | data          | CBOR **byte string** containing canonical JCS UTF-8 bytes.                 |
| 10    | runtime       | CBOR **byte string** containing canonical JCS UTF-8 bytes.                 |
| 11    | output        | CBOR **byte string** containing canonical JCS UTF-8 bytes.                 |
| 12    | binding       | CBOR **byte string** containing canonical JCS UTF-8 bytes.                 |
| 13    | temporal      | CBOR **byte string** containing canonical JCS UTF-8 bytes.                 |
| 14    | evidence      | CBOR **byte string** containing canonical JCS UTF-8 bytes.                 |
| 15    | authoring     | CBOR **byte string** containing canonical JCS UTF-8 bytes.                 |
| 16    | proofs        | CBOR **array** (retained native; see A4).                                  |
| 17    | claim_root    | CBOR **byte string** of exactly 32 raw bytes (SHA-256 digest).             |
| 18    | signatures    | CBOR **array** of signature objects (retained native; see A4).             |

**Default rule:** every nested ADIE object is represented as canonical
JCS UTF-8 bytes, **including** `binding`. A field is retained as a
native CBOR structure only if this amendment (or a later amendment)
explicitly says so.

## A3. Content Profile of JCS Byte Strings

Every JCS byte string admitted on the wire has an explicit
content profile:

1. It MUST be a valid UTF-8 byte sequence.
2. It MUST be a single JSON value of type **object** (a JSON map).
3. It MUST be canonical per RFC 8785 (JCS): sorted keys, minimal
   escaping, I-JSON numeric range, no trailing whitespace, UTF-8
   without BOM.
4. It MUST parse without errors into a JSON object that fits the
   existing DCP 2.1 semantic schema for the corresponding field
   (`subject`, `binding`, etc.).
5. It MUST re-serialize byte-identically under the same JCS
   canonicalization.

A verifier MUST reject any byte string that fails any of (1)–(5).

**Non-normative:** rules (1)–(5) mean the wire is not a second
serialization language. The DCP semantic model remains JSON+JCS;
CBOR carries it.

## A4. Fields Retained as Native CBOR (Explicit Exceptions)

The default in A2 is JCS bytes. The following fields are **retained
as native CBOR structures** by explicit exception:

### A4.1 `proofs` (label 16) — CBOR array

- Empty array in every DCP 2.1 certificate produced today.
- Semantics for non-empty arrays are not defined by WIRE-FORMAT-0.2
  and remain reserved for a future amendment.
- Encoders MUST emit an array; decoders MUST accept an array.

### A4.2 `claim_root` (label 17) — CBOR byte string (32 raw bytes)

- The semantic value in the JSON representation is
  `"sha256:<64-hex>"`.
- On the wire, the digest is carried as a raw 32-byte string.
- A future amendment MAY add an alternative integer encoding; this
  amendment fixes the raw-bytes form.

### A4.3 `signatures` (label 18) — CBOR array

- Each element is a CBOR map with the three inner labels defined in
  base §4.2 (`1` = `alg`, `2` = `key_id`, `3` = `value`).
- `alg` and `key_id` are CBOR text.
- `value` is CBOR bytes containing the raw signature
  (RS256: 256 bytes; ML-DSA-65: 3309 bytes).
- The base JSON representation uses `"base64:..."`; the wire uses
  raw bytes.

## A5. TBS — Explicitly Unchanged

    TBS = "ADIE-SIG-V2\0" || JCS(certificate_without_signatures)

- The 12-byte domain tag `ADIE-SIG-V2\0` is unchanged.
- The certificate body is the DCP 2.1 JSON object.
- JCS canonicalization is unchanged.
- Each algorithm in `signatures[]` signs the same TBS.
- Phase 1 and Phase 2 signatures remain valid.
- No CBOR-canonical TBS is adopted.

**CBOR encoding must not redefine cryptographic identity.** The JCS
byte strings carried inside the CBOR envelope MUST produce, after
reconstruction, the same canonical certificate JSON that JCS+TBS
consumes.

## A6. Verification Pipeline (Normative)

The verifier MUST execute, in order:

1. Parse the CBOR envelope under the deterministic rules of §8.
2. Reject any construct forbidden by §7 (tags, floats, indefinite
   length, duplicate keys, trailing bytes, non-shortest integers,
   text keys, byte keys, composite keys).
3. Reject any non-B-authorized top-level label.
4. For each label 3–15: extract the byte string, and apply A3
   checks (UTF-8, JSON object, JCS-canonical, schema-conformant).
5. For each label 16–18: apply the A4 rules.
6. Reassemble the DCP 2.1 JSON certificate object.
7. Recompute TBS via A5.
8. Verify RS256 and ML-DSA-65 signatures against the TBS.
9. Enforce the ADIE hybrid policy: **RS256 VALID AND ML-DSA-65
   VALID**. A failure of either MUST produce rejection.
10. If all checks pass, accept.

**A failure at any step MUST produce a deterministic ADIE rejection
code (typed, not generic boolean).**

## A7. Canonical Vectors — Normative Requirement

A future canonical vector corpus is REQUIRED before any B+ envelope
implementation may be declared conformant. That corpus MUST include
**real DCP 2.1 certificates**, not only toy scalar values.

Each canonical vector MUST include:

- a certificate with all thirteen named semantic fields populated
  (`issuer`, `subject`, `request`, `context`, `policy`, `model`,
  `data`, `runtime`, `output`, `binding`, `temporal`, `evidence`,
  `authoring`), plus `claim_id`, `dcp_version`, `claim_root`,
  `proofs`, `signatures`;
- the canonical JSON form (JCS bytes of each nested object);
- the deterministic CBOR envelope (wire bytes);
- the TBS bytes;
- the expected RS256 and ML-DSA-65 signatures;
- the expected acceptance result.

The corpus MUST also include negative vectors covering, at minimum:
non-canonical JCS, non-UTF-8 bytes, wrong JSON type in a byte string,
duplicate top-level label, non-shortest integer, tag, float,
indefinite-length, trailing bytes, non-B top-level label, missing
required field, tampered signature bytes, tampered JCS content.

**Vectors that only exercise the CBOR codec do not satisfy this
requirement.**

## A8. Non-Changes — What Remains Frozen

- Base §4.1 top-level label registry.
- Base §4.2 signature-object labels (1, 2, 3).
- Base §4.3 binding inner labels (1–6). These remain normative **for
  the JSON representation of binding**; the wire carries binding as
  JCS bytes per A2.
- Base §5, §6, §13.1, §13.2, §13.3, §14, §15, §18, §19, §20.
- AMENDMENT-1 (Model B+; no COSE_Sign / COSE_Sign1).
- Phase 1 / Phase 2 cryptographic identity.
- `dcp_version` remains `"2.1"`.

## A9. Reserved for the Future

- A COSE-native signing structure is reserved for a future wire
  profile (working name WIRE-FORMAT-0.3), per AMENDMENT-1 §A6.
- A canonical inner-key registry (the R1 approach) is explicitly
  **not** adopted. It may only be introduced in a future wire
  profile with its own version.
- `proofs` non-empty semantics remain undefined.

## A10. Status

This amendment is ADOPTED and FROZEN as part of the WIRE-FORMAT-0.2
corpus. Any change to §A2, §A3, §A5, §A7, or §A9 requires a new
amendment or a new wire profile version. Silent modification is
prohibited.

---

*End of WIRE-FORMAT-0.2-AMENDMENT-2.*
