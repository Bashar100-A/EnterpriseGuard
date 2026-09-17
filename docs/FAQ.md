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
