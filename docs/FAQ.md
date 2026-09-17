# EnterpriseGuard ADIE -- FAQ

Frequently asked questions. Last updated: 2026-09-17.

---

## Part 1: General Questions

### Q1. What is EnterpriseGuard ADIE?
ADIE (Autonomous Decision Governance Infrastructure) is an independent
control plane that records AI-driven decisions in an HMAC-signed,
hash-chained ledger and emits Ed25519-signed proofs. It does not execute
decisions; it governs and proves them.

### Q2. Is ADIE a SIEM, SOAR, EDR, or XDR?
No. Those tools detect and respond to threats. ADIE provides an audit
layer for decisions made by AI systems. It can integrate with them but
does not replace them.

### Q3. Do I need a blockchain?
No. ADIE uses HMAC hash-chains and Ed25519 signatures, which are
sufficient for tamper-evidence and non-repudiation. Blockchain anchoring
is available as an optional proof layer (see blockchain_anchor.py).

### Q4. Is ADIE open source?
Partially. The verifier (tools/open_verifier.py) is MIT-licensed so any
third party can independently verify chains. The core is proprietary.

### Q5. What problem does ADIE solve?
Regulators (EU AI Act Articles 12 and 14, DORA) require evidence of what
an AI system decided, why, and under whose authority. ADIE produces
that evidence as a signed, timestamped, hash-chained artifact.

---

## Part 2: Installation

### Q6. What are the system requirements?
Python 3.12+, git, and Linux or macOS. No GPU required. Windows support
is untested.

### Q7. Do I need internet access to run it?
No for core functionality. Internet is optional for: EU AI Act
blockchain anchoring, external TSA (RFC3161), and pulling updates.

### Q8. Can I run it in an air-gapped environment?
Yes. Core decision recording and verification work offline. Only the
optional blockchain anchor and RFC3161 timestamping require network.

### Q9. How do I install dependencies?
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

### Q10. How do I update to the latest version?
    git pull origin master
    pip install -r requirements.txt

Always re-run the adversarial validation suite after updating:
    python3 adie_validator.py --seed 42

### Q11. What Python version is required?
Python 3.12 or later. The code uses modern typing and dataclasses that
require 3.12+ features (match statements, PEP 695 generics).

### Q12. Is Windows supported?
Untested. Some components (audit_chain.py, hardware_identity.py) use
POSIX-specific file operations (os.replace, chmod). WSL2 works.

### Q13. Do I need root/admin privileges?
No. All tools operate in user-space. Some features (chattr +i WORM
protection) require sudo but are optional.

### Q14. Where is my data stored?
By default:
- `tools/hardware_identity.json` (chmod 0600)
- `tools/genesis_baseline.json` (chmod 0444)
- `.sibb/` for SIBB storage (chmod varies)
- `tools/activity_log.json` for audit trail
All paths are configurable via `tools/paths_config.py`.

### Q15. How much disk space does ADIE need?
~50 MB for the codebase, plus storage. Each SIBB record is typically
1-10 KB. A 1M-decision deployment needs ~10 GB.

### Q16. Can I use it in production today?
No. Phase A (documentation) is complete, but Phase B (SDK) and Phase C
(benchmarks, security review) are pending. Use for evaluation only.

### Q17. Do I need to be a cryptographer to use it?
No. The CLI hides complexity. For auditing, a basic understanding of
SHA-256 and Ed25519 helps but is not required.

### Q18. Is there a Docker image?
Not yet. A Dockerfile exists in the repo but is not published. See
`Dockerfile` and `docker-compose.yml`.

