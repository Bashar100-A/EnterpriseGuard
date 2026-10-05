# ADIE — Meta-Layer Integrity Contract

**Document:** ADIE-META-CONTRACT-0.1
**Status:** Normative
**Branch:** vOmega
**Date:** 2026-10-06
**Predecessor:** ADIE-vΩ Master Execution Blueprint
**Applies to:** Phase 1.5 onwards. Blocks Phase 2.

---

## §0. Preamble

This document fixes the **meta-layer** of ADIE: the layer that governs how claims are authored, compiled, registered, versioned, and validated.

The meta-layer is **not formal**. We do not claim a formal model of it.
The meta-layer is **pinned**: every meta decision is a signed artifact with a digest.
The meta-layer is **finite**: bounded universes, declared registries.
The meta-layer is **deterministic**: F_M is a total, deterministic function.

This is honest. It is weaker than "formally verified" and stronger than "by convention".

### §0.1 Non-goals

This contract does NOT specify:
- cryptography algorithms (Phase 2)
- governance ceremonies (Phase 3)
- zero-knowledge proofs (Phase 4)
- recursive accumulation (Phase 5)
- revenue metering (Phase 6)

This contract defines only **what must be true of the meta-layer before any of those phases begin**.

### §0.2 Foundational axioms (inherited)

From ADIE-vΩ Blueprint:

```
A1  Integrity ≠ Truth
A2  Cryptographic validity ≠ Real-world truth
A3  DID ≠ Trust Anchor
A4  Transparency ≠ Root of Trust
A5  Proof ≠ Trust
A6  ADIE Protocol ≠ ADIE Vendor
```

These are non-negotiable. Any sentence in this document that appears to contradict them is misread.

---

## §1. Meta-Layer State Machine

### §1.1 State

```
M_e = (R, T, W, G, K, P, e)
```

| Field | Meaning |
|---|---|
| R | Registry state (namespaces → entries) |
| T | Template state (templates → canonical digests) |
| W | Rewrite-rule state (rules → canonical digests) |
| G | Governance state (roots, threshold, roles) |
| K | Key-lifecycle state (key_id → KeyState) |
| P | Compatibility state (pair → relation) |
| e | Epoch (unsigned monotonic integer) |

### §1.2 Transition function

```
M_{e+1} = F_M(M_e, μ_e)
```

`F_M` is:
- **Total** on the event set below.
- **Deterministic**: same `(M_e, μ_e)` → same `M_{e+1}`.
- **Non-decreasing** in epoch.

### §1.3 Event set (closed, finite)

```
REGISTER_TEMPLATE
REGISTER_REWRITE_RULE
DECLARE_COMPATIBILITY
DEPRECATE_VERSION
REVOKE_KEY
ROTATE_ROOT
FREEZE_REGISTRY
RESUME_REGISTRY
DECLARE_MIGRATION
```

Any event not in this list: **REJECT** with `E-META-13`.

### §1.4 Event preconditions (each event type)

Every event μ must carry:
- `event_id` (unique, monotonic)
- `issuer_key_id` (must be a currently-active Manifest key)
- `signature` (over the canonical event payload)
- `prev_epoch`
- `new_epoch`

The verifier MUST check `prev_epoch == current_epoch` for sequential application.

### §1.5 Failure mode

```
E-META-13: unknown event / non-deterministic transition / epoch mismatch
```

---

## §2. Meta Object Schema

### §2.1 Canonical form

Every meta object is:

```
O = (
  type,
  id,
  version,
  payload,
  status,
  prev,
  effective,
  expiry,
  issuer,
  digest
)
```

### §2.2 Identity

```
ID(O) = H_A("meta-object", canonical(O_without_digest))
```

Where `H_A` is the domain-separated hash from `protocol/core/domain_hash.py`.

### §2.3 Signature

```
Sig(O, Issuer)
```

The signature covers `ID(O)`. Issuer must be a Manifest key.

### §2.4 Lifecycle states

```
PROPOSED
ACTIVE
DEPRECATED
REVOKED
EXPIRED
SUPERSEDED
```

### §2.5 Invariant: signature is not semantics

```
I16: SignedMetaObject ≠ SemanticallyValidMetaObject
```

Every meta object MUST pass four independent validations:

