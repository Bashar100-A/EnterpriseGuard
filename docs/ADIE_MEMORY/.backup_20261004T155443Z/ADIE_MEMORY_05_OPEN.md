# ADIE — Open Questions & Next Steps

**Purpose:** What is unresolved, and how to continue.

---

## 1. Phase Status

| Phase | Status |
|---|---|
| P-STEP-06.1 (Authority Model) | ✅ Complete (with amendments) |
| P-STEP-06.2 (Ledger / Event Model) | 🔜 Next |
| P-STEP-06.3 (Causal Sufficiency Model) | Pending |
| P-STEP-06.4 (Transition Rules) | Pending |
| P-STEP-06.5 (Entity Schemas) | Pending |
| B.2 (Implementation) | 🚫 Not authorized |

---

## 2. Open Questions (by priority)

### Priority A — Blocking P-STEP-06.2

**AQ-1:** What is the exact structure of the Ledger event?
- Event ID
- Subject entity
- Transition
- Timestamp (which clock? logical or physical?)
- Actor
- Preconditions
- Evidence refs
- Caused_by edges
- Produces edges
- Event hash

**AQ-2:** Is the Ledger linear, DAG, or hybrid?

**AQ-3:** What is the canonical serialization for Ledger events?

**AQ-4:** How is lineage fingerprint computed?

**AQ-5:** How is a causal edge distinguished from a mere reference?

### Priority B — Blocking P-STEP-06.3

**AQ-6:** What is "causal sufficiency"? Formal definition required.

**AQ-7:** What is the acceptance test for a lineage?

**AQ-8:** How is causal inflation prevented?

### Priority C — Blocking P-STEP-06.4

**AQ-9:** Which actor is allowed to execute each transition?

**AQ-10:** How does the system prevent illegal transitions?

**AQ-11:** What is the flow from `SignedIntent ACCEPTED` → `DecisionContract DRAFTED`?

### Priority D — Open from earlier phases

**AQ-12:** Reconcile two signing systems (RSA/ECDSA + Ed25519).
**AQ-13:** Exact schema for `SignedIntent`.
**AQ-14:** Exact schema for new `DecisionContract`.
**AQ-15:** Frontend React connection to V2 API.
**AQ-16:** Fate of legacy `/v1/decisions`.
**AQ-17:** Model `Approval`.
**AQ-18:** Concrete form of Trust Anchor.

### Priority E — Longer-term

**AQ-19:** Emergence of DCP.
**AQ-20:** Migration path V1 → V2.
**AQ-21:** Design of Decision Passport (V3).
**AQ-22:** Selective disclosure without ZKP (V5).

---

## 3. Immediate Next Steps

### P-STEP-06.2 — Ledger / Event Model

**Deliverable:** Design document answering AQ-1 through AQ-5.

**Constraint:** No code. Design only.

### Then: P-STEP-06.3, .4, .5

---

## 4. Explicitly NOT to be Done

- ❌ No code changes.
- ❌ No final spec.
- ❌ No certificate issuance.
- ❌ No verifier building.
- ❌ No migration script.
- ❌ No frontend rework.

---

## 5. How to Continue in a New Conversation

1. Provide `ADIE_MEMORY_00` through `ADIE_MEMORY_05`.
2. Say: "Read in order. Continue from 05_OPEN.md."

---

## 6. Vocabulary Shortcuts

- **"reframe"** = conceptual reclassification without rename
- **"assertion"** = SignedIntent
- **"authority"** = AuthorityGrant
- **"proof"** = AuthorityProof
- **"lineage"** = reconstructible decision history
- **"causally sufficient"** = minimal explanatory set
- **"fail-closed"** = deny by default on ambiguity
- **"semantic escalation"** = value gaining meaning it doesn't earn

---

## 7. Principles Guiding Continuation

1. Truth before convenience.
2. Alignment ≠ Fitness.
3. Unknown ≠ Pass ≠ Refuted.
4. No code until design closes.
5. Every claim testable.
6. Reframe, don't destroy.
7. Causation ≠ Correlation.
8. Fail-closed on ambiguity.
9. Signature ≠ Authority. Integrity ≠ Validity.
10. Assertion ≠ Authority.

---

**End of OPEN.**
