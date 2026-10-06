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
