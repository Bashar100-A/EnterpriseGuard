# ADIE vΩ — Defects Log

**Purpose:** Record every defect discovered by a test suite.
**Rule (from this commit onward):** Every defect found by a test MUST be
logged here with root cause and fix. No silent corrections.

**Format:**DEFECT-NNN
date:
commit_found:
commit_fixed:
suite:
test_id:
test_name:
category: code | test | spec
root_cause:
fix:
lesson:
text


---

## DEFECT-001 — M19 was a duplicate of M06

date: 2026-10-06
commit_found: 99c8376
commit_fixed: a453556
suite: tests/vomega/meta/run_all.py
test_id: M19
test_name: Version Alias Collision
category: test
root_cause: Test registered the same rewrite rule with the same digest
twice. Registry.register_rewrite is idempotent for identical
digests by design, so no E-META-14 was raised. The test failed
to differentiate itself from M06 (Rewrite Rule Shadowing).
fix: Rewrote M19 to test three no-aliasing properties:
(a) distinct version strings stored as distinct entries,
(b) lookup does NOT cross-alias,
(c) same string + different digest → E-META-14.
lesson: A test that passes the same code path as another test does not
extend coverage. Each M-vector must exercise a distinct failure
mode. Review test intent, not test name.
text


---

## DEFECT-002 — A25: EQ did not enforce type check

date: 2026-10-06
commit_found: 5589bb2
commit_fixed: d39fb02
suite: tests/vomega/acl/run_all.py
test_id: A25
test_name: EQ int/str → E200_TYPE_MISMATCH
category: code
root_cause: In protocol/acl/eval.py, the EQ/NEQ branch returned
PASS/FAIL before the type-check block ran. Consequently
EQ(INT(5), STR("x")) returned FAIL instead of raising
E200_TYPE_MISMATCH, violating ACL-0.1 §2.2 (fail-closed on
type mismatch).
fix: Moved type check to the top of the EQ/NEQ/LT/... branch.
LT/LTE/GT/GTE additionally reject Bool and non-(int,str).
lesson: "Fail-closed" only holds if the check runs before any return.
Every comparison branch must validate types before producing
a result. Order of checks is a security property.
text


---

## Metrics

| Metric | Value |
|---|---|
| Total defects | 2 |
| Category: test | 1 |
| Category: code | 1 |
| Category: spec | 0 |
| Total tests at first defect | 40 |
| Total tests at second defect | 40 (ACL) |
| Total tests now | 143 |

---

**End of DEFECTS-LOG**

---


---

**End of DEFECTS-LOG**

---

## DEFECT-003 — Block B test 4 over-specified code

date: 2026-10-06
commit_found: <TBD>
commit_fixed: <TBD>
suite: Block B exploratory test
test_id: manual-4
test_name: authoring tampered → E-META-20
category: test
root_cause: ClaimRoot covers the `authoring` field (13 named fields). Tampering with authoring.canonical_ast_digest changes ClaimRoot, so DCP 2.0 pipeline raises E_CLAIM_ROOT_MISMATCH before the pilot-level authoring check runs. My expectation of E-META-20 was too specific.
fix: Accept either E_CLAIM_ROOT_MISMATCH or E-META-20 as valid rejection in the pilot conformance vectors. Document the ordering guarantee: DCP 2.0 claim_root runs before authoring-level checks.
lesson: Defense-in-depth means a single field tampering may be caught at multiple layers. Test expectations should be written against the failure SET, not a single code, unless the ordering is normative.

---

## DEFECT-004 — JS verify.mjs: ClaimRoot field mismatch + message format

date: 2026-10-06
commit_found: 5fe41ab
commit_fixed: <TBD>
suite: Block C differential
category: code
root_cause: (1) JS FIELD_ORDER had 13 fields; Python uses 14 (adds "proof-set" as always-ABSENT). 13+3 padding != 14+2 padding; Merkle roots diverged. (2) Error messages did not mirror Python str(VerifyError)="code: msg"[:120] format. (3) BindingError requires two-stage slicing [code: msg][:80] -> [code: sliced][:120].
fix: (1) FIELD_NAMES_13 + FIELD_ORDER_14; computeClaimRoot iterates all 14. (2) dcpMsg/bindingMsg helpers replicate Python slicing. (3) Rewrote verify.mjs.
lesson: Cross-language canonical byte-equality requires matching every detail: field order, padding strategy, error message format, and slicing semantics. "Byte-identical" is not just JSON.

---

## Schema addition (effective from DEFECT-006)

Future defect entries MUST include three additional fields:

```
language_pair:       py/js | py/rust | py/ts | single
failure_mode:        structural | message | crypto | timing | semantic
invariant_at_risk:   I13 | I14 | ... | I34 | none
```

