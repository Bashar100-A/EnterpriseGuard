# ADIE — Decision Integrity Infrastructure

**Document version:** 1.1
**Published:** 2026-10-05
**Status:** Public POC — verifier available for testing

> *Don't trust the AI. Verify the decision.*

---

## Try it now — 60 seconds, no signup

**Local verifier:** open `verify.html`
**Live verifier:** `https://bashar100-a.github.io/adie-verifier`

Files included:

1. `samples/certificate-001.json` — a signed decision certificate
2. `samples/public.pem` — the public key
3. `samples/certificate-001-TAMPERED.json` — same cert, one field modified
4. `samples/certificate-001-BADSIG.json` — same cert, signature replaced

**Do this:**

1. Drag `certificate-001.json` and `public.pem` onto the page.
2. Read: `VALID`.
3. Drag `certificate-001-TAMPERED.json` and `public.pem`.
4. Read: `INVALID: E002_HASH_MISMATCH`.
5. Drag `certificate-001-BADSIG.json` and `public.pem`.
6. Read: `INVALID: E002_HASH_MISMATCH`.

You just verified that a decision record was not altered after issuance — offline, without contacting the issuer, without trusting their software.

---

## How you know the key is the right key

A signature only proves integrity *relative to a key*. The verifier must first know the key is authentic. ADIE uses **fingerprint pinning through multiple independent channels**.

**Step 1 — Compute the fingerprint of the key you received:**

