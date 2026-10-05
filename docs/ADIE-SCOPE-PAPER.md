# ADIE — Scope Paper

**Purpose:** One-page clarity on what ADIE does and does not do.
**Audience:** Auditors, regulators, partners, investors.
**Date:** 2026-10-05

---

## In Scope (What ADIE Does)

| Capability | What It Means |
|---|---|
| Certificate integrity | Verify the file was not altered after issuance |
| Signature verification | Confirm the issuer's signature is valid |
| Content hash binding | Confirm content matches the signed assertion |
| Merkle fingerprint | Confirm all referenced items are bound |
| Fail-closed rejection | Any tampering → specific error code (E001-E010) |
| Offline verification | No internet, no ADIE service, no vendor trust |
| Re-verification years later | Same certificate, same result |
| Cross-language parity | Python and JavaScript produce identical bytes |

---

## Out of Scope (What ADIE Does NOT Do)

| Claim | Why Not |
|---|---|
| "The decision was correct" | ADIE verifies integrity, not correctness |
| "The AI model was accurate" | Model behavior is not certified |
| "The input data was true" | Truth of inputs is not proven |
| "The policy was appropriate" | Policy selection is not certified |
| "Compliance with regulation" | ADIE is not a compliance tool |
| "Causality" | Not in current scope (P-STEP-06.3 pending) |
| "The authorization was sufficient" | Q3 is procedural, not causal |
| "Why the decision was made" | ADIE documents, it does not explain |

---

## The Boundary in One Sentence

> **ADIE is a verification layer for decision records. It proves
> integrity, not truth.**

---

## What an Auditor Sees

**ADIE provides:**

- A certificate file (JSON)
- A public key
- A verifier script (Python 196 lines, or browser HTML)

**ADIE does NOT provide:**

- The AI model
- The training data
- The policy engine
- The decision's rationale beyond declared references

---

## Correct Positioning

**Wrong:**
"ADIE proves why the decision was made."

**Right:**
"ADIE makes the decision record independently verifiable, reducing
the need to trust the issuer's records."

---

## What ADIE Replaces

| Before ADIE | With ADIE |
|---|---|
| PDF report from the bank | Certificate + verifier |
| "Trust us" | "Verify yourself" |
| Manual audit trail | Cryptographic binding |
| Re-verification requires bank | Re-verification is offline |

---

## What ADIE Does NOT Replace

- The auditor's judgment
- The regulator's review
- The bank's internal process
- The AI model
- The policy engine
- Compliance frameworks (DORA, AI Act)

---

## Contact

For questions about scope, contact the ADIE project owner.

---

**End of Scope Paper.**
