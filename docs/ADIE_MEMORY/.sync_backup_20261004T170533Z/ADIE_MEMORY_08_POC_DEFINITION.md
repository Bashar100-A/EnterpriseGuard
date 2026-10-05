# ADIE POC — Definition Document v1.1

**Status:** v1.1 (ADOPTED)
**Supersedes:** v1 (historical, preserved as .bak_ if applicable)
**Purpose:** Define one bounded POC that tests the ADIE value
hypothesis against reality, without modifying core architecture.

**Non-purpose:**
- Not a roadmap.
- Not a specification.
- Not a pitch.
- Not a justification of ADIE.

---

## §0 — Boundary Declaration

This POC tests **one** hypothesis:

> **An independent auditor can verify the INTEGRITY of a decision
> certificate and the ISSUER'S SIGNED ASSERTIONS about its issuance
> conditions, without trusting the issuer's software after issuance.**

**What this POC does NOT test:**
- **Decision Truth** — whether the decision described in the
  certificate actually occurred.
- **Causal Claims** — whether the inputs caused the decision.
- **Model correctness.**
- **Evidence accuracy.**
- **Policy appropriateness.**

**Architecture used:** P-STEP-06.2 as frozen. No modifications.

**Key distinction (see §7):**
- **Integrity Verification:** the certificate has not been altered
  since issuance. YES (tested).
- **Issuer's Signed Assertions:** the issuer declared certain facts
  at issuance time. YES (as signed claims, not as truths).
- **Decision Truth:** the declared facts are true in the world.
  NO (not tested).

---

## §1 — Problem Statement

**Regulatory context (accurate timeline):**

- **DORA** — applicable since 17 January 2025. In force now.
- **EU AI Act** — phased application:
  - Prohibitions: February 2025.
  - GPAI: August 2025.
  - General applicability: August 2026.
  - **High-risk Annex III (incl. creditworthiness): full application
    scheduled by December 2027** under current proposals.
- **ISO/IEC 42001** — certifiable AI management-system standard.
- **EBA** — issued specific statements on AI risk in banking.

**The gap.** Current artifacts (internal logs, spreadsheets, PDF
reports) are:

- Not cryptographically bound.
- Not independently verifiable.
- Not portable across systems.
- Fragile under retrospective review.

**The specific pain.** An audit lead today spends weeks preparing a
single decision for audit — manually extracting logs, reconciling
sources, producing a report that a regulator still cannot verify
independently.

---

## §2 — Target Actor

**Role.** Internal Audit Lead, EU bank.
**Organization size.** 5,000 – 50,000 employees.
**Sector.** Banking — retail or SME lending.
**Current tools.** GRC platform, internal log system, spreadsheets,
manual report generation.

**Not the target:** CISO, AI Governance Officer, CTO.

**Why this actor.** Audit Leads feel the DORA pressure directly (DORA
is in force), anticipate the AI Act high-risk obligations (2027), and
own the "evidence quality" problem.

---

## §3 — Decision Scenario

| Field | Value |
|---|---|
| Decision type | REJECT_LOAN_APPLICATION |
| AI system | Credit scoring model v3.2 |
| Input | Loan application #L-2026-0429 |
| Policy invoked | credit-risk-policy-v3 |
| Authority | model-risk-approval-2026-Q1 |
| Decision timestamp | 2026-04-15T14:23:11Z |
| Executor | Loan origination system |

**The decision was issued automatically.** No human reviewed it.

**Six months later, internal audit needs to verify:**
- The certificate was issued by the expected system.
- The certificate has not been tampered with.
- The certificate's signed assertions match the declared policy
  and authority (as **signed claims**, not as independent truths).
- The re-verification can be performed **independently**, without
  bank cooperation.

---

## §4 — Existing Workflow

**Today (without ADIE):**
1. Auditor requests data from IT.
2. IT extracts logs into spreadsheets.
3. Auditor manually reconciles timestamps.
4. Auditor drafts a report.
5. Manager approves.
6. Report presented as PDF to regulator.

**Limitations:**
- Regulator must trust the bank's report.
- No cryptographic verification.
- Manual reconciliation.
- Re-verification 2 years later requires bank cooperation.

---

## §5 — ADIE Value Hypothesis

**If:**
- Each AI decision emits a DecisionContract with emission_fingerprint.
- The certificate + verifier + public key are delivered to the
  auditor.