### Q19. How do I uninstall?
    rm -rf .venv .sibb
    rm -f tools/hardware_identity.json tools/genesis_baseline.json
    rm -f ~/.enterpriseguard/keys/*  # if you created any
Do NOT delete `tools/DECISIONS_LOG.md` -- it is the governance record.

### Q20. Is there a SaaS version?
Not yet. Current deployment is self-hosted (on-prem or private cloud).
A managed offering is planned for later phases.

---

## Part 3: Core Concepts

### Q21. What is a Decision Contract?
An immutable, signed record of an AI-driven decision. It contains a
decision ID, evidence references, policy ID, authority ID, and a
provenance hash. See docs/COMPONENTS/innocence_chain.md.

### Q22. What is the innocence chain?
A tamper-evident sequence of rings. Each ring hashes the previous ring,
the hardware identity, and the current state. Any modification breaks
the chain. See tools/innocence_chain.py.

### Q23. What is SIBB?
Sovereign Immutable Black Box -- a WORM (write-once-read-many) storage
layer with encryption, geographic distribution, and Shamir key sharing.
See tools/sibb_storage.py.

### Q24. What is a genesis seed?
The initial entropy source for the chain. It is generated once per
installation and stored in `tools/genesis_baseline.json` (chmod 0444).
See tools/genesis_seed.py.

### Q25. What is hardware identity?
A SHA-256 hash derived from host-specific values (machine-id, CPU info,
MAC address). It binds the chain to a physical machine. See
tools/hardware_identity.py.

### Q26. What is a provenance hash?
A SHA-256 checksum of all inputs that led to a decision. It allows
reconstruction: same inputs, same provenance hash.

### Q27. What is the difference between HMAC and Ed25519?
HMAC uses a shared secret (symmetric). Ed25519 uses public/private keys
(asymmetric). ADIE uses HMAC for chain integrity and Ed25519 for
non-repudiation (anyone with the public key can verify).

### Q28. What is a TSA?
Time-Stamp Authority -- an RFC3161 service that provides a signed
timestamp. Optional in ADIE; used for legal-grade time anchoring.

### Q29. What is the activity log?
A hash-chained JSON file (`tools/activity_log.json`) recording every
system event. Written only via `audit_chain.append_activity()`.

### Q30. What is a Decision Lifecycle?
The set of states a decision passes through: PROPOSED, VALIDATED,
AUTHORIZED, EMITTED, EXECUTED_EXTERNAL, OBSERVED, ASSESSED, CLOSED.

---

## Part 4: Usage

### Q31. How do I record a decision?
    SIBB_PASSWORD=StrongPass! python3 tools/sibb_cli.py write \
        my-decision.json --data '{"decision":"approve"}'

### Q32. How do I read it back?
    SIBB_PASSWORD=StrongPass! python3 tools/sibb_cli.py read my-decision.json

### Q33. How do I verify the chain?
    python3 tools/open_verifier.py
Expected: VALID: chain is authentic

### Q34. How do I list all records?
    SIBB_PASSWORD=StrongPass! python3 tools/sibb_cli.py list

### Q35. How do I check status?
    SIBB_PASSWORD=StrongPass! python3 tools/sibb_cli.py status

---

## Part 5: Security

### Q36. How are chains protected from tampering?
Each record hashes the previous record + hardware identity. Modifying
any record invalidates all subsequent hashes. HMAC adds a keyed layer
so even a forged rewrite is detectable.

### Q37. What happens if a private key is compromised?
You must: (1) revoke the key, (2) re-sign all active chains with a new
key, (3) record the incident in DECISIONS_LOG.md. Old chains remain
verifiable with the old public key for historical audit.

### Q38. Is the private key stored in the repo?
No. It lives at ~/.enterpriseguard/keys/private_key.pem (chmod 0600).
.gitignore excludes it. Commit history is audited to ensure it was
never leaked.

### Q39. Can an admin delete a decision?
Not silently. Deletion is not exposed. Any file removal breaks the
chain, and the activity log records all operations. Recovery requires
a new chain and a governance decision.

### Q40. How does the system prevent TOCTOU attacks?
Versioned contracts: each decision records the state version it was
made against. If the state changes before execution, the contract is
rejected (fail-closed).

### Q41. How does the system resist DoS?
Token-bucket rate limiting per decision source. Burst capacity is
configurable. Overflow is queued, not dropped.

### Q42. How are third-party AI models verified?
Static SHA-256 hash check of model files. Any change invalidates the
hash and blocks the decision. See docs/COMPONENTS/hardware_identity.md
for the pattern.

### Q43. What is the threat model?
See threat_model.md. Adversaries covered: malicious insider, external
attacker, compromised AI model, supply-chain attacker.

### Q44. Is the audit trail GDPR-compliant?
Yes, with caveats. Personal data is hashed, not stored raw. Right-to-
erasure is honored by deleting the raw data while retaining the hash.
See docs/AAAC_EU_AI_ACT_COMPLIANCE_GUIDE.md.

---

## Part 6: Compliance

### Q45. Does ADIE comply with EU AI Act Articles 12 and 14?
It provides the technical infrastructure to satisfy them: Article 12
(logging) via the innocence chain; Article 14 (human oversight) via
Decision Contract lifecycle states and approval gates.

### Q46. Does ADIE comply with DORA?
DORA requires ICT risk management and third-party oversight. ADIE's
activity log, hardware identity, and third-party AI model verification
map directly. A formal compliance matrix is at docs/DC-038_COMPLIANCE_MATRIX.md.

### Q47. Can I use ADIE for SOC 2 or ISO 27001 audits?
Yes. The audit trail and access logs are evidence-friendly. No formal
certification exists yet; work with your auditor to map the artifacts.

### Q48. How does ADIE handle the right to erasure?
Two-phase: (1) raw data is deleted, (2) the chain record is retained
with only the hash. The proof survives; the content does not.

### Q49. Where can I find the compliance policy?
    tools/compliance_policy.json
    tools/compliance_engine.py

### Q50. Is there a whitepaper or technical report?
Yes:
- docs/WHITEPAPER.md
- docs/TECHNICAL_EVIDENCE_REPORT.md
- docs/TECHNICAL_INTEGRATION_AND_COMPETITORS.md
