# ADIE — P-STEP-06.3a v3.1 — Semantic Separation

**Status:** v3.1 (ADOPTED — replaces v3/v0 as historical drafts)
**Supersedes:** v3 (historical, preserved as .bak_), v0
**Phase:** P-STEP-06.3a
**Depends on:** DEC-036a (Four Questions), Invariants 17–21
**Related:** DEC-036a-4 (Partial Framework Dependence — recorded)
**Next:** POC Definition Document (see file 08)

---

## §0 — Purpose

Define the vocabulary ADIE needs before choosing any causal framework.
No framework is chosen here. No implementation.

**What v3.1 corrects (vs v3):**
1. Hypothesis phrasing in §0 and §6: distinguishes Integrity from Truth.
2. §1 AI Act timeline corrected to reflect actual enforcement schedule.
3. §9 DEC numbering corrected: DEC-036b is reserved for Semantic
   Separation; DEC-036c is reserved for Framework Selection.
4. §6 Status Table: TC4 determinism flagged as needing P-STEP-06.2
   contract alignment.

---

## §1 — The Problem

"Decision-Causal Sufficiency (DCS)" was being used to cover three
distinct meanings:

1. **Derivability** — "the decision can be logically deduced from
   input set S."
2. **Justification** — "the governing policy authorizes this decision
   under the factual conditions in S."
3. **Causal sufficiency** — "the states of variables in S locked the
   outcome of the decision within a defined domain model."

These are mathematically and conceptually distinct. P-STEP-06.3a
strictly separates them.

**Context note (not part of DCS definition).**

- DORA (Digital Operational Resilience Act) is applicable since
  17 January 2025 across EU financial entities.
- The EU AI Act entered phased application: prohibitions (Feb 2025),
  GPAI (Aug 2025), general applicability (Aug 2026). **High-risk
  obligations under Annex III — which include creditworthiness
  assessment — are scheduled for full application by December 2027
  under current proposals.**
- ISO/IEC 42001 exists as a certifiable AI management-system standard.
- EBA has issued explicit statements on AI risk in banking.

**The POC-relevant window is therefore 18–24 months, not "already
enforced".** This distinction matters because it affects commercial
urgency, not the technical problem.

---

## §2 — Twelve Vocabulary Terms

### T1 — Derivation
**Definition.** A finite sequence of rule applications, each licensed
by a declared schema Σ, concluding in a decision D from a premise set S.
**Proves.** D is derivable from S under Σ.
**Does NOT prove.** S is necessary, causally sufficient, or justified.
**Q scope.** Q1, Q2, Q3.

### T2 — Justification
**Definition.** A derivation in which the concluding rules map factual
states to deontic states under a declared policy.
**Proves.** D is consistent with the declared policy's logical structure.
**Does NOT prove.** Policy applies to reality, or authority was valid.
**Q scope.** Q2.

### T3 — Authorization
**Definition.** A derivation in which terminal premises are active
AuthorityGrants and delegation events valid (T11) at time T.
**Proves.** D was issued within a valid delegation chain.
**Does NOT prove.** D was wise, causally justified, or optimal.
**Q scope.** Q3.

### T4 — Causal Model (M)  [framework-dependent]
**Definition.** A formalized, directed representation of state
transitions and structural dependencies among variables in a domain.
**Proves.** Allowed rules of causal interaction for that domain.
**Does NOT prove.** Actual factual state, or model fidelity to reality.
**Q scope.** All.

### T5 — Evaluation Context (C)
**Definition.** The recorded state of a defined variable set V at time T.
**Proves.** The factual baseline for evaluation.
**Does NOT prove.** Which variables contributed to the decision.
**Q scope.** All.

### T6 — Structural Causal Dependence  [framework-dependent]
**Definition.** e depends on e' if, under M, at least one valid mapping
of e' dictates a change in e, holding variables not dependent on e'
constant.
**Proves.** A functional directional link exists in the model.
**Does NOT prove.** The link was active or necessary in any instance C.
**Q scope.** Any.

