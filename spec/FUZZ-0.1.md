# ADIE-FUZZ v0.1 — Property-Based Fuzzing

**Status:** Normative
**Branch:** vOmega
**Date:** 2026-10-06
**Depends on:** META-CONTRACT-0.1, ACL-0.1, AUTHORING-0.1
**Scope:** Phase 1.11 — authoring defense

## §0. Standing

Defines how ADIE's semantic core is stress-tested by property-based
fuzzing, and how Python/JavaScript implementations are compared
byte-by-byte on generated inputs.

Fuzzing is NOT a substitute for hand-written conformance vectors.
It is a complement: it searches for edge cases humans do not imagine.

## §1. Invariants under test

| Invariant | What fuzzing asserts |
|---|---|
| I13 Determinism | Same input → same output, twice |
| I18 No implicit defaults | Undeclared param → error, always |
| I20 Closure completeness | Every accepted input yields exactly 6 authoring keys |
| I21 Purity | No external reads during fuzz |
| I23 Canonical = identity | Canonicalize(e1)==Canonicalize(e2) iff same bytes |
| I34 No identifier redefinition | Once a vector ID emitted, it is fixed |

Cross-language byte-equality (I13 across implementations) is asserted
on every generated input.

## §2. Seed policy

- All fuzzers MUST use a fixed seed.
- The seed is recorded in the fuzzer output.
- Re-running with the same seed and version MUST produce identical inputs.
- Random sources that are NOT the seed (time, /dev/urandom) are forbidden.

## §3. Suites

### §3.1 ACL fuzz

Generates random ASTs and random state dicts, then:
- Runs Python `eval_checked`
- Runs JS equivalent
- Asserts byte-identical verdict (PASS/FAIL/UNKNOWN) OR identical error code

Depth, node count, and operator mix are constrained by declared budget.

### §3.2 ClaimRoot fuzz

Generates random field dictionaries (subset of the 13 named fields,
each possibly ABSENT/NULL/PRESENT with random payload), then:
- Computes ClaimRoot in Python
- Computes ClaimRoot in JS
- Asserts byte-identical 32-byte digest

### §3.3 Authoring fuzz

Generates random templates (with random declared/required params and
a random valid ACL AST), random params dicts (some valid, some with
undeclared keys, some missing required), then:
- Runs Python `Compiler.compile`
- Runs JS `Compiler.compile`
- Asserts byte-identical AClosure OR identical error code

## §4. Failure classification

Any divergence is recorded with:

- `language_pair: py/js`
- `failure_mode: structural | message | crypto | semantic`
- `invariant_at_risk: I13 | I18 | I20 | I21 | I23 | I34`

A failing vector MUST be:
1. Reproducible from the seed alone
2. Reduced to a minimal failing input
3. Added to `tests/vomega/fuzz/regressions.json`
4. Logged in `DEFECTS-LOG.md`

## §5. Budgets

Default budget per suite: 500 iterations.

Extended budget (opt-in): 10000 iterations.

The budget is a parameter, not a constant in the code.

## §6. Non-goals

- No coverage-guided fuzzing in v0.1 (may be added in v0.2)
- No cryptographic fuzzing of RSA internals
- No timing side-channel testing
- No network fuzzing
- No memory-safety testing (Python/JS are managed runtimes)

## §7. Third-language verifier

A Rust implementation of H_A + JCS + ClaimRoot + ACL normalizer MUST
be created and MUST agree byte-for-byte with Python and JavaScript on
all suites. This is Phase 1.11's third-verifier requirement.

Non-goal: full DCP 2.0 pipeline in Rust. The three primitives
(hash, canonicalize, normalize) are the load-bearing ones.

## §8. Exit gate

Phase 1.11 is complete when:

- All 198 existing vectors remain PASS
- All fuzz suites pass at budget 500 with zero divergences
- Rust primitives agree with Python/JS on 200 generated inputs
- Any defect discovered is logged and closed

**End of ADIE-FUZZ-0.1**
