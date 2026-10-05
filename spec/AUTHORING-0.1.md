# ADIE-AUTHORING v0.1 — Compiler Specification

**Status:** Normative
**Branch:** vOmega
**Date:** 2026-10-06
**Depends on:** META-CONTRACT-0.1, ACL-0.1, ERROR-REGISTRY-0.1

## §0. Standing

Defines how a claim's AST is produced deterministically from
(Template, Parameters, Manifest). Output is the Authoring Closure
(AClosure) embedded in a DCP 2.0 certificate.

## §1. Function signature

    compile(Compiler, Template, Parameters) -> AClosure

Compiler is a FROZEN object binding:
- code_digest       (this implementation version)
- manifest          (the meta-layer state)
- acl_version       (the ACL language version)

The compiler is immutable after construction. No internal state changes
between calls.

## §2. Inputs

Template (JSON object):
- template_id            string, required
- acl_version            string, required, must equal Compiler.acl_version
- declared_params        list of strings, required
- required_params        list of strings, required, subset of declared
- forbidden_env          list of strings, optional
- ast                    ACL expression (validated by protocol/acl/ast.py)
- purity                 "PURE" required

Parameters (JSON object):
- Every key MUST be in declared_params.
- Every key in required_params MUST be present.
- No implicit defaults permitted (I18).

Manifest:
- must be a Manifest instance with non-empty .digest
- raw dict is rejected (type-checked at construction)

## §3. Output — AClosure

The compiler returns a dict with exactly these keys:

    template_digest         sha256:...
    parameter_digest        sha256:...
    compiler_digest         sha256:...
    acl_version             string
    canonical_ast_digest    sha256:...
    meta_manifest_digest    sha256:...

No other keys. Missing any -> E-META-20.

## §4. Domain-separated digests

All digests use H_A with domain tags:
- "template"       over canonical_bytes(template)
- "parameters"     over canonical_bytes(parameters)
- "compiler-code"  over the version constant
- "ast"            over canonical_bytes(canonical_ast(ast))
- "manifest"       provided by Manifest.digest

No digest may be reused across domains even if underlying bytes match.

## §5. Invariants

I18: no implicit defaults.
     A parameter not in declared_params -> E-META-18.

I20: AClosure completeness.
     All six fields present, non-empty, correct format.

I21: purity.
     - Compiler MUST NOT read env vars, network, filesystem, clock.
     - forbidden_env check is a defensive guard, not the primary mechanism.
       The primary mechanism is that Python/JS implementations literally
       cannot do those things inside the compile call.

Determinism:
     compile(C, T, P) == compile(C, T, P) byte-for-byte.

## §6. Failure codes

From ERROR-REGISTRY-0.1:
- E-META-18   implicit default / undeclared parameter
- E-META-20   closure incomplete / manifest missing
- E-META-21   impurity detected
- E200..E211  AST validation (propagated from protocol/acl/ast.py)

## §7. Differential conformance

Python and JavaScript implementations MUST produce byte-identical AClosure
on every vector in tests/vomega/authoring/vectors.json.

Divergence -> differential test FAIL -> blocks release.

## §8. Non-goals (Phase 1.8)

- No signature (signing enters at Phase 2)
- No CBOR wire encoding (Phase 2)
- No caching (may be added later without changing output contract)
- No streaming or incremental compilation
- No partial evaluation

## §9. Compiler identity

The Compiler's full identity is:

    H_A("compiler-identity",
        canonical_bytes({code_digest, manifest.digest, acl_version}))

Distinct from compiler_digest, which pins only the code.

## §10. Rationale for the frozen Compiler object

The compiler is a frozen dataclass. Consequences:
- Manifest bound at construction -> no TOCTOU between reads.
- Compiler identity includes manifest.digest -> two compilers with
  different manifests are different objects, not one object called with
  different arguments.
- Matches the pinned-artifact model of META-CONTRACT §2.
- Functional at call site: compile(template, params) is pure given the
  instance, and the instance is immutable.

## §11. Relationship to META-CONTRACT invariants

    I13  Determinism       -> §5 determinism clause
    I14  No silent upgrade -> acl_version must equal Compiler.acl_version
    I15  No silent down    -> same
    I18  No implicit defs  -> declared_params enforced
    I19  Finite universe   -> params keys are finite (from declared_params)
    I20  Closure complete  -> six mandatory fields in AClosure
    I21  Purity            -> no I/O inside compile

## §12. Amendment

Any change requires new version (0.2, 0.3). No in-place edits.
Append-only.

End of ADIE-AUTHORING-0.1
