# ADIE — Decisions Log

**Purpose:** All architectural decisions taken during P0 → P-STEP-06.1, with
rationale and status.

---

## Decision Format

Each decision:
- **ID:** sequential
- **Date:** in-conversation date
- **Phase:** which step
- **Decision:** what was decided
- **Rationale:** why
- **Status:** adopted / amended / superseded

---

## DEC-001 — Start Forensic Audit (P0)

**Phase:** 0
**Decision:** Before any fix or new design, conduct a read-only forensic
audit of the entire repository.
**Rationale:** Earlier reports (V1) contained unverified assumptions.
**Status:** ✅ Adopted; completed.

---

## DEC-002 — Forensic Baseline Scope = 6 Questions

**Phase:** 0
**Decision:** Limit P0 scope to 6 questions, deliverable = 10-page
`FORENSIC_BASELINE.md`.
**Rationale:** Prevent audit becoming infinite.
**Status:** ✅ Adopted; completed.

---

## DEC-003 — Do Not Trust Any Prior Report

**Phase:** 0
**Decision:** Treat earlier assessment as hypothesis, not fact.
**Rationale:** Preserve intellectual honesty.
**Status:** ✅ Adopted.

---

## DEC-004 — Read-Only Rule During Audit

**Phase:** 0
**Decision:** No modifications during P0 or any subsequent reconnaissance.
**Rationale:** Discovery must not contaminate the object being discovered.
**Status:** ✅ Adopted; still in force.

---

## DEC-005 — Rule 15 Exception for Protected Paths (P-STEP-01)

**Phase:** P-STEP-01
**Decision:** Owner authorizes reading `src/enterpriseguard/adie/` under
Rule 15 for this session only.
**Rationale:** H4 requires reading policy/decision/manifest internals.
**Status:** ✅ Adopted; scoped to session.

---

## DEC-006 — 4-Level Verification (Signature / Integrity / Provenance / Claim)

**Phase:** P-STEP-01
**Decision:** Any verification task must distinguish 4 levels.
**Rationale:** Signature validity ≠ Claim validity.
**Status:** ✅ Adopted.

---

## DEC-007 — `UNKNOWN ≠ PASS ≠ REFUTED`

**Phase:** P-STEP-01
**Decision:** Three distinct outcomes for any hypothesis.
**Rationale:** Prevent filling gaps with assumed goodness.
**Status:** ✅ Adopted; Invariant.

---

## DEC-008 — H1–H4 as Falsifiable Hypotheses

**Phase:** P-STEP-01
**Decision:** State testable hypotheses, not conclusions.
**Rationale:** Reasoning must be inspectable.
**Status:** ✅ Adopted.

---

## DEC-009 — `NOT TESTABLE ≠ REFUTED`

**Phase:** P-STEP-01
**Decision:** If a hypothesis cannot be tested due to upstream failure, mark
`NOT TESTABLE`, not `REFUTED`.
**Rationale:** Distinguish hypothesis failure from dependency failure.
**Status:** ✅ Adopted.

---

## DEC-010 — Design Intent vs Implementation Alignment

**Phase:** P-STEP-03
**Decision:** Alignment and Fitness are two orthogonal columns.
**Rationale:** Design can be aligned and unfit.
**Status:** ✅ Adopted.

---

## DEC-011 — D: Semantic Reframing + Authority Unification

**Phase:** P-STEP-03/04
**Decision:** Adopt D+ (reframe + unify).
**Rationale:** Fix at architectural level, not as rename.
**Status:** ✅ Adopted.

---

## DEC-012 — Preserve `DecisionContract` Name

**Phase:** P-STEP-04
**Decision:** `DecisionContract` preserved for canonical layer. Legacy
reframed as `SignedIntent`.
**Rationale:** Don't lose the target name.
**Status:** ✅ Adopted.

---

## DEC-013 — `SignedIntent` as Assertion Layer

**Phase:** P-STEP-04
**Decision:** V1 artifact renamed (conceptually) to `SignedIntent`.
**Rationale:** Assertion ≠ Authority.
**Status:** ✅ Adopted.

---

## DEC-014 — New Invariants (Assertion ≠ Authority, Signature ≠ Authority, Integrity ≠ Validity)

**Phase:** P-STEP-04
**Decision:** Add three invariants.
**Rationale:** Formalize the split.
**Status:** ✅ Adopted.

---

## DEC-015 — `/v1/intents` for V1; `/v1/decisions` for V2

**Phase:** P-STEP-04
**Decision:** V1 endpoint renamed; V2 endpoint reserved.
**Rationale:** Don't pollute future name.
**Status:** ✅ Adopted.

---

## DEC-016 — Compatibility Shim for Legacy

**Phase:** P-STEP-04
**Decision:** Legacy `/v1/decisions` becomes deprecated alias with warning.
**Rationale:** Don't break existing consumers; document the boundary.
**Status:** ✅ Adopted.