Rationale: the pilot layer exposed that cross-language byte-equality failures split into three distinct classes (structural, message, crypto). Tracking them explicitly prevents future regression.

---

## DEFECT-006 — Rust verifier binding error codes use hyphens

date: 2026-10-06
commit_found: f8fb6e5
commit_fixed: <TBD>
suite: tests/vomega/rust/run_all.py
test_id: P06
test_name: wrong audience
test_phase: RUST-VERIFY
category: code
language_pair: py/rust
failure_mode: message
invariant_at_risk: I13 (cross-impl determinism)
root_cause: verifier.rs used E-BINDING-AUDIENCE-MISMATCH (hyphens) while Python verify_cli.py uses E_BINDING_AUDIENCE_MISMATCH (underscores). Cross-language byte-equality broke on error-code format, not on decision logic.
fix: Replaced all E-BINDING-* strings with E_BINDING_* in verifier.rs to match Python verify_pipeline.py and verify_cli.py.
lesson: The new DEFECT schema (language_pair/failure_mode/invariant_at_risk) was justified by this defect. Byte-equality is fragile at every layer including error identifiers. A single hyphen vs underscore = a real divergence. Tests caught it; the previous commit message did NOT (claimed 435/435 when actual was 434/435).

---

## DEFECT-007 — Premature GAP-5 commitment based on partial information

date: 2026-10-06
commit_found: 56717dc
commit_fixed: <TBD>
suite: n/a (process)
test_id: n/a
test_phase: Phase 2 setup
category: process
language_pair: n/a
failure_mode: semantic
invariant_at_risk: I34 (identifier immutability), I13 (determinism of records)
root_cause: After the first cargo fetch failed (Cargo 1.75 + edition2024), GAP-5 was committed as a permanent deferral without first attempting the alternative (rustup official). The second attempt succeeded immediately, invalidating the committed text.
fix: GAP-5 replaced by GAP-5-CORRECTED. DEFECT-007 logged. The lesson is that "attempt failed" does not equal "attempt impossible" — record the failed attempt as a note, not a permanent gap, until the alternative path is also tried.
lesson: In protocol documentation, "deferred" is a claim about the future. It requires exhausting known paths first. Partial-information commitments pollute the spec and require a correction cycle. Rule going forward: any GAP-N entry must include a "paths attempted" list.

---

## DEFECT-008 — Repeated GAP-N before exhausting paths

date: 2026-10-06
commit_found: 56f9bf7 (unpushed)
commit_fixed: <TBD>
suite: n/a (process)
category: process
language_pair: n/a
failure_mode: semantic
invariant_at_risk: I34
root_cause: Same as DEFECT-007, second occurrence. GAP-6 was written assuming nvm was the only path, while NodeSource was simultaneously attempted and succeeded.
fix: GAP-6-RETRACTED. DEFECT-008 logged.
lesson: This is a pattern, not an isolated incident. Going forward, GAP-N entries require a MANDATORY pre-condition: the author must run a "paths-tried" checklist and include raw evidence (commands + exit codes) for EVERY path before committing a "deferred" claim. A GAP-N without such evidence is treated as incomplete.

---

## DEFECT-009 — Placeholder contamination in spec §12.3

date: 2026-10-06
commit_found: <uncommitted>
commit_fixed: <TBD>
suite: n/a (documentation)
category: process
language_pair: n/a
failure_mode: semantic
invariant_at_risk: I34 (identifier immutability)
root_cause: A Python script was provided to update spec/HYBRID-CRYPTO-0.1.md with three hash values. The script included literal placeholders (INTEGRITY, SHA_MLDSA, SHA_PKG) with instructions to substitute them before running. The instruction was not followed, so the placeholders were written to the spec verbatim, making it look complete when it was not.
fix: Replaced placeholders by reading values directly from the filesystem inside the script. No manual substitution required.
lesson: Templates with placeholders are a failure mode. Any script that writes to a normative document MUST resolve all values programmatically. Manual substitution is not permitted for spec files. This is a stricter rule than DEFECT-007 and DEFECT-008 — the defect class is different (placeholders shipped, not partial-information commits).

---

## DEFECT-010 — pqcrypto cannot participate in deterministic ML-DSA testing

