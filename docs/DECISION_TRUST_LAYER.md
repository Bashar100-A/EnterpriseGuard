# Decision Trust Layer -- Strategic Vision

**Status:** DRAFT -- awaiting DC-142 formalization
**Date:** 2026-09-18
**Author:** Biss (Owner)
**Related:** EXECUTION_PLAN.md, PRODUCT_HYPOTHESIS.md, DC-133

---

## 1. The Framing Shift

Prior framings of ADIE:

> "An independent control plane that records AI decisions and signs them."

That framing describes a **product**. It does not describe a **primitive**.

The revised framing:

> **"ADIE makes AI decisions portable, cryptographically bound, and
> independently verifiable -- the decision becomes a first-class object
> that can travel across systems without requiring trust in the system
> that issued it."**

This reframes the Decision itself as an architectural unit, not a
transient application event.

Historical comparison:

| Project    | Did not invent       | But invented                        |
|------------|----------------------|-------------------------------------|
| Git        | hashing              | commit as a DAG object              |
| Docker     | containers           | image as a portable artifact        |
| Kubernetes | scheduling           | pod as an atomic unit               |
| ADIE       | signatures           | Decision as a portable object       |

The claim is not "we invented cryptography". The claim is:
**we invented a new primitive in system architecture.**

---

## 2. The Problem ADIE Addresses (revised)

Today, three layers exist for trust:

- **Logs:** what happened (weak, mutable, unauthenticated)
- **Signed logs:** what happened and did not change
- **AI observability:** what the model did

None of them answer:

> **"Why was this decision made, under what authority, from what state,
> using what evidence, and can a third party verify all of that
> independently?"**

That question is the architectural gap ADIE fills.

---

## 3. The Three Paths

### Path A -- Technical Primitive: Decision Proof / Replayability

Every Decision Certificate binds:

    Decision
      -> Evidence
      -> Policy Version
      -> Authority
      -> State Snapshot
      -> Model / Rule Identity
      -> Provenance Hash
      -> Signature
      -> Timestamp

**Decision Replayability:** an independent party can take the
certificate and the permitted evidence, then reconstruct the context
that existed at decision time.

Three levels of evidence strength:

- **Audit log:** "a decision happened."
- **Signed decision:** "this decision is unchanged."
- **ADIE decision proof:** "this is the state, evidence, policy, and
  authority that produced the decision, and the relationship between
  them can be independently re-verified."

**Decision Integrity Certificate (v1 target):**

    What was decided
    Why it was decided
    Under which authority
    From which state
    Using which evidence
    Under which policy
    And whether the proof can still be independently verified.

No ZKP required in v1. Composition of hashes + signatures suffices.

### Path B -- Industry Standard: Decision Contract Protocol (DCP)

`DecisionContract` becomes more than a class inside ADIE. It becomes
an independent specification:

> **"The Decision Contract Protocol defines how consequential AI
> decisions are represented, proven, and independently verified."**

DCP v1 defines:

- Identity
- Evidence references
- Authority
- Policy version
- State reference
- Provenance
- Signature
- Lifecycle transitions
- Verification semantics
- Conformance rules

Plus a **DCP Conformance Suite**: any AI system can test itself
against the protocol.

ADIE's role becomes:
**Reference implementation + validator + SDK + specification +
conformance suite.**

This is the path to conversations with regulators and audit firms
that treat ADIE as the standard, not the vendor.

### Path C -- Category: Decision Trust Layer

ADIE does not become "a product that records AI decisions". It becomes:

> **"The trust layer for autonomous decisions."**

Any AI system -- bank, insurance, factory, hospital, SOC, autonomous
fleet, fintech, government -- can produce a **Decision Certificate**.
Any other party can verify it.

    AI System
         |
         v
    Decision
         |
         v
    ADIE Trust Layer
         |
         v
    Decision Certificate
         |
         v
    Independent Verification
         |
         v
    Auditor / Regulator / Customer / Another System

