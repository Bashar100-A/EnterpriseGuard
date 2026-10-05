# ADIE — Comprehensive Overview (v3)

**Version:** 3.0
**Date:** 2026-10-05
**Purpose:** Full project description for someone who knows nothing.
**Supersedes:** v2 (which had 3 documented gaps now closed).

---

## 1. What ADIE Is — In Three Sentences

ADIE issues **verifiable decision certificates** for AI-driven
decisions.

Any third party can verify a certificate **offline**, **without
trusting the issuer**, and **without internet**.

The goal: transform a decision from "we say it happened" into "here is
a file anyone can verify independently."

---

## 2. The Problem It Solves

### 2.1 The Problem

In EU banks today, AI systems make consequential decisions (loan
rejection, risk classification, account freezing). After 6 months,
regulators ask: "prove why this decision was made."

The current answer is: internal logs, PDF reports, human testimony.
All depend on trusting the institution.

**The gap:** no technical standard exists for producing decision
evidence that a third party can verify independently.

### 2.2 Why Now

- **DORA** (Digital Operational Resilience Act): applicable since
  17 January 2025.
- **EU AI Act**: phased application.
  - Prohibitions: February 2025
  - GPAI: August 2025
  - General applicability: August 2026
  - High-risk Annex III (incl. creditworthiness): **full application
    scheduled by December 2027** under current proposals.
- **EBA**: explicit statements on AI risk in banking.

The window is **18–24 months**, not "already enforced."

---

## 3. The Central Idea

### 3.1 Example

**Without ADIE:**
```
Bank: "Decision D-123 was made under policy P-7 with authority A-3"
Auditor: "How do I verify?"
Bank: "Trust us"
```

**With ADIE:**
```
Bank: "Decision D-123 + certificate-123.json + public key + verifier"
Auditor: runs verifier → VALID
         No trust required.
         No internet required.
         No contact with bank required.
```

### 3.2 Core Principles

**Portable certificate.** Small JSON file (2 KB).

**Independent verification.** 196-line Python script. No ADIE package.
Works offline.

**Signature proves integrity only.** It proves the file was not
modified. It does NOT prove the decision was correct.

**This distinction is called: `Integrity ≠ Truth`.**

---

## 4. What Distinguishes ADIE

### 4.1 Epistemic Honesty

ADIE does not claim what it cannot prove. It does not say "the
decision was correct." It says "the decision has not changed."

### 4.2 Strict Semantic Separation

Four questions are separated explicitly:

| Q | Question |
|---|---|
| Q1 | Why was the decision **produced**? |
| Q2 | Why was the decision **justified**? |
| Q3 | Why was the decision **authorized**? |
| Q4 | Why was the decision **optimal**? (deferred) |

Each certificate carries a `Q` tag. **Q1, Q2, Q3 are never conflated.**

**Note on Q3:** Authorization is a **procedural claim**. It proves the
authority was delegated digitally and exercised correctly. It does
**NOT** prove the authorization was causally sufficient for the
decision.

### 4.3 Fail-Closed

Any error → specific rejection code (E001–E010). No silent acceptance.

| Code | Meaning |
|---|---|
| E001 | Signature invalid |
| E002 | Content hash mismatch |
| E003 | Schema violation |
| E004 | JCS canonicalization failure |
| E005 | Unsupported algorithm |
| E006 | Invalid timestamp |
| E007 | Version mismatch |
| E008 | Reserved (replay / expired) |
| E009 | Invalid Unicode |
| E010 | Duplicate JSON key |

### 4.4 Zero-Network Paths (Clarified)

The phrase "no external dependency" must be qualified.

| Path | Dependencies | Truly Zero? |
|---|---|---|
| Python verifier | `cryptography` + `jcs` (2 packages) | **No** |
| Browser verifier | Web Crypto (native to browser) | **Yes** |

**Path A (Python):** standard libraries, audit-friendly, widely used.

**Path B (Browser):** single HTML file (~11 KB). Web Crypto is part of
every modern browser. JCS implemented manually (~50 lines of JS).
**Zero CDN. Zero network. Zero external dependencies.**

Both paths produce **byte-identical results** (proven — DEC-042).

### 4.5 Cross-Language Equivalence

Python and JavaScript produce **byte-identical hashes**:

```
certificate-001 Content Hash:
sha256:e751b66330bfdc8c298c360615785a2085c749db3f8abdd58be26b091aa0d051
    Python = JavaScript

Fingerprint:
sha256:6337c84bc1e8767b46a556900393d507ec11779e8ee72f8fffba1fa2ee5a1523
    Python = JavaScript
```

Most "portable certificate" projects fail on cross-language
canonicalization. ADIE does not.

---

## 5. How It Works

### 5.1 Issuance