date: 2026-10-06
commit_found: <uncommitted>
commit_fixed: <TBD>
suite: n/a (API capability)
category: process
language_pair: n/a
failure_mode: structural
invariant_at_risk: none (not a protocol violation; a testing-scope reduction)
root_cause: pqcrypto 1.0.0 (C wrapper over PQClean) exposes sign(sk, msg, context=None, hash_algorithm=None) and keygen() with no arguments. There is no way to inject a fixed ξ seed for FIPS 204 KeyGen_internal, nor to force deterministic signing. Cross-language byte-equality tests (spec HYBRID-CRYPTO-0.1 sec 10, sec 11) require both. Measured: sig_a != sig_b for two identical calls with the same sk and msg.
fix: Reclassified pqcrypto as VERIFY-ONLY for Phase 2. Python production sign path is dilithium-py 1.4.0 (deterministic=True, key_derive(seed)). Python verify path runs BOTH pqcrypto and dilithium-py, and requires agreement. This preserves the independent cross-check where it matters most (verification).
lesson: A "vetted library" claim must be qualified by its API capabilities, not just its cryptographic primitive. pqcrypto implements ML-DSA correctly for the sign/verify operations it exposes, but does not expose the FIPS 204 deterministic interfaces required for reproducible testing. This is not a cryptographic weakness; it is a testing and reproducibility constraint.

---

## DEFECT-011 — mldsa wrapper assumed ctx=b""

date: 2026-10-06
commit_found: 157fa3e
commit_fixed: <TBD>
suite: n/a (spec-vs-KAT scope)
category: code
language_pair: n/a
failure_mode: structural
invariant_at_risk: none (discovered while preparing Block D.2 KAT)
root_cause: The ML-DSA wrapper (mldsa.rs) hard-coded SIGNING_CONTEXT = b"". This was correct for MLDSA-XLANG-001 (which used ctx=b"") but does not cover the ACVP KAT vectors, which carry variable-length context strings (e.g. 17 bytes, 20 bytes). The mismatch was discovered by inspecting the ACVP JSON structure before writing the KAT runner, not by a failing test.
fix: Extended mldsa.rs to expose sign_deterministic_ctx(seed, msg, ctx) and verify_with_ctx(pk, msg, ctx, sig). Legacy sign_deterministic(tbs) and verify() now delegate with ctx=b"". The CLI adie-mldsa accepts ctx_hex (optional, defaults to empty). MLDSA-XLANG-001 regression check passes with ctx=b"".
lesson: A wrapper that "works" for one test vector can still be incomplete for the general case. When preparing to add standard test vectors, read their structure first and confirm the wrapper covers every field. This is DEFECT-009 applied to code instead of docs: do not assume the first passing input defines the contract.

---

## DEFECT-012 — RustCrypto decode was stricter than FIPS 204.Verify semantics

date: 2026-10-06
commit_found: uncommitted (Block D.2b Rust run)
commit_fixed: <TBD>
suite: tests/vomega/mldsa/kat/run_rust.py
test_id: sigver tcId=32,38,41
test_phase: Phase 2 D.2b
category: code
language_pair: py/rust
failure_mode: structural
invariant_at_risk: none (API shape, not protocol)
root_cause: RustCrypto ml-dsa 0.1.1 Signature::decode returns Option::None for signatures whose hint field is out of range (per FIPS 204 sigDecode). The wrapper mapped this None to Err("signature decode failed"). ACVP expects such inputs to produce testPassed=false, not an error. Python dilithium-py returns False directly. Divergence: Err vs Ok(false).
fix: mldsa.rs verify_with_ctx maps decode failures to Ok(false), matching FIPS 204 ML-DSA.Verify which rejects invalid signatures. Wrong-length signature bytes also return Ok(false) now (they cannot be valid by construction).
lesson: "Signature decode" and "signature verification" are both rejections under FIPS 204; only the input format is what differs. Splitting them into Err vs Ok(false) in a wrapper breaks cross-language byte-equality on the decision (which ACVP tests). API ergonomics should follow the spec, not vice versa.

---

## GAP-8 — Rust ML-DSA sigGen not covered by ACVP KAT

date: 2026-10-06
paths tried:
  1. sign_deterministic(seed, msg, ctx) — requires Seed(32B)
  2. ACVP sigGen provides sk (4032B), not seed. Seed cannot be recovered
     from sk (it is derived from seed by an irreversible expansion).
  3. SigningKey::from_expanded(enc) — takes ExpandedSigningKeyBytes, but
     ACVP sk format is FIPS 204 sk encoding, not the RustCrypto
     internal expanded format.
  4. ml-dsa 0.1.1 does not expose a public API to construct SigningKey
     from raw FIPS 204 sk bytes without round-tripping through seed.
consequence:
  - Rust covers: keygen (25/25) + sigver (15/15).
  - Rust does not cover: sigGen (0/15).
  - Cross-language coverage for sigGen: Python (15/15) + JS (pending).
  - This is a wrapper-coverage limit, not a cryptographic gap: Rust
    verifies every ACVP sigVer vector correctly and its pk matches
    every ACVP keygen vector exactly.