The intellectual pivot:

- **Today:** trust the system that made the decision.
- **ADIE:** do not trust the system -- verify the decision.

Positioning line:

> **"Don't trust the AI. Verify the decision."**

Extended:

> **"Don't trust the system. Verify the decision, its authority,
> its evidence, and its state."**

---

## 4. The Fourth Idea: Decision Passport

A Decision Certificate captures the proof. A **Decision Passport**
captures portability across systems.

    Decision Passport
    ----------------
    Decision ID
    Authority
    Policy
    Evidence
    State
    Provenance
    Signature
    Timestamp
    Lifecycle
    Verification status

A passport is not ADIE-proprietary. Any system can issue one. ADIE's
role becomes:

> **"The infrastructure that makes AI decisions portable and
> independently verifiable across systems."**

This is what distinguishes ADIE from SIEM/SOAR/audit products: they
keep decisions inside the perimeter; ADIE lets them travel with proof.

---

## 5. Roadmap (v1 through v6)

    V1  Signed Decision Proof
        (today -- implemented in Phase B)

    V2  Decision Replayability
        Evidence refs + state refs + replay semantics
        No ZKP

    V3  Portable Decision Passport
        Cross-system portability + verification protocol

    V4  DCP -- Decision Contract Protocol
        Open specification + conformance suite

    V5  Selective Disclosure
        Prove facts about a decision without revealing it fully
        (still no ZKP; uses hash commitments)

    V6  Zero-Knowledge Decision Proofs
        Deferred. Not a precondition. Only after v1-v5 are proven
        in production.

ZKP is a **consequence of maturity**, not a **requirement for
revolution**.

---

## 6. Alignment with EXECUTION_PLAN.md

This vision **does not violate** the current plan:

- No ZKP in v1 (Section 6 respected)
- No new blockchain (Section 6 respected)
- No new tech stack (Section 5 respected)

However, the vision **extends** the plan beyond Phase A/B/C/D. It
requires a new phase designation:

    Phase E -- Decision Trust Layer
    (after Phase D gate passes and EXECUTION_PLAN.md reaches v3.0)

Until Phase E is formally adopted, this document is **strategic
guidance**, not an executable plan.

---

## 7. What "Revolutionary" Means Here

A product is not revolutionary because it is technically novel.
It is revolutionary when:

1. It introduces a **new primitive**.
2. The primitive is **adopted** by parties outside the original team.
3. The primitive **changes behavior** at scale.

ADIE's v1 covers (1) partially. It aims at (2) and (3) through
Phase C (proof of value) and Phase E (protocol + standard).

**V1 does not claim to be revolutionary.** It claims to be the
**foundation of a primitive** that could become revolutionary if
adopted.

---

## 8. Success Metrics (revised)

Current metrics (from PRODUCT_HYPOTHESIS.md):

- 3 design partners
- 1 paying customer
- Reproducibility
- Cryptographic correctness

Vision-level metrics (for Phase E and beyond):

- N independent systems issuing Decision Certificates
- At least one regulator or audit firm referencing DCP
- At least one third-party validator (not built by ADIE)
- At least one cross-vendor interchange of Decision Passports

If none of these exist by end of Phase D, Phase E is deferred
indefinitely. The vision does not entitle us to shortcut the market.

---

## 9. Positioning (final)

Short:
> **"Don't trust the AI. Verify the decision."**

Medium:
> **"ADIE makes AI decisions portable, cryptographically bound,
> and independently verifiable."**

Long:
> **"Independent Verification Infrastructure for AI Decisions."**

---

## 10. What This Document Is Not

- Not a roadmap committed to dates.
- Not a promise of ZKP.
- Not a claim of current revolution.
- Not a replacement for Phase C.

It is a **direction**. The market decides whether it becomes a
category.

---

**End of vision document.**
**Formalization pending: DC-142 (tomorrow).**
