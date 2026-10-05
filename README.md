# ADIE — Decision Integrity Infrastructure

**Version:** 1.0 | **Published:** 2026-10-05 | **Status:** Public POC

> *Don't trust the AI. Verify the decision.*

---

## Try it now — 60 seconds, no signup

**Verifier:** [`verify.html`](verify.html)

1. Drag `certificate-001.json` + `keys/adie-v1/public.pem` onto the page.
2. Read: `VALID`.
3. Drag `certificate-001-TAMPERED.json` + same public key.
4. Read: `INVALID: E002_HASH_MISMATCH`.

Verified offline. No issuer contact. No trust in their software.

---

## How you know the key is the right key

A signature only proves integrity *relative to a key*. The verifier must first know the key is authentic.

**Step 1 — Compute fingerprint of the key you received:**
```bash
openssl pkey -pubin -in public.pem -outform DER | openssl dgst -sha256 -hex
```

**Step 2 — Compare to the published fingerprint:**
```
5df07c90c4b346277e585d2a8b20283864dfb74b526c23cda6c993fc37b942a4
```

**Step 3 — If they match, the key is authentic. If not, stop.**

The same fingerprint is:
- Embedded in every certificate as `issuer_fingerprint`.
- Displayed in the verifier UI at page load.
- Committed in [`PUBLIC_KEY_FINGERPRINT.txt`](PUBLIC_KEY_FINGERPRINT.txt).

**Why this is enough for a POC:** the fingerprint is published in a signed git commit. Tampering would require rewriting git history *and* every certificate *and* the verifier UI.

See [THREAT_MODEL.md](THREAT_MODEL.md) for the full model.

---

## The problem

Every day, AI systems in European banks reject loans, flag transactions, classify customers. Six months later an auditor asks: *"Show me decision 4291. Show me it wasn't altered since issuance."*

Today's answer: **Excel, screenshots, scattered logs, and a promise.** The auditor cannot verify. They must trust. Trust is not evidence.

**Regulatory demand is clear and dated:**
- **DORA** — in force since Jan 2025 ([EUR-Lex 2022/2554](https://eur-lex.europa.eu/eli/reg/2022/2554/oj)).
- **EU AI Act** — high-risk obligations 2026–2027 ([EUR-Lex 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj)).
- **EBA / EIOPA / ESMA** — joint statement on frontier AI models as ICT risk under DORA.

The demand exists. The infrastructure does not.

---

## What ADIE is

**ADIE is a decision integrity layer. It emits portable, cryptographically signed decision certificates that any third party can verify offline — without contacting the issuer, without trusting their software, without any vendor dependency.**

---

## What we prove — and what we do not

**ADIE proves:**
- Certificate issued by holder of the private key matching `issuer_fingerprint`.
- No field altered after issuance.
- Cryptographic binding between decision, evidence ref, policy version, issuance time.
- Verification possible offline, with only a public key.

**ADIE does not prove:**
- Decision was correct.
- Model was accurate.
- Input data was truthful.
- Policy was appropriate.
- Decision even occurred — only that it was declared and signed.

We call this **Integrity ≠ Truth**. It is the honest boundary.

---

## What is already working

**POC v1.0:**
- Standalone verifier — `adie-cli.py` (Python).
- **Browser verifier** using Web Crypto (`verify.html`) — no install, no server.
- **51 adversarial tests, 100% pass.**
- Verified on macOS ARM64, Windows x86_64, Linux x86_64, in-browser.
- **Trust anchor** via fingerprint pinning.

**Standards:**
- RFC 8785 (JSON Canonicalization)
- RFC 6962 (Merkle Tree — planned)
- RSA-2048 / ECDSA-P256, SHA-256

---

## What we are not

- **Not SIEM.** No detect/respond.
- **Not SOAR.** No execute.
- **Not XDR.** No network monitor.
- **Not a policy engine.** No rule evaluation.
- **Not a blockchain.** No consensus.
- **Not a truth oracle.** Integrity, not correctness.

**One layer. Verification for decision records. Done well.**

---

## Vision — Not Yet Built

1. **Verifiable Compliance Proof** — model hash, data commitment, execution proof.
2. **Zero-Knowledge Disclosure** — compliance without PII.
3. **Hardware-Backed Execution** — HSM, confidential computing.
4. **Cross-Institutional Consortium** — issuer in one jurisdiction, verifier in another.

---

## How a bank issues a certificate

```bash
python3 adie-cli.py keygen --out private.pem --pub public.pem
python3 adie-cli.py issue \
  --decision decision.json \
  --policy credit-risk-v3 \
  --evidence evidence.json \
  --key private.pem \
  --issuer bank.example \
  --out certificate-4291.json
python3 adie-cli.py verify \
  --cert certificate-4291.json \
  --pub public.pem
# → VALID
```

---

## Reproduce the tests

```bash
git clone https://github.com/Bashar100-A/EnterpriseGuard.git
cd EnterpriseGuard
python3 tests/adversarial/run_all.py
# → TOTAL: 51 | PASS: 51 | FAIL: 0
```

---

## Contact

**Repository:** `https://github.com/Bashar100-A/EnterpriseGuard`
**Verifier:** [`verify.html`](verify.html)
**Email:** `adie-contact@proton.me`

---

**"Don't trust the AI. Verify the decision."**
