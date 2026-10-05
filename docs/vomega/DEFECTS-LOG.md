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

## DEFECT-002 — A25: EQ did not enforce type check

date: 2026-10-06
commit_found: 5589bb2
commit_fixed: d39fb02
suite: tests/vomega/acl/run_all.py
test_id: A25
test_name: EQ int/str -> E200_TYPE_MISMATCH
category: code
root_cause: In protocol/acl/eval.py the EQ/NEQ branch returned PASS/FAIL before the type-check block ran. EQ(INT(5), STR("x")) returned FAIL instead of raising E200_TYPE_MISMATCH, violating ACL-0.1 section 2.2 (fail-closed on type mismatch).
fix: Moved type check to top of EQ/NEQ/LT branch. LT/LTE/GT/GTE additionally reject Bool and non-(int,str).
lesson: Fail-closed only holds if the check runs before any return. Order of checks is a security property.