resolution path (Phase 2.5):
  - Inspect RustCrypto for a hypothetical from_encoded API in later
    versions, OR
  - Build a thin adapter that reconstitutes the internal key from the
    standard sk format (if FIPS 204 defines such a path).
  - MLDSA-XLANG-001 already proves byte-equality of sigGen across the
    three languages for the seed-based path.
not retracted: RISK-2.1 (ml-dsa pre-1.0, unaudited).

---

## DEFECT-013 — spec claimed 13-byte domain tag; actual is 11 chars + NUL = 12 bytes

date: 2026-10-07
commit_found: f05af3d
commit_fixed: <TBD>
suite: n/a (spec text)
category: spec
language_pair: n/a
failure_mode: semantic
invariant_at_risk: none (implementation was always 12 bytes; only doc was wrong)
root_cause: spec/HYBRID-CRYPTO-0.1.md §5 wrote ""ADIE-SIG-V2\0" is an ASCII domain separation tag (13 bytes + NUL)". The string ""ADIE-SIG-V2"" has 11 characters (A D I E - S I G - V 2), not 13. With NUL, the tag is 12 bytes. Hex "41 44 49 45 2D 53 49 47 2D 56 32 00" (also listed in the same sentence) was always correct.
fix: spec corrected to "11 ASCII chars + NUL = 12 bytes". Code (protocol/hybrid/tbs.py) has always used 12 bytes with an explicit assertion.
lesson: Spec docs should not describe byte counts in prose next to hex literals. The hex is the source of truth; the prose is commentary and can drift. This is the second spec-vs-implementation mismatch (DEFECT-009 was placeholder text, this is character count). Both were caught before they affected real byte output.

---

## GAP-9 — ML-DSA-65 key_id uses raw pk bytes, not SPKI DER

date: 2026-10-07
paths tried:
  1. Spec §6 originally stated "SPKI DER with OID id-ml-dsa-65 (RFC 9964)".
  2. SPKI encoding requires SEQUENCE { SEQUENCE { OID id-ml-dsa-65, NULL }, BIT STRING pk }.
  3. Implementing this requires DER OID encoding, BIT STRING wrapping,
     and length prefix computation, all of which need independent testing.
  4. Cross-language byte-equality of SPKI-wrapped ML-DSA-65 pk has not
     been verified.
consequence:
  - ML-DSA-65 key_id = sha256(SHA-256(pk_raw)) where pk_raw is 1952 bytes.
  - RS256 key_id = sha256(SHA-256(SPKI_DER)).
  - The two key_id derivations use different encodings.
  - Fine for internal consistency but blocks cross-algorithm key_id comparison.
resolution path (Phase 2.5):
  - Add SPKI wrapper for ML-DSA-65 with OID DER (id-ml-dsa-65 from RFC 9964).
  - Cross-verify SPKI bytes across Python/JS/Rust.
  - Bump to key_id scheme v2 (not v1, to avoid identifier redefinition).
not retracted: RISK-2.1.


---

## DEFECT-014 — Test count conflation across phases

date: 2026-10-07
commit_found: 6f1152b
commit_fixed: <TBD>
suite: n/a (process)
test_id: n/a
test_phase: Phase 2 closure
category: process
language_pair: n/a
failure_mode: semantic
invariant_at_risk: I34 (identifier immutability — numbers are identifiers)
root_cause: Multiple numbers were claimed based on ad-hoc summation:
  (a) "648 Phase 1 regression" — actually 633. Off by 15.
  (b) "723/723 total" — sum of 648 + 75. Neither base number was correct.
  (c) "75 Phase 2" — actually 59 Python + 11 JS = 70, with 5 TBS-differential
      not being a standalone suite (they are inside test_tbs.py).
  The numbers were asserted in commit messages (fd5d98d, 6f1152b) and in
  PHASE-2-CLOSURE.md before being measured by a tool.
fix: Created tests/account.py as the sole authority for test counts. It
  runs every suite as a subprocess and reads the TOTAL line from stdout.
  Real numbers: 633 regression + 59 py + 11 js + 55 ACVP-unique = 758.
  PHASE-2-CLOSURE.md §12 and CONTINUITY §32 record the correction.
lesson: A number in a document is an identifier (I34). It must be produced
  by a deterministic tool, not by memory. The pattern is identical to
  DEFECT-007, DEFECT-008, DEFECT-009: a claim was committed before being
  measured. The difference here is that the claim was numeric and would
  have propagated into external communication. The consequence of leaving
  it uncorrected: an investor or auditor could have found the discrepancy
  and lost confidence in all other numbers. Now the source of every number
  is a script that any third party can run.