1. **Schema validation** — JSON shape, types
2. **Semantic validation** — payload is meaningful within its `type`
3. **Lifecycle validation** — status transitions are permitted
4. **Authorization validation** — issuer role permits this type

Failure codes:
```
E-META-16a  schema
E-META-16b  semantic
E-META-16c  lifecycle
E-META-16d  authorization
```

---

## §3. Ten Invariants

Each invariant has: **Claim**, **Formal statement**, **Normative text**, **Failure mode**, **Test vector IDs**.

### I13 — Meta-State Determinism

**Claim:** Meta transitions are deterministic.

**Formal:**
```
∀ M, μ:  F_M(M, μ) is uniquely defined
```

**Normative:** `F_M` MUST be a total function on the closed event set §1.3. No "interpreter-dependent" behavior.

**Failure:** `E-META-13`.

**Tests:** M01, M08, M13, M19, M25, M31, M37.

---

### I14 — No Silent Semantic Upgrade

**Claim:** A meta object at version `v` is never interpreted as `v+n`.

**Formal:**
```
Known(M, v) = false  ⇒  reject, do not upgrade
```

**Normative:** A verifier that knows only `v-1` returns `E-META-14` on `v`. No compatibility inference.

**Failure:** `E-META-14`.

**Tests:** M02, M09, M14, M20, M26, M32, M38.

---

### I15 — No Silent Semantic Downgrade

**Claim:** A meta object at version `v` is never interpreted as `v-n`.

**Formal:**
```
Known(M, v) = false  ⇒  reject, do not downgrade
```

**Normative:** A verifier that knows only `v+1` returns `E-META-15` on `v`. No compatibility inference.

**Failure:** `E-META-15`.

**Tests:** M03, M10, M15, M21, M27, M33, M39.

**Note:** I14 + I15 together forbid ALL implicit version negotiation. Transitions are **signed events** (I13), not inferences.

---

### I16 — Signature ≠ Semantic Validity

**Claim:** Signed does not mean valid.

**Formal:**
```
Signed(O)  ⇏  Valid(O)
Valid(O)   ⇔  Schema ∧ Semantic ∧ Lifecycle ∧ Authorization
```

**Normative:** See §2.5.

**Failure:** `E-META-16a..d`.

**Tests:** M04, M11, M16, M22, M28, M34, M40.

---

### I17 — No Compatibility Inference

**Claim:** Compatibility is declared, never inferred.

**Formal:**
```
Compat(a,b) MUST NOT be derived from:
  - same major version
  - same field names
  - same semantic digest prefix
```

**Normative:** Every compatibility relation is an explicit signed object:

```
K_{a,b} = (
  from, to, scope, relation,
  proofDigest, constraints, authority, expiry
)

relation ∈ { EXACT, ENCODING, SEMANTIC, INCOMPATIBLE }
```

If `relation = SEMANTIC`, `proofDigest` is mandatory.

**Failure:** `E-META-17`.

**Tests:** M05, M12, M17, M23, M29, M35.

---

### I18 — No Implicit Semantic Defaults

**Claim:** No hidden defaults.

**Formal:**
```
Effect(O) = Effect(Explicit(O))
```

**Normative:** Every value that affects meaning MUST appear in the parameter object OR in the template digest. No `timeout=30` hidden in the compiler. No silent locale.

**Failure:** `E-META-18`.

**Tests:** M06, M13, M18, M24, M30, M36.

---

### I19 — Finite Universe

**Claim:** The set of known meta objects is finite and declared.

**Formal:**
```
Universe_e = (
  ACLVersions,
  TemplateIDs,
  RewriteRuleIDs,
  RegistryNamespaces,
  Algorithms,
  CompatibilityRelations
)
|Universe_e| < ∞
UnknownObject ∉ Universe_e  ⇒  FAIL
```

**Normative:** Every Protocol Manifest declares its Universe. No "maybe in the future".

**Failure:** `E-META-19`.

**Tests:** M07, M14, M19, M25, M31, M37.

---

### I20 — Authoring Closure Completeness

**Claim:** The compiler's output depends only on declared inputs.

**Formal:**
```
AClosure = (
  TemplateDigest,
  ParameterDigest,
  CompilerDigest,
  ACLVersion,
  CanonicalASTDigest,
  MetaManifestDigest
)

Effect(AClosure) = Effect(Compile)
```