**Then:**
- Audit preparation time per decision decreases.
- Trust in the certificate's **integrity** becomes independent of
  the issuer's software.
- Re-verification years later is possible without the bank's
  cooperation.

**What this hypothesis does NOT claim:**
- It does not claim the auditor can verify that the decision was
  correct or even that it occurred.
- It does not claim the policy was appropriate.
- It does not claim the model was accurate.

**Falsifiable.** Disproven if:
- 4 of 5 auditors say "no improvement."
- No measurable time reduction.
- No willingness to use or pay.

---

## §6 — Minimal Architecture

AI system
|
v
SignedIntent (caller-supplied assertion, cryptographically signed)
|
v
ADIE Core (V2 minimal)
|-- DecisionContract (structured decision content)
|-- decision_contract_content_hash
|-- emission_fingerprint (RFC 6962 Merkle root)
|-- contract-emission-link (SIBB artifact)
|
v
Delivered to auditor:
|-- certificate.json
|-- adie_public.pem
|-- verify.py
|
v
Auditor runs:
python3 verify.py certificate.json adie_public.pem
|
v
Output: VALID | INVALID (+ reason)
text


**NOT in this POC:** Causal Layer, DCS evaluation, Authority Chain
complexity, multi-tenancy, dashboard, SIBB integration (using local
content-addressed dir), signature unification.

---

## §7 — Trust Boundaries

**Three distinct levels — measured and reported SEPARATELY:**

| Level | Meaning | In POC? | How measured |
|---|---|---|---|
| Integrity Verification | Certificate not altered | YES | TC1–TC3 |
| Issuer's Signed Assertions | Issuer declared facts at issuance | YES | TC1, TC4 |
| Decision Truth | Facts are true in the world | NO | Not measured |
| Causal Claims | Inputs caused the decision | NO | Not measured |

**Trusted:**
- SHA-256.
- RSA-2048 / ECDSA-P256.
- The verifier's cryptographic operations.
- The public key (out-of-band delivery assumed).

**NOT trusted:**
- The bank (issuer).
- The ADIE server after issuance.
- The auditor's environment (verified by offline operation).

**Explicitly NOT verified:**
- Model correctness.
- Input accuracy.
- Policy appropriateness.
- Real-world occurrence of the decision.

---

## §8 — Threat Model

| # | Threat | Detected? | Mechanism |
|---|---|---|---|
| T1 | Certificate tampered | YES | event_hash chain + signature |
| T2 | Certificate forged | YES | Requires private key |
| T3 | Policy retroactively changed | YES | policy_version binding |
| T4 | Replay across decisions | YES | Nonce + timestamp |
| T5 | Model lied about output | NO | Out of scope |
| T6 | Input data was false | NO | Out of scope |
| T7 | Verifier itself malicious | PARTIAL | Verifier open-source |

**Boundary statement.** This POC detects **tampering with the
artifact**, not **falsehood in the artifact's content**. The
distinction is deliberate: it is the difference between Integrity
and Truth.

---

## §9 — Four Mandatory Test Cases

**TC1 — Valid certificate.**
- Input: valid certificate + correct public key.
- Expected: exit 0, prints "VALID".
- Pass if: output is exactly "VALID" (or equivalent).

**TC2 — Tampered certificate.**
- Input: valid certificate with one byte flipped.
- Expected: exit 1, prints specific reason.
- Pass if: detection + reason is specific and non-generic.

**TC3 — Wrong public key.**
- Input: valid certificate + wrong public key.
- Expected: exit 1, reason mentions signature mismatch.

**TC4 — Determinism of the derivation (revised).**
- Input: identical SignedIntent, fixed Evaluation Context C,
  fixed Model version Mv, fixed Policy version Pv, **fixed logical
  timestamp T**, fixed algorithm version Av.
- Expected: byte-identical decision_contract_content_hash on two
  independent runs.
- Pass if: the hash is identical.
- Note on scope: The test verifies determinism of the **content
  hash** given fixed inputs. It does NOT assume that two
  "same-intent" issuances at different wall-clock times produce
  identical emission_fingerprint. emission_fingerprint includes
  event_hash values that include timestamp and prev_event_hash.
  The determinism claim is about the **algorithm**, not the artifact
  timing.

**All four must pass. No partial success.**

---

## §10 — Independent Verification Requirements

The verifier:

- Is a **single Python file**.
- Is **< 200 lines**.
- Does **NOT** import enterpriseguard.
- Only external dependency: cryptography.
- Runs **offline**.
- Produces **deterministic output**.

