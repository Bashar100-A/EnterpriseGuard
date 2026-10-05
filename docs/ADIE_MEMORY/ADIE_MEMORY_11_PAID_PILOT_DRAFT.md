# ADIE — Paid Pilot Draft (Phase P-STEP-05)

**Status:** DRAFT — not for external distribution yet.
**Purpose:** Define a minimal, measurable pilot to be offered after
Gate 2 (External Developer Test) passes.
**Constraint:** No promises of regulatory compliance. No causality
claims. Integrity verification only.

---

## §0 — What This Is / Is Not

**This is:**
- A framework for a bounded, paid pilot.
- A measurement instrument for a single decision type.
- A way to test Customer Truth (Gate 3) and Economic Truth
  (Gate 4) in one motion.

**This is NOT:**
- A sales pitch.
- A claim of compliance with DORA, AI Act, ISO/IEC 42001, or any
  regulation.
- A commitment to unlimited scope.
- A claim that ADIE "proves" decisions are correct.

---

## §1 — Target Client (Hypothesis)

**Primary:** Internal Audit Lead, EU bank (5,000 - 50,000 employees).
**Alternative:** Model Risk Officer at the same institution.

**Why this actor:**
- DORA is applicable now.
- Feels evidence-quality pain directly.
- Has budget authority for audit tooling.
- Controls the audit timeline.

**Reject for pilot:** CISO, AI Governance Officer, CTO, external
regulator (as primary contact).

---

## §2 — The Single Decision Type to Measure

**Pre-commit to one:**
REJECT_LOAN_APPLICATION by a credit scoring model, issued under a
declared policy, with no human review.

**Alternative (if rejected):**
APPROVE_LOAN_APPLICATION for the same model.

**Rejected for pilot:** Multiple decision types, model training,
model changes, policy changes during the pilot.

---

## §3 — Baseline Measurement (Before ADIE)

**Duration:** 7 consecutive business days.

**Who measures:** The client (Audit Lead or delegate), not us.

**Instrument:** Stopwatch + simple spreadsheet.

**Metrics (per decision):**

| # | Metric | How measured |
|---|---|---|
| M1 | Time to prepare decision for audit | Stopwatch, end-to-end |
| M2 | Number of manual steps | Count of distinct actions |
| M3 | Number of "trust this" moments | Self-report, per decision |
| M4 | Number of independent verifications possible | Count of verifiable artifacts |

**Sample:** At least 5 decisions, from the same decision type,
within the baseline window.

**Deliverable:** A signed note from the client with the four numbers.

---

## §4 — Pilot Deployment (Minimal)

**What we deliver:**
- A standalone verifier (verify.py, ~180 lines).
- Public key, out-of-band.
- A certificate for each of the pilot decisions.
- A 1-page guide for the Audit Lead.

**What we do NOT deliver:**
- No cloud.
- No integration with the bank's systems.
- No database.
- No continuous operation.
- No production deployment.

**Duration:** 7 consecutive business days after deployment.

**Cost to us:** Near-zero (no hosting, no ops).

---

## §5 — Post-Measurement

**Same instrument, same metrics:**

| # | Metric | Target |
|---|---|---|
| M1 | Audit prep time per decision | >= 40% reduction (conservative) |
| M2 | Manual steps | >= 60% reduction |
| M3 | "Trust this" moments | >= 1 reduction |
| M4 | Independent verifications | >= 1 per decision (up from 0) |

**Additional qualitative signals:**
- Auditor says "I would use this in my next audit" (yes/no).
- Auditor says "I would pay for this" (yes/no).
- Auditor names one specific pain that was reduced.

**Deliverable:** Same signed note, comparing before vs after.

---

## §6 — Success Criteria (Pre-Committed)

**The pilot is judged as:**

| Outcome | Criteria |
|---|---|
| SUCCESS | M1, M2, M3, M4 all met, AND client says "would use" |
| PARTIAL | 2 of 4 met, OR client hesitates on "would use" |
| FAIL | < 2 met, OR client says "no improvement" |

**No interpretation after the fact.** The numbers decide, not the
narrative.

---

## §7 — Scope Limits (Hard)

- **One decision type** for the entire pilot.
- **One client** for the entire pilot.
- **7 business days** baseline + 7 business days post.
- **5 decisions** minimum.
- **No code changes** to the verifier during the pilot.
- **No new features** to ADIE during the pilot.

If the client asks for more, we say: "Pilot scope is fixed.
We can discuss expansion after the pilot succeeds."

---

## §8 — Commercial Terms (Framework Only)

**We do not set prices in this draft.**

**We define two commercial options for negotiation:**

### Option A — Fixed-Fee Pilot

- One-time fee for the 14-day pilot.
- No success fee.
- No exclusivity.
- Deliverable: the signed measurement note.

### Option B — Contingent Pilot

- Lower base fee.
- Additional fee if M1-M4 targets are met.
- Deliverable: same as Option A.

**Both options are intentionally vague here.** Real numbers come
after Gate 3 (Customer Truth) reveals actual willingness to pay.

---

## §9 — Exit Conditions

**We stop the pilot if:**

- Client requests scope changes beyond §7.
- Client asks for claims we cannot make (compliance, causality,
  decision correctness).
- Client asks for integration with their production systems.
- Any party attempts to alter the pre-committed metrics.

**We complete the pilot if:**

- Metrics are measured as agreed.
- The signed note is delivered.
- Payment (if any) is processed.

---

## §10 — What This Pilot Proves / Does Not Prove

**Proves:**
- Whether the verifier provides measurable improvement in audit
  preparation time.
- Whether an auditor finds the certificate useful in practice.
- Whether the auditor expresses willingness to pay.
- Whether the four metrics we chose are the right metrics.

**Does NOT prove:**
- That the decision was correct.
- That the model was correct.
- That the inputs were accurate.
- That the policy was appropriate.
- That ADIE is compliant with any regulation.
- That ADIE is production-ready.
- That ADIE has product-market fit.

**If any reader of this document confuses the first list with the
second, the document has failed.**

---

## §11 — Deliverable After Pilot

Two artifacts:

1. **Signed measurement note** from the client (before/after numbers).
2. **Our internal memo** — what we learned, what surprised us, what
   we will change.

The client sees #1. We use #2 to decide Gate 4 (Economic Truth).

---

## §12 — Next Steps After Pilot

| Outcome | Next |
|---|---|
| SUCCESS + willing to pay | Begin Gate 4 discussions; consider a second pilot. |
| SUCCESS + no payment | Ask why. Reconsider market. |
| PARTIAL | Fix the specific metric that failed; re-run. |
| FAIL | Stop. Write a Stop Report. Reconsider hypothesis. |

**No "wait and see." Every outcome triggers a decision.**

---

**End of Paid Pilot Draft.**