**Normative:** The compiler MUST NOT depend on:
- environment variables
- wall clock
- network
- locale
- mutable registry snapshot not bound by digest

**Failure:** `E-META-20`.

**Tests:** M08, M15, M20, M26, M32, M38.

---

### I21 — ACL Execution Purity

**Claim:** ACL evaluation has no side effects.

**Formal:**
```
∀ e, σ:  Eval(e, σ) does not read or write external state
```

**Normative:** The ACL MUST NOT execute:
- HTTP requests
- DB queries
- filesystem lookups
- DNS
- plugins

All external data MUST be pre-loaded into `EvidenceSet`. The ACL reads only `FIELD(EvidenceSet,...)`.

**Failure:** `E-META-21`.

**Tests:** M09, M16, M21, M27, M33, M39.

---

### I22 — Offline Revocation Honesty

**Claim:** Offline verification reports uncertainty, never assumes freshness.

**Formal:**
```
known_revocation_epoch = e
claim_depends_on_epoch(e') with e' > e
  ⇒  result ∈ { STALE, UNKNOWN }
  ⇒  result ≠ PASS
```

**Normative:** The verifier MUST NOT return `PASS` for a claim depending on revocation data newer than its manifest epoch.

**Failure:** `E-META-22`.

**Tests:** M10, M17, M22, M28, M34, M40.

---

## §4. Attack Matrix M01–M40

Format: `(id, attack, target invariant, expected failure code)`.

### §4.1 Meta-layer attacks

| ID | Attack | Invariant | Expected |
|---|---|---|---|
| M01 | Template Substitution (same ID, different digest) | I13 | E-META-13 |
| M02 | Compiler Substitution | I14 | E-META-14 |
| M03 | Hidden Default Injection | I18 | E-META-18 |
| M04 | Compatibility Forgery (no proof) | I17 | E-META-17 |
| M05 | Registry Fork (same ID, two digests) | I13 | E-META-13 |
| M06 | Rewrite Rule Shadowing | I14 | E-META-14 |
| M07 | Rewrite Precondition Bypass | I16 | E-META-16b |
| M08 | Epoch Rollback | I13 | E-META-13 |
| M09 | Revocation Suppression | I22 | E-META-22 |
| M10 | Governance Capture (below threshold) | I16 | E-META-16d |
| M11 | Semantic Phantom Field | I16 | E-META-16a |
| M12 | UI/Compiler Divergence | I20 | E-META-20 |
| M13 | Manifest Downgrade | I15 | E-META-15 |
| M14 | Key-Role Confusion | I16 | E-META-16d |
| M15 | DID-to-Key Confusion | I16 | E-META-16d |
| M16 | Dependency-Closure Omission | I20 | E-META-20 |
| M17 | Unknown Critical Registry Object | I19 | E-META-19 |
| M18 | Unsafe Non-Critical Object | I19 | E-META-19 |
| M19 | Version Alias Collision | I14 | E-META-14 |
| M20 | Same-ID / Different-Digest Collision | I13 | E-META-13 |
| M21 | Signature-Valid, Semantically-Invalid | I16 | E-META-16b |
| M22 | Stale Revocation Accepted | I22 | E-META-22 |
| M23 | Compatibility Chained (a→b→c inferred) | I17 | E-META-17 |
| M24 | Implicit Locale Default | I18 | E-META-18 |
| M25 | Freeze Ignored | I13 | E-META-13 |
| M26 | Silent ACL Patch | I14 | E-META-14 |
| M27 | External I/O During Eval | I21 | E-META-21 |
| M28 | Replay Against Wrong Epoch | I13 | E-META-13 |
| M29 | Cross-Registry Compatibility | I17 | E-META-17 |
| M30 | Environment Variable Leak | I20 | E-META-20 |
| M31 | Manifest Not In Universe | I19 | E-META-19 |
| M32 | Compiler Version Mismatch | I20 | E-META-20 |
| M33 | Live Network Read in ACL | I21 | E-META-21 |
| M34 | Revocation Epoch Skew | I22 | E-META-22 |
| M35 | Inferred Semantic Equivalence | I17 | E-META-17 |
| M36 | Template Hidden Parameter | I18 | E-META-18 |
| M37 | Epoch Skip | I13 | E-META-13 |
| M38 | Authoring Closure Missing Field | I20 | E-META-20 |
| M39 | Concurrent Registry Mutation | I21 | E-META-21 |
| M40 | Offline PASS Despite Stale Data | I22 | E-META-22 |