1. Freeze contract content.
2. Compute `content_hash` using JCS (RFC 8785).
3. Compute `emission_fingerprint` using RFC 6962 Merkle tree.
4. Store fingerprint in SIBB (WORM storage).
5. Store `contract-emission-link` in SIBB (no contract modification).
6. Emit `DECISION_EMITTED` event with `contract_ref`.

**Nothing is amended after writing.**

### 5.2 Verification

1. Read file as **raw bytes** (no newline translation).
2. Strip UTF-8 BOM if present.
3. Parse JSON with duplicate-key detection.
4. Validate schema.
5. Recompute `content_hash` via JCS.
6. Recompute `emission_fingerprint`.
7. Reconstruct signed payload.
8. Verify RSA-2048 signature.
9. Output `VALID` or `INVALID: E0XX`.

### 5.3 What's In the Certificate

The certificate contains **references**, not the full evidence:

- `content_hash` (32 bytes)
- `emission_fingerprint` (32 bytes)
- `referenced_event_hashes[]` (hashes only)
- `referenced_evidence_hashes[]` (hashes only)

**Full evidence lives in SIBB**, not in the certificate. An auditor
with SIBB access can reconstruct the full lineage.

---

## 6. Technical Standards

### 6.1 RFC 8785 (JCS)

JSON Canonicalization Scheme. Same JSON → same bytes.

### 6.2 RFC 6962 (Merkle Tree)

Certificate Transparency style. Supports selective disclosure later.

### 6.3 RSA-2048 PKCS#1 v1.5 + SHA-256

Deterministic. Universally supported.

### 6.4 WORM Ordering (6 steps)

```
1. Freeze contract content
2. Compute content_hash
3. Compute emission_fingerprint
4. Store fingerprint in SIBB
5. Store contract-emission-link in SIBB
6. Emit DECISION_EMITTED event
```

No artifact is amended. Each written once.

---

## 7. What Was Built

### 7.1 Files in `poc/`

| File | Size | Purpose |
|---|---|---|
| `verify.py` | 196 lines | Main verifier |
| `test_pstep02.py` | 111 lines | 10-case suite |
| `certificate-001.json` | 2067 B | Test fixture |
| `certificate-002.json` | 1905 B | Second fixture |
| `visual-verifier-v2.html` | ~11 KB | Browser verifier |
| `public-key-001.pem` | 451 B | Trust anchor |
| `wrong-key.pem` | 451 B | Wrong key for testing |

### 7.2 Distribution Package

`adie-external-test-v4-20261004.tar.gz` (16 KB, 12 files).

### 7.3 Test Results

- **Python suite:** 10/10.
- **Browser suite:** 4/4.

### 7.4 OS Coverage

| OS | Arch | Python | Result |
|---|---|---|---|
| macOS | ARM64 | 3.11 | ✅ 10/10 |
| Linux | x86_64 | 3.12 | ✅ 10/10 |
| Windows | x86_64 | 3.12 | Bug found, fixed |
| Browser | — | Web Crypto | ✅ 4/4 |

---

## 8. What ADIE Proves and Does NOT Prove

### 8.1 Proves

- The certificate **has not been altered** since issuance.
- The signature is **valid** for the holder of the private key.
- The signed content **matches** what is shown.
- Re-verification is possible **years later**.
- Verification works **offline**.

### 8.2 Does NOT Prove

- The decision was **correct**.
- The AI model was **accurate**.
- Inputs were **true**.
- The policy was **appropriate**.
- Compliance with any regulation.
- Causality.
- That the authorization (Q3) was causally sufficient.

### 8.3 Core Rule

```
Integrity ≠ Truth.
Derivability ≠ Causality.
Signature ≠ Authority.
```


---

## 9. Positioning vs Existing Systems

ADIE is not the first system to use signatures, hashes, or Merkle
trees. This section distinguishes ADIE from the closest systems.

### 9.1 Sigstore / cosign

Sigstore does: signs containers, uses Rekor transparency log.

ADIE differs: signs decisions, not containers. Self-contained
certificate. Multi-question.

### 9.2 in-toto / SLSA

in-toto does: supply chain provenance.

ADIE differs: records decision context, not build steps.

### 9.3 OPA / Open Policy Agent

OPA does: evaluates policy (engine).

ADIE differs: OPA is a policy engine. ADIE is a decision recorder.
OPA produces logs; ADIE produces portable certificates.

### 9.4 EU AI Act Logging Tools

They do: logs, compliance reports.

ADIE differs: reports require trust in the issuer. Certificates
do not.

### 9.5 Summary Table

| System | Object | Trust Model | Portable? |
|---|---|---|---|
| Sigstore | Container | Transparency log | Yes |
| in-toto | Build artifact | Attestations | Yes |
| OPA | Policy decision | Trust the engine | No |
| AI Act tools | Logs / Reports | Trust the issuer | No |
| ADIE | Decision | Offline verification | Yes |

---

