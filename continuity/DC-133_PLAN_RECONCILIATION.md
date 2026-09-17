# DC-133: Plan Reconciliation — EXECUTION_PLAN.md as Sole Authority

**Date:** 2026-09-17
**Owner:** Biss
**Status:** APPROVED
**Resolves:** BLOCKER-003

---

## Context

Two plans coexisted:
- `docs/EXECUTION_PLAN.md` v2.1 — committed, dated, authoritative
- P0–P12 "ADIE Master Plan" — chat-only, never committed

Per Section 0.3 of EXECUTION_PLAN.md, tasks outside the plan must be
refused. Recent commits (3f38b49..c22619c) followed P0–P12.

---

## Decision

1. `docs/EXECUTION_PLAN.md` v2.1 remains the sole authoritative plan.

2. P0–P12 is preserved as `docs/ADIE_MASTER_PLAN.md` with status
   **PROPOSED**. It will be reconsidered as **Phase E** after the
   Phase D gate passes and EXECUTION_PLAN.md is updated to v3.0.

3. **Phase 0 is inserted BEFORE Phase A** with five tasks:
   - P0.1  Send product sentence to 20 people
   - P0.2  Run 5–10 discovery conversations
   - P0.3  Define the first client (name/role/company size/sector)
   - P0.4  External review: is current Decision contract SDK-ready?
   - P0.5  Write `docs/PRODUCT_HYPOTHESIS.md`

4. **Gate 0 requires** P0.3 to produce a single-sentence client identity.
   The value "unspecified" fails the gate. Phase A cannot begin without it.

5. **If P0.4 fails** (Decision contract judged inadequate): a refactor
   task "Phase A0" is authorized between Phase A and Phase B. This is
   exempt from Rule §0.2 because it addresses a blocking defect.

6. **Phase C timeline** is revised from 60 days to **120–150 days**
   (demo + benchmarks + external security review + 3 LOIs).

7. Commits **3f38b49..c22619c** (ADIE v2.0, CI/CD, duplicates retirement,
   GATE 0 answers) are accepted as **pre-Phase-A work**. They are
   compatible with Phase A (cleaner codebase) and Phase B (signed
   evidence is part of the SDK contract).

---

## Consequences

- Any future task not in EXECUTION_PLAN.md v2.2 (or its successor) is
  refused by default.
- The P0–P12 framework is not lost, but is frozen until Phase D.
- Phase 0 is non-negotiable: no code ships to a design partner until
  the client identity is defined.

---

## References

- `docs/EXECUTION_PLAN.md` v2.1 (will be updated to v2.2)
- `docs/ADIE_MASTER_PLAN.md` (to be created, status PROPOSED)
- `docs/BLOCKERS.md` BLOCKER-003
- Consultant review 2026-09-17 (Phase 0 recommendation)

---

**Approved by:** Biss (Owner)
**Effective:** 2026-09-17