```bash
openssl pkey -pubin -in public.pem -outform DER | openssl dgst -sha256 -hex

Step 2 — Compare to the published fingerprint:
text

5df07c90c4b346277e585d2a8b20283864dfb74b526c23cda6c993fc37b942a4

Step 3 — If they match, the key is authentic. If not, stop.

The same fingerprint is:

    Embedded in every issued certificate as issuer_fingerprint.

    Displayed in the verifier UI at page load.

    Committed to the repository in PUBLIC_KEY_FINGERPRINT.txt.

Why this is enough for a POC: the fingerprint is published in a signed git commit. Tampering would require rewriting git history and every issued certificate and the verifier UI simultaneously. v1.1 will add X.509 certificate chains and Certificate Transparency log entries for full trust anchoring.
The problem — in one paragraph

Every day, AI systems in European banks reject loan applications, flag transactions, classify customers, approve transfers. These decisions are automatic. They are logged internally, exported to spreadsheets, summarized in PDFs.

Six months later, an auditor asks: "Show me decision 4291. Show me why this loan was rejected. Show me it wasn't altered since issuance."

Today's answer: Excel files, screenshots, scattered logs, and a promise. The auditor cannot verify. They must trust. Trust is not evidence.

Regulatory demand is clear and dated:

    DORA — in force since January 2025 (EUR-Lex 2022/2554).

    EU AI Act — high-risk obligations (including creditworthiness) scheduled for 2026–2027 (EUR-Lex 2024/1689), pending Digital Omnibus.

    EBA / EIOPA / ESMA — joint statement naming frontier AI models as ICT risk under DORA.

The regulatory demand exists. The technical infrastructure does not.
What ADIE is — one sentence

ADIE is a decision integrity layer. It emits portable, cryptographically signed decision certificates that any third party can verify offline — without contacting the issuer, without trusting their software, without any vendor dependency.
What we prove — and what we do not

ADIE proves:

    The certificate was issued by the holder of the private key matching issuer_fingerprint.

    No field of the certificate was altered after issuance.

    The cryptographic binding between decision hash, evidence reference, policy version, and issuance time.

    The certificate is not expired.

    Verification is possible offline, in any environment, with only a public key.

ADIE does not prove:

    That the decision was correct.

    That the AI model was accurate.

    That the input data was truthful.

    That the policy was appropriate.

    That the decision even occurred — only that it was declared and signed.

We call this Integrity ≠ Truth. It is not a weakness. It is the honest boundary that makes the product trustworthy to auditors and regulators.
What is already working

Not a slide deck. A working artifact, independently tested.

POC v1.0:

    Standalone CLI — adie-cli.py (Python).

    Browser verifier — verify.html, using Web Crypto. No installation, no server. After page load, no network.

    51 adversarial tests, 100% pass — tampered content, tampered signature, wrong key, malformed JSON, expired cert, invalid Unicode, schema violation, version mismatch, encoding attacks, cross-key attacks.

    Verified on macOS ARM64, Windows x86_64, Linux x86_64, in-browser.

    Trust anchor via fingerprint pinning.

Standards used:

    RFC 8785 (JSON Canonicalization Scheme)

    RFC 6962 (Merkle Tree — Certificate Transparency, planned)

    RSA-2048 / ECDSA-P256 signatures

    SHA-256 hashing

Engineering record:

    93,000+ lines of code across the project

    253+ passing tests

    46 architectural decisions recorded with rationale

    A formal Governance Charter with Authority Order and Ten Principles

    14 lessons learned documented after real incidents

Privacy by design

Certificates contain zero PII by default. They contain SHA-256 hashes and references. The decision record itself never leaves the issuer's boundary. This makes ADIE GDPR-compatible by construction: no personal data is processed by the verifier.

Later layers (Zero-Knowledge Disclosure) will allow verifying compliance without revealing the applicant's name, salary, or the model's weights.
How a bank issues a certificate
bash

# 1. Generate a key pair
python3 adie-cli.py keygen --out private.pem --pub public.pem

# 2. Issue a certificate for a decision
python3 adie-cli.py issue \
  --decision decision.json \
  --policy credit-risk-v3 \
  --evidence evidence.json \
  --key private.pem \
  --issuer bank.example \
  --out certificate-4291.json

# 3. Any third party verifies offline
python3 adie-cli.py verify \
  --cert certificate-4291.json \
  --pub public.pem
# → VALID

The certificate contains: version, issuer, issuer_fingerprint, issued_at, expires_at, nonce, decision_hash, policy_version, evidence_ref, signature. No decision content. No PII.
Threat model — POC v1.0
#	Threat	Mitigation	Status
T01	Certificate content altered	RFC 8785 + RSA signature	✅ Tests B01–B07
T02	Signature tampered	base64 + RSA verify	✅ Tests E01–E04
T03	Public key substitution	issuer_fingerprint bound in signature	✅ Tests C01–C04
T04	Expired certificate used	expires_at checked	✅ Tests D01–D02
T05	Bad timestamp ordering	issued_at <= expires_at	✅ Test D03
T06	Missing field	10 required fields enforced	✅ Tests F01–F05
T07	Malformed JSON	Schema validation	✅ Tests F06–F09
T08	Invalid UTF-8	Decode check	✅ Test J01
T09	Version downgrade	version == 1.0	✅ Test B08
T10	Replay of old certificate	nonce + expires_at	⚠️ Partial — no server-side nonce registry in POC
T11	Compromised signing key	—	❌ Planned for v1.1 (revocation endpoint)
T12	GitHub compromise (trust anchor)	Multiple fingerprint channels	⚠️ Partial — planned v1.1 (X.509 + CT log)
T13	Issuer repudiates certificate	Non-repudiable signature	⚠️ Partial — planned v1.1 (HSM)
T14	Verifier software tampered	196 LOC, open source, reviewable	⚠️ Partial — planned v1.1 (reproducible build)

Full model: THREAT_MODEL.md.
What we are not

    Not a SIEM. We do not detect or respond.

    Not a SOAR. We do not execute.

    Not an XDR. We do not monitor networks.

    Not a policy engine. We do not evaluate rules.

    Not a blockchain. We do not require distributed consensus for verification.

    Not a truth oracle. We prove integrity, not correctness.

We are a verification layer for decision records. One layer. Done well.
Competition and adjacent standards

The incumbent is not a product. It is current practice: Excel files, screenshots, and trust. Universally deployed, structurally broken.

Adjacent alternatives:
Alternative	What it offers	Why ADIE differs
Immutable logs (WORM)	Tamper-resistant storage	No offline third-party verification
Timestamping services (RFC 3161)	Trusted time	Proves time, not the decision
Sigstore / in-toto	Software supply chain signing	Not designed for AI decisions
AI governance platforms	Policy, dashboards	Not a verification layer
C2PA	Media provenance	Not for decisions
ADIE	Offline, third-party, no-vendor verification	Built on RFC 8785 + RFC 6962

We build on these standards. We do not reinvent them.
Vision — Not Yet Built

The POC proves the primitive. Four layers are planned. None are implemented today.

Layer 1 — Verifiable Compliance Proof (VCP).
Binding the certificate not only to the decision, but to what produced it: model hash, data commitment, policy version, authority chain, execution proof.

Layer 2 — Zero-Knowledge Disclosure.
A verifier in Frankfurt confirms that a decision on a Moroccan loan application complied with credit-risk-policy-v3, without seeing the applicant's name, salary, or the model's weights.

Layer 3 — Hardware-Backed Execution.
Issuance keys move to HSM. Execution moves to confidential computing (Intel TDX / AMD SEV-SNP). The certificate attests not only to the identity of the model, but to the fact that it ran as declared.

Layer 4 — Cross-Institutional Consortium.
A bank in one jurisdiction issues a certificate. An auditor in another verifies it without intermediary.

Endpoint: independent verification infrastructure for AI decisions — as foundational as HTTPS for transport, JWT for identity.
Who this is for

Primary buyer: Internal Audit Lead, EU bank (5,000–50,000 employees). The person who, when a regulator asks "prove your AI was safe yesterday", currently has no answer.

Adjacent roles: Chief Risk Officer · Model Risk Officer · Head of AI Governance · CISO with DORA obligations · External auditors · Regulators.

Not for: Teams looking for a dashboard. Teams looking for a policy engine. Teams looking for an AI governance platform.
What you buy today vs what is planned

Today (POC v1.0): a verification primitive — CLI, browser verifier, trust anchor via fingerprint pinning, 51 adversarial tests passing.

Planned (v1.1+): X.509 trust chain, revocation endpoint, server-side nonce registry, HSM-backed issuance, reproducible build with checksum.

Later (v2.0+): VCP, ZK disclosure, hardware attestation, cross-institutional consortium.
Reproduce the tests
bash

git clone https://github.com/Bashar100-A/EnterpriseGuard.git
cd EnterpriseGuard
python3 tests/adversarial/run_all.py
# → TOTAL: 51 | PASS: 51 | FAIL: 0

What we ask

If you are an auditor: Try the 60-second demo. Tell us whether the certificate is useful in your workflow. We are not selling. We are listening.

If you are a regulator: We would like 20 minutes to show what we have built and hear what an auditable AI decision should look like from your side.

If you are a journalist: Full access to the code, certificates, tests, and boundary conditions.

If you are a potential partner: We are looking for one institution willing to try a 14-day pilot on a single decision type. No integration required.

If you are an investor: We are not raising yet. We will when the primitive is validated externally.
Contact

Repository: https://github.com/Bashar100-A/EnterpriseGuard
Local verifier: verify.html
Email: adie-contact@proton.me

"Don't trust the AI. Verify the decision."