### §4.2 Normative rule

Every M0x MUST have:
- a test vector in `tests/vomega/meta/`
- a declared expected failure code
- a declared target invariant

No M0x may be skipped. Failure to pass ALL 40 blocks Phase 2.

---

## §5. Implementation Independence Criteria

### §5.1 Independence axes

| Axis | Requirement |
|---|---|
| Language | V1 ≠ V2 (e.g., Python vs Rust) |
| Parser | independent implementations |
| Canonicalizer | independent implementations |
| Test-vector provenance | not shared as sole source |
| Crypto library | distinct implementations |
| Semantic evaluator | independently written |

### §5.2 Test vector categories

Three independent sources:

```
TV_SPEC       — hand-written from this document
TV_FORMAL     — derived from a bounded proof model
TV_ATTACK     — from adversarial generation
```

### §5.3 K_ACL role

`K_ACL` is a **consistency oracle**, not a source of truth.
It checks that `TV_SPEC`, `TV_FORMAL`, `TV_ATTACK` do not contradict each other.
It does NOT generate truth. It does NOT define semantics.

### §5.4 Failure mode

Any of:
```
E-META-51: TV_SPEC/TV_FORMAL divergence
E-META-52: TV_SPEC/TV_ATTACK divergence
E-META-53: implementation pair diverges on same input
```

blocks the release gate.

---

## §6. Assurance Vector Extension

### §6.1 Extended vector

```
{
  "meta_integrity":       "PASS" | "FAIL" | "UNKNOWN",
  "authoring_integrity":  "PASS" | "FAIL" | "UNKNOWN",
  "registry_integrity":   "PASS" | "FAIL" | "CONFLICT",
  "semantic_kernel":      "PASS" | "FAIL" | "STALE",
  "compatibility":        "PASS" | "FAIL" | "CONFLICT",
  "integrity":            ...,
  "binding":              ...,
  "claim_root":           ...,
  "signature":            ...
}
```

### §6.2 Normative

- `meta_integrity` reflects I13–I16.
- `authoring_integrity` reflects I20.
- `registry_integrity` reflects I19 + M05.
- `semantic_kernel` reflects I21.
- `compatibility` reflects I17.

### §6.3 Relying-party decision

```
Decision = Policy_RP(AssuranceVector)
```

Never:
```
VerifierResult == true  ⇒  Truth
```

---

## §7. Test Vector Triple Provenance

### §7.1 Rules

- `TV_SPEC` is derived from the specification text by a human editor.
- `TV_FORMAL` is derived from a bounded proof model (Lean/Coq/Isabelle or agreed substitute).
- `TV_ATTACK` is produced by an adversarial generator independent from the first two.

### §7.2 K_ACL consistency check

The kernel `K_ACL`:
- MUST NOT be the sole source of any test vector.
- MUST be run against `TV_SPEC ∪ TV_FORMAL ∪ TV_ATTACK`.
- MUST return FAIL if any vector diverges.

### §7.3 Failure mode

```
E-META-71: K_ACL diverges from TV_SPEC
E-META-72: K_ACL diverges from TV_FORMAL
E-META-73: K_ACL diverges from TV_ATTACK
```

---

## §8. Specification Division

The specification is decomposed into six independent modules:

```
ADIE-CORE   Claim model, commitments, assurance, failure model
ADIE-ACL    Grammar, types, semantics, canonical AST
ADIE-META   Registries, templates, compatibility, rewrite rules, lifecycle, governance
ADIE-WIRE   JSON/JCS, CBOR/COSE, size profiles
ADIE-PROOF  ZK, recursive, TEE, FHE
ADIE-OPS    Keys, rotation, revocation, migration, offline operation
```

**Phase rule:** ADIE-PROOF MUST NOT enter MVP.

---

## §9. Execution Order (normative)

