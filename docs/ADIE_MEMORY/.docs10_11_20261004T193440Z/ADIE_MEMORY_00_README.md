# ADIE — Memory Index

**Purpose:** This folder contains the complete memory of the ADIE project as
of 2026-10-04. When starting a new conversation with any AI assistant, provide
these files in order (00 → 05) to restore full context.

**Last updated:** 2026-10-04
**Current phase:** P-STEP-06 (Authority Model complete; Ledger next)
**Next phase:** P-STEP-06.2 (Ledger / Event Model)

---

## Reading Order

1. **00_README.md** (this file) — orientation
2. **01_IDENTITY.md** — what ADIE is, concepts, glossary
3. **02_JOURNEY.md** — full forensic journey (P0 → P-STEP-06.1)
4. **03_DECISIONS.md** — all architectural decisions and their rationale
5. **04_DESIGN.md** — current authoritative design state
6. **05_OPEN.md** — open questions, next steps, how to continue
7. **06_P_STEP_06_2.md** — Ledger Event Model design (P-STEP-06.2)
8. **07_P_STEP_06_3A_V0.md** — Semantic Separation draft (P-STEP-06.3a v0)
9. **08_POC_DEFINITION.md** — POC Definition v1.1 (adopted)
10. **09_STRATEGY.md** — Strategic and commercial context

---

## One-Paragraph Summary

ADIE (Adaptive Defense Intelligence Engine) is a **Sovereign Reference Core**
that emits **portable, independently verifiable decisions** for AI-driven
systems. The project went through a forensic audit (P0) that revealed a
**semantic escalation** in V1: an SDK endpoint named `/v1/decisions` was
signing caller-supplied assertions with `authorized=True` without any policy
evaluation. This was documented in the design (DC-139 §D7) but never
reconciled with the API's naming. D+ (Semantic Reframing + Authority
Unification) was adopted to fix this at the architectural level, not as a
rename. The current design separates `SignedIntent` (assertion layer) from
`DecisionContract` (canonical decision layer), makes `AuthorityGrant` a
first-class entity, and defines a **Decision Lineage** as the primary trust
artifact.

---

## Status at a Glance

| Item | Status |
|---|---|
| Code changes | NONE (design only) |
| V1 status | Legacy; reframed, not deleted |
| V2 design | In progress (P-STEP-06) |
| B.2 implementation | NOT AUTHORIZED |
| Final spec | NOT YET |
| Ledger design | COMPLETE (DEC-035) |
| Semantic Separation (P-STEP-06.3a) | ADOPTED (DEC-036b) |
| POC Definition | ADOPTED (file 08) |
| POC execution | COMPLETE (DEC-037, 10/10 tests) |

---

## How to Use These Files

**For a new AI conversation:**
> "Read files `ADIE_MEMORY_00` through `ADIE_MEMORY_05` in order. Then
> continue from `05_OPEN.md`."

**For a new human contributor:**
> Read 00 → 01 → 02 first. Then 03 → 04. Leave 05 for when you're ready to
> work on next steps.

**For a review:**
> Read 02 → 03 → 04. These three contain the full reasoning chain.

**For a quick recall:**
> Read 00 (this file) + 04 (current design).

---

## Non-Negotiable Rules (as of this date)

- No code changes until decision phases complete.
- No in-place rename of legacy entities.
- Every architectural claim must be testable.
- `UNKNOWN` ≠ `PASS` ≠ `REFUTED`.
- Alignment with design ≠ Fitness for purpose.
- Signature ≠ Authority.
- Integrity ≠ Validity.
- Assertion ≠ Authority.

---

## File Versions

| File | Version | Hash (for reference) |
|---|---|---|
| 00_README | v1.0 | (self) |
| 01_IDENTITY | v1.0 | — |
| 02_JOURNEY | v1.0 | — |
| 03_DECISIONS | v1.0 | — |
| 04_DESIGN | v1.0 | — |
| 05_OPEN | v1.0 | — |
| 06_P_STEP_06_2 | v2.4 | (pending adoption as DEC-035) |
| 07_P_STEP_06_3A_V0 | v3.1 | (adopted, DEC-036b) |
| 08_POC_DEFINITION | v1.1 | (adopted) |
| 09_STRATEGY | v1.0 | (reference) |