---

## DEC-017 — No Shared Lifecycle

**Phase:** P-STEP-05
**Decision:** 12 entities, each with its own lifecycle.
**Rationale:** Forcing one lifecycle on all is V1's original sin.
**Status:** ✅ Adopted.

---

## DEC-018 — Entity Graph, not Pipeline

**Phase:** P-STEP-05
**Decision:** Model as Entity Graph with typed transitions.
**Rationale:** Pipeline hides relationships; graph shows them.
**Status:** ✅ Adopted.

---

## DEC-019 — Decision Lineage as Primary Trust Artifact

**Phase:** P-STEP-05
**Decision:** Lineage is the trust artifact; `DecisionContract` is the
operational output.
**Rationale:** Trust comes from reconstrucibility, not from the artifact
alone.
**Status:** ✅ Adopted (amended in P-STEP-06).

---

## DEC-020 — Manifest Required iff External Obligation

**Phase:** P-STEP-05
**Decision:** Manifest required **iff** decision declares external execution
obligation.
**Rationale:** Preserve `Decision ≠ Execution`.
**Status:** ✅ Adopted.

---

## DEC-021 — Prediction Absence is Policy-Derived Fact

**Phase:** P-STEP-05
**Decision:** `PolicyEvaluation` records `NOT_REQUIRED | REQUIRED_SATISFIED |
REQUIRED_MISSING`.
**Rationale:** Absence must be provable.
**Status:** ✅ Adopted.

---

## DEC-022 — Conceptual Reclassification, Not In-Place Rename

**Phase:** P-STEP-05
**Decision:** Legacy `DecisionContract` becomes compatibility representation
for `SignedIntent`. No file rename.
**Rationale:** Preserve lineage of the legacy entity.
**Status:** ✅ Adopted.

---

## DEC-023 — SIBB Stores Two Distinct Semantic Types

**Phase:** P-STEP-05
**Decision:** SIBB stores Evidence and Authority artifacts. Shared integrity
layer; different semantic types.
**Rationale:** Prevent semantic conflation.
**Status:** ✅ Adopted.

---

## DEC-024 — Lineage Answers "Causally Sufficient"

**Phase:** P-STEP-05
**Decision:** Lineage answers "what facts and rules were causally
sufficient?" — not "what is associated?"
**Rationale:** Causation ≠ Correlation.
**Status:** ✅ Adopted.

---

## DEC-025 — B: Ledger Above SIBB

**Phase:** P-STEP-06.1
**Decision:** Adopt Option B (Ledger above SIBB).
**Rationale:**
- SIBB = artifact store.
- Ledger = event store.
- Lineage = reconstruction from both.
**Status:** ✅ Adopted.

---

## DEC-026 — Ledger is Not Just an Event Log

**Phase:** P-STEP-06.1
**Decision:** Ledger must model causal edges (caused_by, required_for,
satisfied_by, derived_from, produced, superseded, revoked_by).
**Rationale:** To distinguish causal edges from mere references.
**Status:** ✅ Adopted.

---

## DEC-027 — Authority Model v1 (proposed)

**Phase:** P-STEP-06.1
**Decision:** Adopt Authority Model with `AuthorityGrant`, chain, time
model, scope, constraints, `AuthorityProof`.
**Status:** ✅ Adopted with 5 amendments (see DEC-028 to DEC-032).

---

## DEC-028 — `policy_basis_ref` is not Retroactive

**Phase:** P-STEP-06.1
**Decision:** Grant evaluated against policy version under which it was
issued + explicit subsequent invalidation.
**Rationale:** Prevent temporal discontinuity.
**Status:** ✅ Adopted.

---

## DEC-029 — Authority Resolution is Deterministic, Fail-Closed

**Phase:** P-STEP-06.1
**Decision:** No heuristic "strongest grant." Policy-defined resolution.
If ambiguous → `AMBIGUOUS` → no `DecisionContract`.
**Rationale:** No general mathematical answer for "strongest."
**Status:** ✅ Adopted.

---

## DEC-030 — Grant References Governance Directly

**Phase:** P-STEP-06.1
**Decision:** `policy_basis_ref` + `policy_version` + `policy_hash`.
No intermediate abstraction.
**Rationale:** Prevent re-creating V1's identity problem.
**Status:** ✅ Adopted.

---

## DEC-031 — `Approval ≠ AuthorityGrant`

**Phase:** P-STEP-06.1
**Decision:** Provisional: `Approval` is a separate entity.
**Rationale:** Grant = who may do X. Approval = condition for specific case.
**Status:** ✅ Provisional; to confirm after Ledger design.

---

## DEC-032 — Trust Anchor ≠ Genesis Key