### T7 — Instance Counterfactual Dependence  [framework-dependent]
**Definition.** D counterfactually depends on e if, in Context C,
evaluating M with e forced to an alternate valid state changes D,
holding variables not dependent on e to their states in C.
**Proves.** A counterfactual relation in a specific instance.
**Does NOT prove.** e is the only or sufficient cause.
**Q scope.** Q1, Q2, Q3.

### T8 — Decision-Causal Sufficiency (DCS)
**Definition.** DCS(Q, S, D | M, C, T) := evaluating M with S fixed to
its values in C guarantees D for all domain-valid permutations of
variables outside S.
**Proves.** S satisfies the declared sufficiency criterion.
**Does NOT prove.** M matches external physical reality.
**Q scope.** Q1, Q2, Q3.

### T9 — Derivational Necessity
**Definition.** e is derivationally necessary for D under Σ if removing
e invalidates all possible valid derivations of D from S.
**Proves.** e is non-redundant in the proof graph.
**Does NOT prove.** Counterfactual necessity or sufficiency.
**Q scope.** Q1, Q2, Q3.

### T10 — Actual Causal Contribution
**Definition.** e contributes causally to D in C if e belongs to at
least one subset S' ⊆ S such that (1) S' is DCS-sufficient for D, and
(2) e is counterfactually necessary (T7) for D within S'.
**Proves.** e is non-redundant in some sufficient subset.
**Does NOT prove.** e was the sole or global-necessary cause.
**Q scope.** Q1, Q2, Q3.

### T11 — Validity
**Definition.** An element satisfies its declared cryptographic
integrity, timestamp, and provenance conditions.
**Proves.** The element is intact and unaltered.
**Does NOT prove.** Accuracy, applicability, or sufficiency.
**Q scope.** All.

### T12 — Applicability
**Definition.** A rule, policy, or model matches the categorical
parameters of the current Context C.
**Proves.** The artifact was the correct reference for this case.
**Does NOT prove.** Inputs were valid or sufficient.
**Q scope.** Q2, Q3.

---

## §3 — Six Proof Obligations

- **O1 — Computation Correctness.** Algorithm executed per spec.
- **O2 — Derivation Correctness.** Valid derivation exists from S to D.
- **O3 — Evidence Validity.** Evidence items cryptographically intact.
- **O4 — Policy Applicability.** Policy matches categorical parameters of C.
- **O5 — Authority Validity.** Delegation chain unbroken and active.
- **O6 — Causal Sufficiency Evaluation.** DCS evaluated, yields
  YES / NO / INDETERMINATE.

---

## §4 — Three-Layer Architecture
Layer 1: Provenance & Authority -> Authenticated Context C
Layer 2: DCDS (Derivation Proof) -> YES/NO + Proof Graph
Layer 3: DCS Evaluator -> YES / NO / INDETERMINATE
Output: Decision Lineage Certificate

Layers do not share proof obligations.

---

## §5 — Invariants (Reference)

- **Invariant 17.** No causal sufficiency claim without explicit Q, M,
  C, semantics.
- **Invariant 18.** Never prove more causality than M supports.
- **Invariant 19.** Corroboration != causation.
- **Invariant 20.** Derivability != Causal Sufficiency.
- **Invariant 21.** Computation != derivation != causal sufficiency.

---

## §6 — Status Table

