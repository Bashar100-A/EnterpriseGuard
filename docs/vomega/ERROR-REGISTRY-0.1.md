# ADIE vΩ — Error Registry

**Document:** ERROR-REGISTRY-0.1
**Status:** Normative (index)
**Date:** 2026-10-06
**Applies to:** All vΩ layers
**Referenced by:** META-CONTRACT-0.1, ACL-0.1, future specs

---

## §0. Purpose

Central index of all error codes across ADIE vΩ. Contracts and specs
**reference** this document; they do not own error codes.

## §1. Required schema

Every registered error code MUST declare:

| Field | Type | Meaning |
|---|---|---|
| `code` | string | unique identifier |
| `layer` | enum | META / CORE / ACL / AUTH / CRYPTO / PQ / ZK / TEE / TIME / EVID / RECUR / LOG / PRIV / INTERNAL |
| `condition` | string | when this fires |
| `terminal` | YES/NO | if YES, no continuation |
| `assurance_effect` | string | which dimensions of the assurance vector are affected |
| `retryable` | YES/NO | whether a retry may succeed |
| `normative_response` | string | what the verifier MUST return |

## §2. Non-terminal states

`STALE`, `UNKNOWN`, `CONFLICT`, `NOT_REQUIRED`, `NOT_EVALUATED` are
**not** errors. They are assurance states resolved by relying-party policy.

`STALE ≠ FAIL`
`UNKNOWN ≠ FAIL`

## §3. Registration rule

An error code is **normative** only if it appears in this registry.
Code that raises an unregistered code fails I34 (identifier immutability)
and MUST be rejected at CI.

## §4. Current registry

### §4.1 E-META-*

| Code | Condition | Terminal | Retryable |
|---|---|---|---|
| E-META-13 | Non-deterministic meta transition | YES | NO |
| E-META-14 | Silent semantic upgrade attempted | YES | NO |
| E-META-15 | Silent semantic downgrade attempted | YES | NO |
| E-META-16a | Meta object schema invalid | YES | NO |
| E-META-16b | Meta object semantics invalid | YES | NO |
| E-META-16c | Meta object lifecycle invalid | YES | NO |
| E-META-16d | Meta object authorization invalid | YES | NO |
| E-META-17 | Compatibility inference attempted | YES | NO |
| E-META-18 | Implicit semantic default detected | YES | NO |
| E-META-19 | Object outside declared universe | YES | NO |
| E-META-20 | Authoring closure incomplete | YES | NO |
| E-META-21 | ACL impurity detected | YES | NO |
| E-META-22 | Offline verification lacks freshness | NO | YES |
| E-META-34 | Historical identifier redefined | YES | NO |

### §4.2 E-CORE-*

| Code | Condition | Terminal | Retryable |
|---|---|---|---|
| E-CLAIM_ROOT_MISMATCH | Recomputed ClaimRoot differs from declared | YES | NO |
| E-BINDING_MISSING_FIELD | Required binding field absent | YES | NO |
| E-BINDING_AUDIENCE_MISMATCH | Audience differs from expectation | YES | NO |
| E-BINDING_PURPOSE_MISMATCH | Purpose differs from expectation | YES | NO |
| E-BINDING_RESOURCE_MISMATCH | Resource differs from expectation | YES | NO |
| E-BINDING_REQUEST_HASH | Recomputing request_hash differs | YES | NO |
| E-SCHEMA | Claim schema invalid | YES | NO |
| E-VERSION | dcp_version unsupported | YES | NO |
| E-PARSE | Bytes not decodable | YES | NO |
| E-CANONICAL | I-JSON / JCS violation | YES | NO |
| E-SIGNATURE | Signature invalid or unsupported | YES | NO |

### §4.3 E-ACL-*

| Code | Condition | Terminal | Retryable |
|---|---|---|---|
| E200_TYPE_MISMATCH | Operation on incompatible types | YES | NO |
| E201_UNKNOWN_OPERATOR | Operator outside closed set | YES | NO |
| E202_MALFORMED_AST | AST structure invalid | YES | NO |
| E208_NESTED_TOO_DEEP | Depth > declared max | YES | NO |
| E209_EMPTY_AND | AND with zero args | YES | NO |
| E210_EMPTY_OR | OR with zero args | YES | NO |
| E211_NON_CANONICAL_INT | Non-canonical integer literal | YES | NO |

### §4.4 Reserved namespaces

The following namespaces are declared but not yet populated:

```
E-AUTH-*      authentication
E-CRYPTO-*    cryptographic primitives
E-PQ-*        post-quantum
E-ZK-*        zero-knowledge
E-TEE-*       trusted execution
E-TIME-*      temporal
E-EVID-*      evidence
E-RECUR-*     recursive state
E-LOG-*       transparency log
E-PRIV-*      privacy
E-INTERNAL-*  internal invariants
```

They are populated as their phase begins. No codes may be added to reserved
namespaces outside a phase transition.

---

**End of ERROR-REGISTRY-0.1**