**Phase:** P-STEP-06.1
**Decision:** Root Authority derived from Trust Anchor (institutional,
charter-based).
**Rationale:** Single genesis key would just rename `authorized=True`.
**Status:** ✅ Adopted; details pending.

---

## DEC-033 — `Authority ≠ Capability`

**Phase:** P-STEP-06.1
**Decision:** Grant is proof-of-grant, not bearer token.
**Rationale:** Grant = may. Proof = did. Not same.
**Status:** ✅ Adopted.

---

## DEC-034 — AuthorityProof is Immutable

**Phase:** P-STEP-06.1
**Decision:** `AuthorityProof` referenced by `DecisionContract` is immutable.
Extension via new artifact, not modification.
**Rationale:** Historical decisions must remain reconstructible as of
issuance.
**Status:** ✅ Adopted.

---


---

## DEC-035 — Ledger / Event Model Adopted (P-STEP-06.2 v2.4)

**Phase:** P-STEP-06.2
**Decision:** The Ledger / Event Model design (P-STEP-06.2, v2.4) is adopted.

**Key claims:**
- Ledger topology = **hybrid** (linear within entity chain, DAG between decisions).
- Decision boundary = **primary-subject identity**, not time.
- `decision_id` allocated at `DECISION_INITIATED` event.
- Cross-chain events = two atomic events in one transaction.
- Event envelope with `event_class` (LIFECYCLE / RELATIONSHIP).
- `contract_ref` in `LIFECYCLE_EVENT` body points to `DecisionContract`.
- `payload_ref` = `{location_hint}` only; hash is authoritative.
- Causal edges in separate fields from informational refs.
- JCS (RFC 8785) for canonical serialization.
- Distinct domain prefixes per hash type (`ADIE:EVENT`, `ADIE:PAYLOAD`,
  `ADIE:CONTRACT`, `ADIE:EMISSION`).
- `prev_event_hash` **is included** in `event_hash`.
- Merkle construction = **RFC 6962** (Certificate Transparency), explicitly.
- Circular dependency resolved via **Solution C** (`DecisionContract` =
  content-only; fingerprint in SIBB; ref via link artifact).
- `emission_fingerprint` computed at **`DECISION_EMITTED`**; covers
  Construction + Emission segments only.
- **Content-Only Contract Principle** (§0.1): post-freeze outputs live in
  separate SIBB artifacts, never embedded in the contract.
- Multi-tenancy = one logical Ledger; `tenant_id` + `environment_id`
  mandatory on every event.
- `by_decision` returns exactly one chain (one fingerprint per decision).
- Reconstruction requires **Ledger + SIBB** (not Ledger alone).

**WORM ordering procedure (six steps, §5.5):**
1. Freeze contract content.
2. Compute `decision_contract_content_hash`.
3. Compute `emission_fingerprint`.
4. Store fingerprint in SIBB.
5. Store `contract-emission-link` in SIBB.
6. Record `DECISION_EMITTED` event with `contract_ref`.

**Documented discoveries:** 15 (see file 06 §4).

**Open questions:** OQ-06.2-1 → OQ-06.2-14 (13 questions; see file 06 §5).

**Depends on:** DEC-025, DEC-026, DEC-034.
**Supersedes:** none (first Ledger design).
**Full details:** `ADIE_MEMORY_06_P_STEP_06_2.md`.

**Rationale:**
- Fixes V1's "SDK issues claims without evidence" at the structural level.
- Provides a verifiable, offline-checkable lineage for every emitted decision.
- Names and enforces the WORM ordering — no artifact is amended.
- Lays the groundwork for P-STEP-06.3 (causal sufficiency) with explicit
  structural fields (`caused_by[]`, `required_for[]`, etc.).

**Status:** ✅ Adopted upon recording.



---

## DEC-036a — Four Questions of Decision-Causal Sufficiency

**Phase:** P-STEP-06.3 (Semantic Separation)
**Status:** ✅ Adopted.
**Related:** DCDS reclassified as **Decision-Derivation Proof Layer**
(not the framework for DCS). Framework choice deferred.

### Decision

Any causal-sufficiency claim about a Decision D MUST specify which of
the following four questions it answers:

| Q | Name | Target |
|---|---|---|
| **Q1** | Production | Why was D produced (issued)? |
| **Q2** | Justification | Why was D justified? |
| **Q3** | Authorization | Why was D authorized? |
| **Q4** | Optimality | Why was D preferred over alternatives? |

### Scope

- **Q1, Q2, Q3:** in scope for P-STEP-06.3.
- **Q4:** DEFERRED. Requires an objective function, alternatives,
  utility/regret semantics — outside the Proof-of-Claim scope.

### Consequences

1. No single causal-sufficiency claim may answer two questions at once.
2. A Decision may have different causal sets for different Q.
3. The umbrella term is **DCS**; each instance must state its Q explicitly.
4. **The unqualified term "causal sufficiency" MUST NOT be used as an
   ADIE claim.** ADIE uses **DCS** only for its project-specific,
   question-indexed notion.

