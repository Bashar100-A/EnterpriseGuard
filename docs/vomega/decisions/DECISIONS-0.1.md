# ADIE vΩ — Decision Record 0.1

**Date:** 2026-10-06
**Authority:** Project Lead
**Status:** Binding
**Applies to:** vOmega branch onward

---

## Preamble

This record formalizes five leadership decisions that fix the relationship
between the **implemented normative authority** and the **future target
architecture**. It also introduces a new invariant (I34) that applies to all
identifiers in the system — not only claims.

---

## Decision 1 — Terminal Architecture is North Star, not authority

**Choice:** (b) — Parallel document, non-normative for unimplemented layers.

**Formal:**
```
TerminalArchitecture ≠ NormativeContract
```

**Consequences:**
- `META-CONTRACT-0.1` remains the **current** normative authority.
- `ADIE-TERMINAL-ARCHITECTURE-0.1` describes **future** architecture.
- No section of Terminal Architecture may:
  - cancel an existing invariant in META-CONTRACT-0.1
  - cancel an existing test vector
  - redefine an existing normative error code
- No `META-CONTRACT-0.2` is created at this time.

---

## Decision 2 — Attack-ID registry

**Choice:** (ج) — M01–M40 frozen under `META-M*`; extensions use distinct
family namespaces.

**Namespaces:**

| Family | Meaning |
|---|---|
| `META-M01..M40` | Meta-layer (existing, frozen) |
| `CORE-C01..` | Core claim layer |
| `SEM-S01..` | Semantic attacks |
| `BIND-B01..` | Binding attacks |
| `TIME-T01..` | Temporal attacks |
| `EVID-E01..` | Evidence attacks |
| `PRIV-P01..` | Privacy attacks |
| `FHE-F01..` | FHE attacks |
| `ZK-Z01..` | Zero-knowledge attacks |
| `TEE-H01..` | TEE/hardware attacks |
| `RECUR-R01..` | Recursive-state attacks |
| `LOG-L01..` | Transparency-log attacks |

**Alias rule:**
```
M01 ≡ META-M01
M02 ≡ META-M02
...
M40 ≡ META-M40
```

**Frozen:** The numbers M01–M40 keep their existing meaning. No reuse.

---

## Decision 3 — Error code registry

**Choice:** (ب) — Independent `ERROR-REGISTRY-0.1.md`.

**Rationale:**
- Error namespace MUST NOT be coupled to a single contract document.
- META-CONTRACT-0.1 references the registry normatively; it does not own it.

**Registry structure:**
```
ERROR-REGISTRY-0.1
├── E-META-*
├── E-CORE-*
├── E-ACL-*
├── E-AUTH-*
├── E-CRYPTO-*
├── E-PQ-*
├── E-ZK-*
├── E-TEE-*
├── E-TIME-*
├── E-EVID-*
├── E-RECUR-*
├── E-LOG-*
├── E-PRIV-*
└── E-INTERNAL-*
```

**Every code MUST declare:**
```
code
layer
condition
terminal (YES/NO)
assurance_effect
retryable (YES/NO)
normative_response
```

**Distinction:** `STALE ≠ FAIL`. `UNKNOWN ≠ FAIL`. Both are non-terminal
by default and resolved by relying-party policy.

---

## Decision 4 — Wire format

**Choice:** (ب) — Design now, implementation deferred to Phase 2.

**Formal:**
```
Wire design now ≠ Wire standard now
```

**Consequences:**
- §2 of Terminal Architecture is **non-normative**.
- No binary header, section ID, recursive wire object, usage receipt, FHE
  object, or ZK object is fixed as normative protocol.
- When Phase 2 begins, wire content is extracted into `ADIE-WIRE-0.1` as an
  independent normative document with its own conformance vectors.

---

## Decision 5 — Attack families remain separate

**Choice:** (أ) — Preserve family separation; optional central index later.

**Rationale:**
```
Namespace = Meaning
```
`META-M*` immediately communicates "this is a meta-layer attack".
A flat sequence like `ATTACK-073` communicates nothing.

---

## New Invariant — I34

**No historical identifier is ever redefined.**

**Scope (normative):**
- test vector IDs
- error codes
- registry IDs
- versioned semantic object IDs
- META-CONTRACT invariants
- attack vector IDs

**Formal:**
```
∀ id ∈ HistoricalIDs:
  Meaning(id, t1) = Meaning(id, t2)  ∀ t2 > t1
```

**Failure mode:** `E-META-34`.

**Consequence:** Extensions MUST use new identifiers. Version aliasing is
forbidden. Deprecation is allowed (status change); redefinition is not.

---

## Prohibitions effective immediately

1. Reusing `M01..M40` with new meanings.
2. Introducing a new error code into the implementation without registering
   it in `ERROR-REGISTRY-0.1.md`.
3. Treating any wire structure in Terminal Architecture as implemented.
4. Treating ZK / FHE / TEE / IVC / iO as dependencies of the current verifier.
5. Granting Terminal Architecture authority to modify META-CONTRACT, ACL
   implementation, existing tests, or the frozen POC.

---

## Status of the current repository

```
branch:  vOmega
commit:  a453556
frozen:  51/51 (POC v1.0)
Phase 1: 12/12
Phase 1.6: 40/40 (real)
ACL-0.1.md: written
protocol/acl/{ast,eval,normalize}.py: written
tests/vomega/acl/run_all.py: NOT written (Phase 1.7 incomplete)
```

No conflict with this record.

---

## Naming correction

The phrase "actual planet-scale architecture" from the source report is
replaced with:

```
Target Planet-Scale Architecture
```

Reason: Architecture exists ≠ Capability exists.
The formula `Design Score ≠ Implementation Score` is upheld.

---

**End of DECISIONS-0.1**
