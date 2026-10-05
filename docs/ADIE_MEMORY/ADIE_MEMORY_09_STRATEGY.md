# ADIE — Strategic Context

**Purpose:** Commercial and strategic context behind the ADIE POC.
**Status:** Reference document.
**Related:** ADIE_MEMORY_08_POC_DEFINITION.md.

## 1. The Category ADIE Occupies

**ADIE is not a compliance product. ADIE is a Decision Integrity
Infrastructure.**

It is a layer that makes an automated decision:

- **portable** (travels as a certificate),
- **verifiable** (independent verification),
- **tamper-evident** (cryptographic binding),
- **independently inspectable** (offline verification).

This is distinct from:

- **AI Governance platforms** (Credo AI, Holistic AI) — these manage
  registration, risk, and compliance. They do not produce an
  independently verifiable decision certificate.
- **Supply-chain attestation** (Sigstore, in-toto) — these bind
  artifacts, not decisions.
- **SIEM/SOAR** — these detect and respond. They do not verify why a
  decision occurred.
- **Verifiable compute** (ZK, TEE) — these verify computation, not
  decision conditions.

ADIE is best described as: **the missing verification layer between
"we say it happened" and "here is a certificate you can check."**

## 2. Market Context (as of October 2026)

**Regulatory.**

- **DORA** (Digital Operational Resilience Act) — applicable since
  **17 January 2025** across EU financial entities.
- **EU AI Act** — phased:
  - Prohibitions: February 2025.
  - GPAI: August 2025.
  - General applicability: August 2026.
  - **High-risk Annex III (incl. creditworthiness): full application
    scheduled by December 2027** under current proposals.
- **ISO/IEC 42001** — certifiable AI management-system standard.
- **EBA** — issued explicit statements on AI risk in banking.

**Market size.**

- Gartner: AI Governance spending ~$492M in 2026, crossing $1B by 2030.
- ECB: ~3,683 credit institutions in Eurozone (May 2026).

**The window.**

The POC-relevant window is **18–24 months**, not "already enforced."

## 3. The Real Competitor

Not Credo AI. Not Splunk. Not Palantir.

**The real competitor is:**
> screenshots + PDFs + logs + manual audit trails + human testimony.

This competitor is strong (universally deployed) but has three
structural weaknesses:

1. **Fragmented** — evidence lives in 10 different systems.
2. **Trust-based** — the regulator must trust the bank.
3. **Non-portable** — cannot survive re-verification years later.

ADIE attacks these three specific weaknesses.

## 4. Target Actor

**Primary:** Internal Audit Lead, EU bank (5,000–50,000 employees).

**Adjacent decision-makers (not targets for the POC, but future buyers):**
CISO, Chief Risk Officer, Model Risk, Compliance, Legal,
Regulatory Affairs.

**Why Audit Lead first:**
- Feels DORA pressure directly.
- Controls the audit timeline.
- Owns the "evidence quality" problem.
- Has budget authority for audit tooling.

## 5. Positioning Statement

**Short:**
> "Don't trust the AI. Verify the decision."

**Medium:**
> "ADIE makes AI decisions portable, cryptographically bound, and
> independently verifiable."

**Long:**
> "Independent Verification Infrastructure for AI Decisions."

## 6. What ADIE Is NOT (positioning)

- Not an AI Governance platform.
- Not a compliance product.
- Not a dashboard.
- Not a SIEM/SOAR/XDR.
- Not an ML detector.

**ADIE is a Decision Integrity Infrastructure.**

## 7. Silent Failure Prevention

ADIE explicitly rejects "silent failure" — continuing to build for
years without external validation.

**Pre-committed Gates:**

| Gate | Criterion | Action if failed |
|---|---|---|
| **Gate 1 — Technical Truth** | POC works (TC1–TC4) | Fix, don't expand |
| **Gate 2 — Customer Truth** | 3 of 5 auditors find value | Reconsider hypothesis |
| **Gate 3 — Economic Truth** | ≥ 1 LOI or paid pilot | Reconsider market |
| **Gate 4 — Evidence of Pain** | ≥ 1 measurable metric improves | Reconsider scope |
| **Gate 5 — Repeatability** | Second actor/context works | Reconsider product |

**Rule:** No "wait and see." Every gate outcome triggers a decision.

## 8. Roadmap Priorities (post-POC)

**If Gate 2 passes:**

1. Extend POC to a second actor (e.g., Model Risk Officer).
2. Extend to a second decision type (e.g., `APPROVE_LOAN`).
3. Formalize the "independent verifier" delivery (open-source).
4. Prepare a short narrative for regulators (not a pitch deck).

**If Gate 3 passes:**

1. Build the minimal SDK around the certificate.
2. Choose one integration target (GRC platform or internal audit tool).
3. Initiate discussion with one regulatory sandbox.

**If Gate 5 passes:**

1. Consider open-sourcing the verifier as a standard artifact.
2. Consider publishing a short technical paper on DCS.
3. Evaluate commercial structure (open core, consortium, etc.).

## 9. Constraints

- **No new architectural features** during POC — architecture is
  frozen (P-STEP-06.2 as-is).
- **No framework selection** until Gate 2 passes.
- **No entity schema finalization** until Gate 3 passes.
- **No code changes** to memory files without DEC.

## 10. Metrics That Matter

- Audit preparation time (before/after).
- Manual steps count (before/after).
- Independent verifications per decision (before/after).
- "Trust this" moments (before/after).
- LOIs signed.
- Paid pilots initiated.

**Everything else is internal noise.**

---


---

## 11. Positioning vs Existing Systems

ADIE is not the first system to use signatures, hashes, or Merkle trees.
This section distinguishes ADIE from the closest systems.

### 11.1 Sigstore / cosign

**Sigstore does:** signs OCI container images, uses a transparency log
(Rekor), binds identity via OIDC.

**ADIE differs:**
- Signs **decisions**, not containers.
- No transparency log required.
- Self-contained certificate (with SIBB references).
- Multi-question (Q1/Q2/Q3 separated explicitly).

**When to use which:**
- Sigstore: "which container ran in production?"
- ADIE: "which decision was made, under what policy, by whose authority?"

### 11.2 in-toto / SLSA

**in-toto does:** records supply chain steps, links artifacts to build
steps, provides provenance for software.

**ADIE differs:**
- Records decision context, not build steps.
- No build graph.
- Policy and authority are first-class (not derived).

### 11.3 OPA / Open Policy Agent

**OPA does:** evaluates policy, produces allow/deny decisions, policy
is code.

**ADIE differs:**
- OPA is a policy engine. ADIE is a decision recorder.
- ADIE does not evaluate policy.
- ADIE produces a **portable certificate** from the evaluation.
- OPA produces logs, not portable artifacts.

### 11.4 EU AI Act Logging Tools

**They do:** capture logs, record AI decisions, produce compliance
reports.

**ADIE differs:**
- Logging tools produce **reports** (PDF, internal dashboards).
- ADIE produces **verifiable certificates** (portable, offline).
- Reports require trust in the issuer. Certificates do not.

### 11.5 Summary Table

| System | Object | Trust Model | Portable? |
|---|---|---|---|
| Sigstore | Container | Transparency log | Yes |
| in-toto | Build artifact | Attestations | Yes |
| OPA | Policy decision | Trust the engine | No |
| AI Act tools | Logs / Reports | Trust the issuer | No |
| **ADIE** | **Decision** | **Offline verification** | **Yes** |

**ADIE's unique position:** makes **decisions** portable in a way that
requires **no trust in the issuer**.


**End of Strategic Context.**