| Item | Category | Note |
|---|---|---|
| T1 Derivation | Resolved | Formal logic |
| T2 Justification | Provisionally resolved | Factual/deontic split |
| T3 Authorization | Provisionally resolved | Depends on T11 |
| T4 Causal Model M | Framework-dependent | See DEC-036a-4 |
| T5 Evaluation Context C | Resolved | Bounded to recorded V |
| T6 Structural Dep. | Framework-dependent | See DEC-036a-4 |
| T7 Instance Counterfac. | Framework-dependent | See DEC-036a-4 |
| T8 DCS | Provisionally resolved | Permutation-based |
| T9 Deriv. Necessity | Resolved | Proof-graph property |
| T10 Actual Contribution | Resolved | Subset-based |
| T11 Validity | Resolved | Cryptographic |
| T12 Applicability | Resolved | Categorical match |
| O1 Computation | Resolved | Algorithmic |
| O2 Derivation | Resolved | Structural |
| O3 Evidence | Resolved | Cryptographic |
| O4 Policy App. | Provisionally resolved | Categorical |
| O5 Authority | Provisionally resolved | Chain-based |
| O6 DCS Evaluation | Framework-dependent | Needs M |
| OQ-06.3a-1 Q3 counterfac. | Open | Reopened by M3-A |
| OQ-06.3a-2 Causal Primitive | Rejected | Unverifiable |
| OQ-06.3a-3 Probabilistic | Open | Needs framework |
| OQ-06.3a-4 Environment in M | Open | Needs framework |
| OQ-06.3a-5 5th Question | Open | No evidence yet |
| OQ-06.3a-6 Omissions | Provisionally resolved | Absence in C |
| OQ-06.3a-7 Contribution vs Suf. | Resolved | T10 subset of T8 |
| OQ-06.3a-8 Multiple DCS sets | Provisionally resolved | Declare proposed S |
| OQ-06.3a-9 Corroboration bd. | Open | M-dependent |
| OQ-06.3a-10 App. vs Validity | Resolved | Distinct |
| M1 T10 refinement | Resolved | Subset-based |
| M2 Primitive Causal Rel. | Rejected | Unverifiable |
| M3-A Q3 counterfactuals | Open | Under-explored |
| M3-B Multiple sets | Provisionally resolved | Declare proposed |
| M3-C Corroboration bd. | Open | M-dependent |
| TC4 Determinism test | Needs contract alignment | See file 08 POC |

**Categories:** Resolved | Provisionally resolved |
Framework-dependent | Open | Rejected | Needs contract alignment.

---

## §7 — Strategic Finding (S1)

Complete semantic separation from framework is **impossible** for some
terms. Specifically: **T4, T6, T7** cannot be defined without
committing to a framework for variables, mapping functions, and
intervention operators.

This is not a failure of P-STEP-06.3a. It is a **discovery** that:

- The framework and the semantics must develop in parallel.
- Framework selection is **not a downstream task**; it is
  **co-dependent** with the deepest semantics.

This finding is recorded as **DEC-036a-4**.

---

## §8 — What v3.1 Does NOT Decide

1. Framework M (see DEC numbering in §9).
2. Probabilistic vs deterministic formalization (OQ-06.3a-3).
3. Environmental scope of M (OQ-06.3a-4).
4. Whether Q4 is adoptable.
5. The algorithmic traversal for DCS.
6. Implementation schemas.
7. Entity model — deferred to P-STEP-06.5.
8. Any advancement of DEC-035 or DEC-036a.

---

## §9 — DEC Numbering (Confirmed)

| Number | Content | Status |
|---|---|---|
| DEC-035 | Ledger / Event Model (P-STEP-06.2) | Recorded |
| DEC-036a | Four Questions of DCS | Recorded |
| DEC-036a-4 | Partial Framework Dependence | Recorded |
| DEC-036b | Semantic Separation Adopted (this document) | Reserved |
| DEC-036c | Framework Selection (P-STEP-06.3b) | Deferred |
| DEC-036d | DCS Evaluation Algorithm (P-STEP-06.3c) | Deferred |

---

## §10 — Status

**v3.1 is ADOPTED.** It supersedes v3 and v0 as historical drafts. v3
is preserved in the backup file (`.bak_`).

Adoption path completed:
1. Gate review (passed).
2. Pre-flight check confirmed DEC numbering compatibility.
3. Owner approved.
4. v3.1 written to this file.
5. v3/v0 preserved as `.bak_` (historical).

**End of P-STEP-06.3a v3.1 (adopted).**