```
0.  Freeze POC                        ✓ done (tag v1.0-poc)
1.  DCP 2.0                           ✓ done (Phase 1)
2.  ClaimRoot + Binding               ✓ done (Phase 1)
3.  63-test baseline                  ✓ done (12 + 51)
4.  META contract                     ◀ this document
5.  ACL executable semantics
6.  Authoring compiler
7.  Registry + compatibility
8.  Pilot claim
9.  Python verifier
10. Rust independent verifier
11. Differential tests
12. Governance ceremony
13. Hybrid RS256 + ML-DSA
14. WASM adapter
15. Model/weight provenance
16. ZK-0
17. Transparency
18. Recursive state
19. Regional/global aggregation
20. Enterprise SDK
21. Privacy-preserving metering
22. Security review
23. External pilot
24. Interoperability program
25. Standardization
```

No phase may outrun its predecessor.

---

## §10. MetaScore

### §10.1 Definition

```
MetaScore = |Passed Meta Properties| / |Required Meta Properties|
```

Required properties:

- I13 (Meta-State Determinism)
- I14 (No Silent Semantic Upgrade)
- I15 (No Silent Semantic Downgrade)
- I16 (Signature ≠ Semantic Validity)
- I17 (No Compatibility Inference)
- I18 (No Implicit Semantic Defaults)
- I19 (Finite Universe)
- I20 (Authoring Closure Completeness)
- I21 (ACL Execution Purity)
- I22 (Offline Revocation Honesty)
- M01–M40 (Attack Matrix)
- TV_SPEC / TV_FORMAL / TV_ATTACK coherence

### §10.2 Gate

Phase 2 unblocks only when:

```
MetaScore = 1.0
```

### §10.3 Test method

Tests MUST include:
- happy path
- fault injection
- malformed objects
- forks
- rollbacks
- concurrent mutations

Happy-path-only passing is insufficient.

---

## §11. What This Contract Does NOT Claim

- That the meta-layer is formally verified.
- That the meta-layer is complete.
- That MetaScore = 1.0 implies production readiness.
- That passing M01–M40 exhausts all attacks.

The contract claims only:
```
The meta-layer is pinned, finite, testable, and honest about its limits.
```

---

## §12. Amendment

Any change to this contract:
- requires a new document version (0.2, 0.3, …)
- requires re-running M01–M40
- requires commit on `vOmega` branch
- MUST NOT be silent

No in-place edits. No aliasing. No exceptions.

---

**End of ADIE-META-CONTRACT-0.1**

---

## §13. Addendum 1 — Invariant I34 and Error Registry coupling

**Date added:** 2026-10-06
**Authority:** DECISIONS-0.1
**Effect:** Extends the invariant set. Does not modify I13–I22.

### §13.1 I34 — No historical identifier redefinition

**Claim:** No identifier in the historical record is ever redefined.

**Scope (normative):**
- test vector IDs (M01..M40, and future families)
- error codes
- registry IDs
- versioned semantic object IDs
- META-CONTRACT invariant IDs (I1..I34)
- attack vector IDs
- compatibility relation IDs

**Formal:**
```
∀ id ∈ HistoricalIDs:
  Meaning(id, t1) = Meaning(id, t2)  for all t2 > t1
```

**Normative:** Deprecation is permitted (status change).
Redefinition is forbidden. Extensions MUST use new identifiers.

**Failure mode:** `E-META-34`.

**Test vectors:** META-M34a (rename attempt), META-M34b (alias reintroduction).

### §13.2 Error registry coupling

Effective immediately, no implementation MAY raise an error code not
registered in `ERROR-REGISTRY-0.1.md`. The registry is normative as an
**index**; individual error semantics remain defined by their layer spec.

### §13.3 Terminal Architecture relationship

`docs/vomega/ADIE-TERMINAL-ARCHITECTURE-0.1.md` is a **non-normative**
North Star document. It:
- does NOT cancel any invariant in this contract;
- does NOT cancel any test vector;
- does NOT redefine any error code;
- describes future layers whose implementation is deferred to later phases.

### §13.4 Attack-ID families

Existing M01–M40 are frozen under aliases `META-M01..META-M40`.
New attack families use distinct namespaces:
`CORE-C`, `SEM-S`, `BIND-B`, `TIME-T`, `EVID-E`, `PRIV-P`,
`FHE-F`, `ZK-Z`, `TEE-H`, `RECUR-R`, `LOG-L`.

### §13.5 Wire format

Wire format (§2 of Terminal Architecture) is **design-only**.
Implementation is deferred to Phase 2, at which point wire content becomes
`ADIE-WIRE-0.1` with independent conformance vectors.

---

**End of Addendum 1**