**External test:** A non-ADIE developer must be able to download,
run, and correctly interpret the output in under 10 minutes without
ADIE documentation.

---

## §11 — Measurement Plan — Three Levels, Separately

**Three levels measured independently. Success at one level does NOT
imply success at another.**

### Level A — Technical Evidence

| Metric | Threshold |
|---|---|
| TC1–TC4 pass | 4/4 |
| Certificate generation time | < 1 s |
| Verification time | < 200 ms |
| Verifier line count | < 200 |
| External developer interprets output without docs | 1 test |
| Python 3.11+ on Ubuntu 22.04 | Yes |

### Level B — Customer Evidence

**Baseline** (measured before POC exposure with 3 target actors):

| Metric | How measured |
|---|---|
| Time to prepare one decision for audit | Stopwatch, end-to-end |
| Number of manual steps | Count |
| Number of "I have to trust this" moments | Self-report |
| Number of independent verifications possible | Count |

**Post-POC:** same metrics.

**Pre-committed targets:**
- >= 50% reduction in audit prep time.
- >= 80% reduction in manual steps.
- >= 1 independent verification per decision.

### Level C — Economic Evidence

| Signal | Threshold |
|---|---|
| Auditor says "I would use this" | >= 3 of 5 |
| Auditor says "I would pay for this" | >= 1 of 5 |
| Signed LOI or paid pilot offer | >= 1 |
| Specific pain reduced (concrete instance) | >= 1 |

**Customer feedback is evidence, not a vote.**

---

## §12 — Technical Acceptance Criteria

| # | Criterion | Threshold |
|---|---|---|
| TA1 | Certificate generation | < 1 s |
| TA2 | Verification | < 200 ms |
| TA3 | Determinism (per TC4) | byte-identical content hash |
| TA4 | All 4 test cases | 4/4 |
| TA5 | Verifier lines | < 200 |
| TA6 | External deps | only cryptography |
| TA7 | Python 3.11+ Ubuntu 22.04 | Yes |
| TA8 | External developer interprets output w/o docs | 1 test |

**All must pass.**

---

## §13 — Commercial Validation Criteria

**After Gate 2 (External Truth):**

| Signal | Threshold |
|---|---|
| "I would use this" | >= 3 of 5 |
| "I would pay for this" | >= 1 of 5 |
| LOI or paid pilot | >= 1 |
| Specific pain reduced | >= 1 concrete |

---

## §14 — Stop / Continue / Pivot Rules

**Pre-committed. Not to be changed after results.**

### STOP if:
- 4 of 5 auditors say "no improvement", AND
- No auditor will pay or sign LOI, AND
- No metric improves.

**Action:** Stop Report. Archive. Do not reinterpret.

### CONTINUE if:
- 3 of 5 auditors say "useful", AND
- >= 1 LOI or paid pilot, AND
- >= 1 metric improves.

**Action:** Extend to a second actor / second decision type.

### PIVOT if:
- Value surfaces in a direction different from hypothesis, OR
- A different actor surfaces as more natural user.

**Action:** Rewrite Problem Statement. Re-run Gate 2 within 4 weeks.

**No "wait and see". Every outcome triggers a decision.**

---

## §15 — What This POC Proves vs Does Not Prove

**Proves:**
- An external party can verify a certificate's integrity without
  trusting the issuer's software.
- The verifier is < 200 lines, offline, deterministic.
- Tamper detection works for three classes of tampering (TC2, TC3,
  TC4).
- A non-ADIE developer can interpret the verifier's output without
  documentation.
- Three auditors see measurable reduction (or not) in audit prep
  time.
- At least one (or zero) auditor expresses willingness to pay.

**Does NOT prove:**
- The decision actually occurred in the world.
- The AI model computed correctly.
- The input data was accurate.
- The policy was appropriate.
- The authority was meaningful outside the signed artifact.
- Anything about causal sufficiency (DCS).
- Anything about Q2, Q3, Q4.
- Anything about SIBB, Causal Layer, or future phases.

**If any reader of this document confuses the first list with the
second, the document has failed.**

---

## §16 — Status

**v1.1 is ADOPTED.** It supersedes v1 (historical, preserved as
.bak_ if applicable).

Adoption path completed:
1. Gate review (passed).
2. Owner approved.
3. v1.1 written to this file.

**End of POC Definition Document v1.1 (adopted).**
