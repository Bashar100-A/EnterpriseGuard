# ADIE-RUST-VERIFIER v0.1 — Semantic Verifier

**Status:** Normative
**Branch:** vOmega
**Date:** 2026-10-06
**Depends on:** META-CONTRACT-0.1, ACL-0.1, AUTHORING-0.1
**Scope:** Phase 1.12-lite — third-language semantic verifier

## §0. Purpose

Provide a Rust implementation that verifies every SEMANTIC layer of a
DCP 2.0 certificate, so that three independent language stacks
(Python, JavaScript, Rust) agree on semantic verdicts.

## §1. What is verified

- Required field presence (E_SCHEMA)
- dcp_version == "2.0" (E_VERSION)
- ClaimRoot recomputation (E_CLAIM_ROOT_MISMATCH)
- Binding: request_hash recomputation (E_BINDING_REQUEST_HASH),
  expected audience (E_BINDING_AUDIENCE_MISMATCH),
  required fields (E_BINDING_MISSING_FIELD)
- Authoring closure: 6 keys, well-formed SHA-256 digests,
  acl_version constant (E-META-20, E-META-14)
- AST canonicalization digest (E-META-20)

## §2. What is NOT verified — explicit gaps

**GAP-1 (Signature):** RSA-2048 verification is NOT performed.
The output marks `signature: "SKIPPED"`. A certificate with a
tampered but structurally valid signature will be accepted by the
Rust verifier. This is a documented, deliberate gap.

Rationale: RSA verification in Rust requires either an external
crate (`rsa`/`ring`) or ~550 lines of BigInt + PKCS#1 v1.5. Neither
is acceptable in Phase 1.12-lite. The cryptographic check remains
in Python and JavaScript, both of which have been tested.

**GAP-2 (Strict load I-JSON):** Duplicate-key rejection,
non-NFC string detection, and float rejection are NOT performed.
serde_json parses standard JSON; strict_load semantics remain
Python/JS-only.

**GAP-3 (ACL AST structural validation):** The Rust verifier checks
the canonical AST digest but does NOT run the full ACL validate()
for E201/E202/E209/E210 errors. Certs with malformed ASTs may pass
if they are canonicalizable.

**GAP-4 (Fuzz scale):** The differential fuzz uses 200 random certs.
10k+ scale is deferred.

## §3. Output format

Success:{"checks":{"acl_version":"PASS","ast_canonicalization":"PASS",
"authoring_closure":"PASS","binding":"PASS",
"claim_root":"PASS","dcp20":"PASS","signature":"SKIPPED"},
"status":"VALID"}
text


Failure:

{"code":"E_CLAIM_ROOT_MISMATCH","message":"...","status":"INVALID"}
text


## §4. Message format compatibility

Error messages MUST match Python's format exactly:
- DCP-level: `str(VerifyError)[:120]` where str(e) = "code: msg"
- Binding-level: two-stage slicing per verify_pipeline.py
- CLI-level (E-META-*): unprefixed message

## §5. Differential test

Python vs Rust on 15 pilot vectors (14 excluding P13 signature tamper).
For VALID cases: compare `checks` maps after stripping `signature`.
For INVALID cases: compare `code` and `message` byte-for-byte.

## §6. Exit gate

- All 15 pilot vectors: VALID/INVALID decisions match Python
- For INVALID: codes and messages match exactly
- Known gaps documented and reproducible

**End of ADIE-RUST-VERIFIER-0.1**
