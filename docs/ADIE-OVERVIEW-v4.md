# ADIE — Comprehensive Overview (v4)

**Version:** 4.0
**Date:** 2026-10-05
**Purpose:** Full project description for someone who knows nothing.
**Supersedes:** v3 (with correction clarifications and legal section).

---

## 1. What ADIE Is — In Three Sentences

ADIE issues **verifiable decision certificates** for AI-driven
decisions.

Any third party can verify a certificate **offline**, **without
trusting the issuer's records**, and **without internet**.

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

**Important note on Q3:** Authorization is a **procedural claim**.
The certificate records what the issuer **asserts** about delegation.
It does **NOT** prove:
- that the delegation was appropriate
- that the authority was exercised wisely
- that the authorization was causally sufficient for the decision

Q3 is a procedural record, not a causal proof. Do not present it as
more than it is.

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

**Full evidence lives in SIBB**, not in the certificate.

**Important:** This means the certificate's **integrity** can be
verified independently (offline, no SIBB). But the **full context**
(evidence, delegation chain, events) requires **SIBB access**.

If SIBB is under the issuer's control, then full context verification
is **not fully independent** of the issuer. Integrity verification
remains independent; context verification does not.

This distinction is deliberate and is not hidden.

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
Size grows linearly with the number of referenced hashes. Each
hash is 71 bytes. A certificate with 100 references is ~9 KB; 1000
is ~90 KB. A future optimization (Merkle root over references) could
make size constant regardless of count.

---

## 16. Conclusion

ADIE gives institutions a tool to produce independently verifiable
evidence that a decision was issued under declared conditions -
without requiring trust in the issuing institution.

Not blockchain. Not AI. Not SaaS. Not a Dashboard.

It is infrastructure.

Works offline. Open to verification. Claims only what it can prove.

---

## 17. Known Limitations (Honest Inventory)

This section lists every limitation we are aware of. None is hidden.

### 17.1 Trust Anchor Distribution

**Limitation:** The public key must be delivered out-of-band. The user
must trust that this key belongs to the issuer.

**What is displaced, not eliminated:** Trust moves from "trust the
issuer's records" to "trust the issuer's key distribution."

**Mitigation:** A future CA hierarchy + transparency log would reduce
this. Not implemented in POC.

**Status:** Documented. Production design in File 14.

### 17.2 SIBB Dependency for Full Context

**Limitation:** The certificate holds references (hashes), not
evidence. Full context requires SIBB access.

**What is not independent:** If SIBB is under the issuer's control,
full context verification is not fully independent of the issuer.

**What IS independent:** Certificate integrity verification (offline,
no SIBB needed).

**Mitigation:** SIBB could be operated by a third party, or replicated
across institutions.

**Status:** Documented in §5.3.

### 17.3 No Trusted Timestamp

**Limitation:** The certificate has an `issued_at` field, but no TSA
(RFC 3161) or external transparency log binds that timestamp
cryptographically.

**What is not proven:** That the certificate was issued at the
declared time.

**Risk:** Replay of an older certificate is theoretically possible
without a timestamp anchor.

**Error code reserved:** E008. Not implemented.

**Mitigation:** A future RFC 3161 TSA integration would close this.

**Status:** Design deferred. Feedback from Gate 3 determines priority.

### 17.4 Key Management Not Implemented

**Limitation:** Single RSA-2048 key. No rotation. No revocation. No
CA hierarchy.

**What is not supported:** Key lifecycle operations.

**What is documented:** Production design in File 14.

**Status:** POC adequate for Gate 3; not adequate for production.

### 17.5 Q3 Is Procedural, Not Causal

**Limitation:** Q3 (Authorization) proves the issuer **asserts** a
valid delegation. It does NOT prove the delegation was causally
sufficient for the decision.

**Why it matters:** Do not present Q3 as causal proof.

**Status:** Emphasized in §4.2.

### 17.6 JCS Browser Implementation

**Limitation:** The JavaScript implementation of RFC 8785 (JCS) is
about 50 lines, hand-written. It has been tested against two
certificates.

**What is not yet done:** Systematic testing against RFC 8785 official
test vectors (numbers, Unicode, edge cases).

**Risk:** A JCS divergence on unusual inputs would break
cross-language equivalence.

**Mitigation:** RFC 8785 publishes test vectors. We will add a
conformance test before production use.

**Status:** Planned. Test addition prioritized.

### 17.7 Certificate Size Grows

**Limitation:** Size grows linearly with the number of referenced
hashes (71 bytes per hash).

**What was corrected:** The earlier claim "~2 KB always" was wrong.

**Mitigation:** A Merkle root over references would make size
constant, regardless of count. Not implemented.

