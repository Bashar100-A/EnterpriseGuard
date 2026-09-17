# EnterpriseGuard ADIE — Product Hypothesis

**Date:** 2026-09-17
**Status:** DRAFT — based on Phase 0 signals (S1-S4)
**Purpose:** Formalize the market hypothesis before Phase A begins

---

## The Hypothesis (one sentence)

**Financial institutions in the EU need a cryptographic, independent audit
layer for AI-driven decisions — because regulators (EU AI Act, DORA) now
demand continuous, reconstructable evidence of what the AI decided, why,
and under whose authority — and no existing tool provides this as an
independent control plane.**

---

## Evidence Base (Phase 0 Signals)

### S1 — Big-4 Reports (5/5 verified)
- **Deloitte (2025-06):** Audit committees must validate AI in internal
  controls, especially black-box models.
- **PwC (2025-10):** 87% of executives expect autonomous AI agents to
  reshape governance; 50% cite operationalizing governance at scale as
  their top hurdle.
- **EY (2025-06):** 72% of organizations scaled AI, only 33% have
  responsible AI controls in place.
- **KPMG/Melbourne (2025-05):** 66% of employees rely on AI outputs
  without evaluating accuracy.
- **McKinsey (2025-11):** Scaled AI impact is stalled by agentic AI
  control gaps.

**Finding:** Regulatory and board-level pressure on AI governance is
documented across all Big-4 firms. The gap between AI deployment and
governance maturity is quantified and public.

### S2 — AI Governance Jobs (3/20 verified)
- N26 (Berlin) — Cloud & AI Governance Manager
- N26 (Berlin) — ICT GRC Senior Manager
- Robinhood (Luxembourg) — ICT Risk Oversight Lead

**Finding:** EU financial institutions are actively hiring dedicated AI
governance roles in 2026. Demand exists at the operational level.

### S3 — Public Statements (3/3 verified)
- **r/GRC (2026-08):** "If a regulator asked you to prove your AI was safe
  yesterday... what would you show them?"
- **r/Compliance (2026-05):** "What does audit-defensible evidence of AI
  judgment competency actually look like in practice?"
- **r/SaaS (2026-03):** "The audit layer has to be independent of the model
  — sitting below it, not inside it."

**Finding:** Practitioners explicitly ask for what ADIE provides:
continuous, independent, cryptographic decision evidence.

### S4 — RFPs and Regulatory Signals (2/2 verified)
- **EU AI Office (2025-04):** €9M tender for AI safety technical
  assistance, including GPAI compliance monitoring.
- **EBA/EIOPA/ESMA (2026-07):** Joint statement demanding governance and
  third-party oversight for frontier AI models under DORA.

**Finding:** EU regulators are themselves procuring technical
infrastructure for AI compliance, and are jointly calling for DORA-aligned
AI governance.

---

## Target Customer (working definition)

**Primary segment:**
EU financial institution (bank, insurer, or fintech), 50–500 employees,
subject to DORA and EU AI Act, currently deploying or planning AI in
credit, fraud, AML, or customer-facing agents.

**Buyer role (initial hypothesis):**
GRC Lead, CISO, or Head of AI Governance — the person held accountable
when a regulator asks "prove your AI was safe yesterday."

**Why this segment first:**
- Regulatory deadline pressure (DORA 2025, EU AI Act 2026+)
- Budget exists
- Decision cycle is shorter than for 5000+ enterprise
- Pilot scope is manageable

---

## The Problem (as validated)

Financial institutions cannot produce **continuous, independent,
audit-defensible evidence** of:
1. What the AI decided
2. Why it decided it (rationale, evidence, policy)
3. Under whose authority
4. What the alternatives were
5. Whether the decision is still valid today (not 6 months ago)

Existing tools (SIEM, SOAR, EDR, LLM observability) provide logs and
traces, not cryptographically signed decision records.

---

## The Solution (ADIE positioning)

**ADIE** is an independent control plane that:
- Intercepts AI decisions before execution
- Produces Ed25519-signed, hash-chained decision records
- Provides third-party verifiability (public key only)
- Runs independently of the AI model (below, not inside)
- Never executes the decision itself

**Differentiation:** Cryptographic evidence, not logs.
**Target category:** Decision audit layer, not monitoring tool.

---

## Why Now (regulatory timing)

- **DORA:** in force since 2025-01-17 — financial entities must manage
  ICT risk, including AI-driven systems.
- **EU AI Act:** high-risk obligations phasing in through 2026-2027;
  Articles 12 (logging) and 14 (human oversight) already applicable.
- **EBA/EIOPA/ESMA:** 2026 joint statement explicitly naming frontier AI
  as an ICT risk requiring governance.

---

## Open Questions (must be answered before Phase B)

1. **Who is the first named buyer?** (not yet identified)
2. **What is the price point?** (subscription? per-decision? enterprise license?)
3. **Is SaaS acceptable, or on-prem required by BFSI buyers?**
4. **What is the minimum viable integration** (LLM API? agent framework? custom?)
5. **Does the buyer want a full product, or an SDK + verifier?**

---

## Success Criteria for Phase A (documentation phase)

By end of Phase A, the following must be true:
- 20 components documented (`docs/COMPONENTS/`)
- QUICKSTART works in <10 minutes
- 5 recipes written
- FAQ with ≥50 questions
- Product hypothesis tested against at least 3 informal conversations

If a single real buyer cannot be named after Phase A, Phase B is
postponed until market discovery completes.

---

## References

- `docs/P0_SIGNALS/S1_BIG4_REPORTS.md`
- `docs/P0_SIGNALS/S2_AI_GOVERNANCE_JOBS.csv`
- `docs/P0_SIGNALS/S3_CISO_POSTS.md`
- `docs/P0_SIGNALS/S4_RFPS.md`
- `docs/EXECUTION_PLAN.md`
- `continuity/DC-133_PLAN_RECONCILIATION.md`