## 10. Strategic Structure

### 10.1 Silent Failure Prevention

Silent failure is the enemy, not declared failure.

Gates:

1. Gate 1: POC works.
2. Gate 2: External independent verification.
3. Gate 3: Real auditor finds value.
4. Gate 4: Auditor pays (Paid Pilot).
5. Gate 5: Second context adopts.

No "wait and see." Every gate outcome triggers a decision.

### 10.2 Current Status

- Gate 1: Complete.
- Gate 2: macOS + Linux. Windows retest pending.
- Gate 3: Ready to begin (LinkedIn outreach).

---

## 11. What ADIE Does NOT Do

- Does not execute security actions.
- Does not calculate risk.
- Does not make decisions.
- Is not a Dashboard.
- Is not SIEM / SOAR / XDR.
- Is not a replacement for AI governance platforms.

ADIE = Decision Integrity Infrastructure. Nothing more.


---


---

## 12. Key Management

### 12.1 Current POC

Single RSA-2048 key pair. Public key delivered out-of-band.

### 12.2 Gap Acknowledged

- No key rotation.
- No revocation.
- No CA hierarchy.
- No Trust Anchor beyond a single public key.

### 12.3 Production Design (Proposed)

Three-tier hierarchy:

    Trust Anchor (institution)
            |
            v
    Issuer Root Key (long-lived, offline, HSM)
            |
            v
    Issuer Operational Key (shorter-lived, online)
            |
            v
    Decision Certificates

Rules:
- Keys are never deleted. Historical verification requires them.
- Rotation scheduled + forced on compromise.
- Old keys become ARCHIVED - usable for verification, not issuance.

### 12.4 What We Tell Auditors

"The POC uses a single public key as the Trust Anchor. We deliver it
out-of-band. Key rotation and revocation are documented as production
requirements but are not implemented in the POC. If you need them,
tell us - that feedback determines our next priority."

### 12.5 Reference

Full design: ADIE_MEMORY_14_KEY_MANAGEMENT.md.

---

## 13. Documentation

The project maintains 14 memory files in docs/ADIE_MEMORY/:

| # | File |
|---|---|
| 00 | README |
| 01 | IDENTITY |
| 02 | JOURNEY |
| 03 | DECISIONS (46) |
| 04 | DESIGN |
| 05 | OPEN |
| 06 | P-STEP-06.2 (Ledger) |
| 07 | P-STEP-06.3a (Semantic Separation) |
| 08 | POC Definition |
| 09 | Strategy |
| 10 | Pre-Audit Blueprint |
| 11 | Paid Pilot Draft |
| 12 | Gate 3 Playbook |
| 13 | P-STEP-02 Execution |
| 14 | Key Management |

---

## 14. How to Test - Fast Track

### 14.1 Prerequisites

    pip install cryptography jcs

### 14.2 Steps

    tar xzf adie-external-test-v4-20261004.tar.gz
    cd external-test

    # Verify file integrity
    sha256sum -c SHA256SUMS

    # Test A: valid certificate
    python3 verify.py certificate-001.json public-key-001.pem
    # Expected: VALID

    # Test B: wrong key
    python3 verify.py certificate-001.json wrong-key.pem
    # Expected: INVALID: E001_SIGNATURE_INVALID

    # Test C: full suite
    python3 test_pstep02.py
    # Expected: Results: 10/10 passed

### 14.3 Browser Path

Open visual-verifier-v2.html. Drag two files. Click "Verify".

Expected: VALID.


## 15. FAQ

"Is this blockchain?"
No. RSA-2048 signature + RFC 6962 Merkle tree. No blockchain.

"Does it use AI?"
No. It records decisions made by other systems. ADIE itself does
not use AI.

"Does it replace human audit?"
No. It gives the auditor a tool. The audit decision remains human.

"What about key management?"
See section 12. Documented gap. Production design proposed.

"How is this different from Sigstore?"
See section 9.1. Sigstore signs containers; ADIE signs decisions.

"Is it a standard yet?"
No. A standards path (W3C / IETF) is deferred until after Gate 5.

"What does the certificate contain?"
References, not evidence. See section 5.3.

"How big is a real certificate?"
Roughly the same size (about 2 KB), regardless of evidence volume.
Because it holds hashes, not content.

---

## 16. Conclusion

ADIE gives institutions a tool to produce independently verifiable
evidence that a decision was issued under declared conditions -
without requiring trust in the issuing institution.

Not blockchain. Not AI. Not SaaS. Not a Dashboard.

It is infrastructure.

Works offline. Open to verification. Claims only what it can prove.

---

## Appendix A - What Was Closed in v3

This version closes three gaps identified by external review:

1. Key management - documented in section 12 and File 14.
2. Positioning vs existing systems - section 9.
3. Clarification of "no external dependency" - section 4.4.

---

End of Overview v3.