**Status:** Documented in §15.

### 17.8 Algorithm Choice

**Limitation:** RSA-2048 PKCS#1 v1.5 is older than modern
alternatives (Ed25519, RSA-PSS).

**Why chosen:** Universal compatibility. Web Crypto support. Determinism.

**Not a bug:** A compatibility decision, not an error.

**Future:** Ed25519 or RSA-PSS as an optional profile. Not before
Gate 3.

**Status:** Deferred.

### 17.9 No Transparency Log

**Limitation:** There is no public append-only log that would let
third parties detect if a certificate was issued.

**What this means:** There is no global visibility into what the
issuer has emitted.

**Mitigation:** A future integration with a transparency log (like
Certificate Transparency's Rekor) would add this. Not implemented.

**Status:** Out of scope for POC.

### 17.10 Standards Path Deferred

**Limitation:** ADIE is not a standard. No IETF/W3C submission yet.

**Why deferred:** Standards require at least two independent
production implementations. We have one (ADIE) plus a reference
implementation (TypeScript).

**Path:** After Gate 5 (second context adoption), a standards
submission becomes viable.

**Status:** Explicitly deferred. Documented in §9.5.

---

### 17.11 GDPR / Privacy

**Limitation:** ADIE certificates may contain hashes of personal data.
Under GDPR, even hashes can be considered personal data if
re-identification is feasible.

**What ADIE does not do:**
- No pseudonymization strategy.
- No data minimization analysis.
- No DSAR (Data Subject Access Request) procedure.
- No retention policy.

**Why it matters:** A banking decision certificate references the
subject (loan applicant). The certificate must be handled according
to GDPR.

**Mitigation (to be designed):**
- Hash salt + key management to prevent cross-referencing.
- Retention policy for certificates.
- DSAR workflow (certificate deletion vs immutability tension).
- DPIA (Data Protection Impact Assessment) before production.

**Status:** Not addressed. Documented as gap.

### 17.12 eIDAS / Legal Weight

**Limitation:** ADIE certificates are technical attestations, not
legal signatures under eIDAS (EU Regulation 910/2014).

**What ADIE provides:** cryptographic integrity + signer identity.

**What ADIE does NOT provide:**
- Qualified Electronic Signature (QES) status.
- Qualified Timestamp.
- Legal weight recognized across EU member states.

**Why it matters:** A regulator may reject a certificate as legal
evidence if it lacks QES/QTS.

**Mitigation:**
- Integration with Qualified Trust Service Providers (QTSPs).
- RFC 3161 timestamp from qualified TSA.
- Legal review of evidentiary weight.

**Status:** Design not started. Not a technical gap but a legal one.

**Positioning clarification:** ADIE is a technical attestation layer.
Legal qualification requires additional services.

### 17.13 Threat Model

**Limitation:** No explicit threat model is documented.

**What is implicitly addressed:**
- Malicious modification → detected (E001-E010).
- Wrong key → detected (E001).
- Malformed JSON → detected (E003, E009, E010).

**What is NOT addressed:**
- **Malicious issuer:** ADIE does not detect if the issuer lies
  about the decision content. Certificate binds assertions, not truth.
- **Compromised private key:** No detection mechanism post-compromise.
- **SIBB tampering:** If SIBB is under issuer control, no protection.
- **Collusion:** Issuer + SIBB operator could fabricate evidence.
- **Insider threat:** No mechanism beyond signature.

**Why it matters:** A threat model clarifies what ADIE protects
against and what it does not.

**Mitigation:** A separate threat model document will be produced
after Gate 3 (informed by auditor feedback).

**Status:** Acknowledged. Not yet written.


---

## 17.14 Summary Table

| # | Limitation | Severity | Status |
|---|---|---|---|
| 1 | Trust anchor distribution | Medium | Documented |
| 2 | SIBB dependency | Medium | Documented |
| 3 | No TSA | High | Deferred |
| 4 | Key management | High | Designed |
| 5 | Q3 procedural | Info | Documented |
| 6 | JCS browser testing | Medium | Planned |
| 7 | Certificate size | Low | Documented |
| 8 | Algorithm choice | Low | Deferred |
| 9 | No transparency log | Medium | Out of scope |
| 10 | Standards path | Info | Deferred |
| 11 | GDPR / Privacy | High | Gap |
| 12 | eIDAS / Legal | High | Gap |
| 13 | Threat Model | High | Acknowledged |

**Every limitation is public. Every limitation has a mitigation path.**

---


---

## 18. Threat Model (Summary)

Detailed threat modeling will follow after Gate 3. This section
provides the current view.

### 18.1 What ADIE Protects Against

| Threat | Detection |
|---|---|
| Certificate modified after issuance | E002_HASH_MISMATCH |
| Signature tampered | E001_SIGNATURE_INVALID |
| Wrong public key used | E001_SIGNATURE_INVALID |
| Policy version changed retroactively | E007_VERSION_MISMATCH |
| Timestamp malformed | E006_TIMESTAMP_INVALID |
| Duplicate JSON key injection | E010_JSON_DUPLICATE_KEY |
| Invalid Unicode | E009_UNICODE_INVALID |
| Algorithm downgrade | E005_ALG_UNSUPPORTED |

### 18.2 What ADIE Does NOT Protect Against

| Threat | Why |
|---|---|
| Malicious issuer lying about decision | ADIE binds assertions, not truth |
| Compromised private key | No post-compromise detection |
| SIBB tampering by operator | No SIBB-independent verification |
| Collusion between issuer and SIBB | Out of scope |
| Insider threat | Signature only |
| Replay with forged timestamp | No TSA (see 17.3) |

### 18.3 Trust Assumptions

ADIE assumes:

1. **SHA-256 is collision-resistant** (accepted assumption).
2. **RSA-2048 PKCS1v15 is secure** (accepted assumption).
3. **The public key belongs to the claimed issuer** (see 17.1).
4. **The verifier is not compromised** (open-source, readable).
5. **The operating system is not compromised** (out of scope).

### 18.4 Attackers Considered

| Attacker | In Scope? |
|---|---|
| External network attacker | Yes (integrity) |
| Certificate modifier | Yes (integrity) |
| Malicious auditor | Partial (can't fake validity) |
| Malicious issuer | No (assertion truth) |
| Colluding issuer + SIBB | No |
| Nation-state with key compromise | No |

### 18.5 What an Auditor Should Ask

1. Who controls the private key?
2. Where is SIBB hosted?
3. Who can read/write SIBB?
4. Is there a transparency log?
5. How is the public key distributed?

**Answers to these questions are part of the audit, not part of
ADIE's guarantee.**

---

## 19. Legal and Privacy Notes

### 19.1 What ADIE Is, Legally

**ADIE is:**
- A technical attestation layer.
- A verification tool.
- A cryptographic proof of integrity.

**ADIE is NOT:**
- A legal signature under eIDAS.
- A qualified electronic seal.
- A substitute for legal evidence rules.

### 19.2 Positioning for Legal Use

ADIE produces a **technical artifact** that may be used as **supporting
evidence**. Its legal weight depends on:

- Applicable jurisdiction.
- Whether a QES/QTS is required.
- Whether the regulator accepts technical attestation.

### 19.3 GDPR Considerations

**Risk:** Hashes of personal data may be considered personal data
under GDPR if re-identification is possible.

**Required actions before production:**
1. Data Protection Impact Assessment (DPIA).
2. Pseudonymization strategy (salt + key management).
3. Retention policy for certificates.
4. Data Subject Access Request (DSAR) procedure.
5. Legal review of cross-border data flows.

### 19.4 Recommended Language

When presenting to legal teams, use:

> "ADIE provides a technical integrity verification layer. It is
> intended to support, not replace, legal evidentiary processes."

Do NOT say:

> "ADIE proves the decision was made."
> "ADIE is legally binding."
> "ADIE guarantees compliance."

### 19.5 Path to Legal Acceptance

1. **Today:** Technical POC.
2. **After Gate 3:** Real auditor feedback on usefulness.
3. **After Gate 4:** Paid pilot validates economic value.
4. **Then:** Legal review with a QTSP partner.
5. **Eventually:** Standardization (W3C/IETF/CEN).

**No shortcut. No overclaim.**

---

## Appendix A
 - What Was Closed in v3

This version closes three gaps identified by external review:

1. Key management - documented in section 12 and File 14.
2. Positioning vs existing systems - section 9.
3. Clarification of "no external dependency" - section 4.4.

---

End of Overview v4.




---

## Appendix B - Corrections Applied in v4

v4 applies four corrections based on external review:

1. **Language precision (§1):** "without trusting the issuer" replaced
   with "without trusting the issuer's records". The issuer is not
   entirely untrusted; only their records are verified independently.

2. **SIBB dependency clarified (§5.3):** The certificate's integrity
   can be verified offline. Full context requires SIBB. If SIBB is
   under issuer control, full context verification is not fully
   independent.

3. **Certificate size claim corrected (§15):** Size grows linearly
   with the number of referenced hashes.

4. **Q3 emphasized as procedural (§4.2):** Stronger language on what
   Q3 does NOT prove.

Original v3 preserved in repository history.

---

**End of Overview v4.**