### Neutral stage-wise definition of DCS

```
DCS(Q, S, D | M, C, T)
```

is a **declared claim** that the set `S` satisfies the **sufficiency
criterion** defined by:

- causal model `M`,
- causal context `C`,
- evaluation semantics `T`,
- question `Q`,

with respect to decision `D`.

**The causal model `M` is what defines** "contribution", "dependence",
"intervention", and "counterfactual" semantics. DCS itself does not
presuppose these definitions.

### Layered architecture

```
DCDS         ──► "Is D derived from S?"                 YES / NO
   │
Causal Model ──► "What does contribution/dependence mean?"  (per M)
   │
   ▼
DCS          ──► "Does S satisfy the declared sufficiency criterion?"
             ──► YES / NO / INDETERMINATE
```

DCDS is **not** the framework for DCS. DCDS is the **derivation proof
layer**.

### What This Decision Does NOT Determine

- The framework for the derivational layer — **DEC-036b** (deferred).
- The framework for the causal layer — **DEC-036c** (deferred).
- The algorithm for evaluating sufficiency — later.
- Whether Q4 is eventually adopted — later.

### Related Invariants (see file 01)

- **Invariant 17:** No causal sufficiency claim without explicit Q,
  model/version, context, evaluation semantics.
- **Invariant 18:** Never prove more causality than the declared model
  supports.
- **Invariant 19:** Corroboration ≠ causation.
- **Invariant 20:** Derivability ≠ Causal Sufficiency.
- **Invariant 21:** Computation correctness, derivation correctness, and
  causal sufficiency are distinct proof obligations.

### Related Concepts

- **DCDS** — Decision-Derivation Proof Layer. Handles "how was D
  derived?" question. **Not** the framework for DCS.
- **Causal Layer** — framework TBD. Handles "what made D the case?"
  question, operating on **derived representations**, not the
  historical record.

**Approved by:** Owner.
**Effective:** 2026-10-04.



---

## DEC-036a-4 — Partial Framework Dependence Admitted

**Phase:** P-STEP-06.3a (finding from Strategic Question S1)
**Status:** ✅ Adopted.
**Related:** P-STEP-06.3a v3.1 (proposed), §7.

### Finding

P-STEP-06.3a aimed to separate semantics from framework. The strategic
analysis (S1) concluded:

> Complete semantic separation is **impossible** for some terms.
> Specifically, three terms cannot be defined without committing to a
> framework:
>
> - **T4** (Causal Model M)
> - **T6** (Structural Causal Dependence)
> - **T7** (Instance Counterfactual Dependence)
>
> These require an explicit framework specifying:
> 1. A directed graph structure over variables.
> 2. Endogenous/exogenous partition.
> 3. Directional mapping functions.
> 4. An intervention/mutation operator.

### Consequence

- Nine terms (T1, T2, T3, T5, T8, T9, T10, T11, T12) are framework-
  independent and remain as defined in P-STEP-06.3a.
- Three terms (T4, T6, T7) are recorded as **framework-dependent**.
- Framework selection (a future decision) is therefore **not a
  downstream task**; it is a **co-requisite** for finalizing these
  three terms.

### DEC Numbering (Proposed)

| Number | Content | Status |
|---|---|---|
| DEC-035 | Ledger / Event Model | Recorded |
| DEC-036a | Four Questions of DCS | Recorded |
| DEC-036a-4 | Partial Framework Dependence | This decision |
| DEC-036b | Semantic Separation Adopted | Reserved |
| DEC-036c | Framework Selection | Deferred |
| DEC-036d | DCS Evaluation Algorithm | Deferred |

### What This Decision Does NOT Do

- Does not select a framework.
- Does not begin P-STEP-06.3b.
- Does not modify DEC-035 or DEC-036a.
- Does not authorize implementation.

### Status of the Framework Question

**Deferred.** P-STEP-06.3b is postponed pending the POC Definition
Document and its Gate 2 outcome.

**Approved by:** Owner.
**Effective:** 2026-10-04.


## Summary

| ID Range | Phase | Count |
|---|---|---|
| DEC-001 to DEC-004 | P0 | 4 |
| DEC-005 to DEC-009 | P-STEP-01 | 5 |
| DEC-010 to DEC-016 | P-STEP-03/04 | 7 |
| DEC-017 to DEC-024 | P-STEP-05 | 8 |
| DEC-025 to DEC-034 | P-STEP-06.1 | 10 |
| DEC-035 | P-STEP-06.2 | 1 |
| DEC-036a | P-STEP-06.3 | 1 |
| DEC-036a-4 | P-STEP-06.3a | 1 |
| **Total** | | **36** |

---

**End of DECISIONS.**
