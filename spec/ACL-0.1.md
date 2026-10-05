# ADIE-ACL v0.1 — Attestation Claim Language

**Status:** Normative
**Branch:** vOmega
**Date:** 2026-10-06
**Depends on:** ADIE-META-CONTRACT-0.1
**Scope:** Phase 1.7 — executable semantics for authorization claims

## §0. Preamble

ACL is a small, decidable language for expressing authorization predicates
over claim state. Used by the authoring compiler to produce the AST embedded
in a DCP 2.0 certificate.

ACL is not Turing complete. Auditability > expressiveness.

### §0.1 Non-goals

- No user-defined functions
- No loops, recursion, iteration
- No external lookups at evaluation time
- No implicit type coercions
- No semantic equivalence beyond structural normalization

### §0.2 Inheritance from META-CONTRACT

- I14/I15: no silent version up/downgrade
- I18: no implicit semantic defaults
- I19: finite operator universe
- I21: pure execution — no I/O
- I23: CanonicalAST identity is protocol identity, not semantic equivalence

## §1. Grammar (JSON wire form)

expr :=
  | {"op":"TRUE"}
  | {"op":"FALSE"}
  | {"op":"NOT","arg":expr}
  | {"op":"AND","args":[expr,...]}
  | {"op":"OR","args":[expr,...]}
  | {"op":"EQ"|"NEQ"|"LT"|"LTE"|"GT"|"GTE","args":[term,term]}
  | {"op":"IN","term":term,"set":[literal,...]}
  | {"op":"EXISTS","path":"a.b.c"}

term :=
  | {"t":"FIELD","path":"a.b.c"}
  | {"t":"INT","v":<int>}
  | {"t":"STR","v":<string>}
  | {"t":"BOOL","v":<bool>}

### §1.1 Closed operator universe

TRUE, FALSE, NOT, AND, OR, EQ, NEQ, LT, LTE, GT, GTE, IN, EXISTS

Any other operator: E201_UNKNOWN_OPERATOR.

## §2. Type system

Bool | Int | Str

Type mismatch: E200_TYPE_MISMATCH (fail-closed).

## §3. Kleene three-valued semantics

V = { PASS, FAIL, UNKNOWN }

NOT: PASS->FAIL, FAIL->PASS, UNKNOWN->UNKNOWN

AND: any FAIL -> FAIL; all PASS -> PASS; else UNKNOWN

OR:  any PASS -> PASS; all FAIL -> FAIL; else UNKNOWN

UNKNOWN never promotes to PASS.

## §4. Evaluation

sigma[path] present -> value
sigma[path] absent  -> UNKNOWN (not error)

Hard errors: malformed AST (E202), unknown op (E201), type mismatch (E200),
depth > 32 (E208), empty AND/OR (E209/E210).

## §5. Normalization (structural only)

R01: NOT(NOT(x)) -> x
R02: AND(x) -> x
R03: OR(x) -> x
R04: AND(...,TRUE,...) -> AND(...)
R05: OR(...,FALSE,...) -> OR(...)
R06: AND(...,FALSE,...) -> FALSE
R07: OR(...,TRUE,...) -> TRUE
R08: flatten nested AND
R09: flatten nested OR
R10: sort commutative operands by canonical bytes
R11: AND() empty after drop -> TRUE
R12: OR() empty after drop -> FALSE

Termination: each rule decreases (depth, node_count) lexicographically.
Confluence: algorithm single-pass, not search-based.

## §6. Canonical AST

CanonicalAST(e) = JCS(Normalize(e))

ProtocolIdentity(e1,e2) <=> CanonicalAST(e1)=CanonicalAST(e2)

NOT semantic equivalence.

## §7. Failure codes (closed set)

E200_TYPE_MISMATCH
E201_UNKNOWN_OPERATOR
E202_MALFORMED_AST
E208_NESTED_TOO_DEEP
E209_EMPTY_AND
E210_EMPTY_OR
E211_NON_CANONICAL_INT

End of ADIE-ACL-0.1
