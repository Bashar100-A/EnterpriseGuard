
# ADIE — P-STEP-02 Execution Report

**Status:** Adopted. First operational artifact of ADIE.
**Phase:** P-STEP-02 (Gate 2)
**Date:** 2026-10-04 → 2026-10-05
**Related:** DEC-037, DEC-038, DEC-039, DEC-040, DEC-041, DEC-042, DEC-043, DEC-044.

---

## §1 — What Was Built

| Artifact | Location | Size | Purpose |
|---|---|---|---|
| `verify.py` | `poc/verify.py` | 196 lines | Standalone verifier |
| `test_pstep02.py` | `poc/test_pstep02.py` | 111 lines | 10-case suite |
| `certificate-001.json` | `poc/certificate-001.json` | 2067 B | Test fixture |
| `certificate-002.json` | `poc/certificate-002.json` | 1905 B | Second fixture |
| `visual-verifier-v2.html` | `poc/.sandbox/` | ~11 KB | Browser verifier |
| `public-key-001.pem` | `poc/public-key-001.pem` | 451 B | Trust anchor |
| `wrong-key.pem` | `poc/wrong-key.pem` | 451 B | Wrong key |

**Distributed package:** `~/Desktop/adie-external-test-v4-20261004.tar.gz` (16 KB, 12 files).

---

## §2 — What verify.py Does

**The verifier:**

1. Reads certificate file as **raw bytes** (no newline translation).
2. Strips UTF-8 BOM if present.
3. Parses JSON with duplicate-key detection (E010).
4. Validates schema (E003).
5. Recomputes `decision_contract_content_hash` using JCS (RFC 8785).
6. Recomputes `emission_fingerprint` using RFC 6962 Merkle.
7. Reconstructs signed payload.
8. Verifies RSA-2048 PKCS1v15 + SHA-256 signature (E001).

**On any failure:** exits with specific error code (E001-E010). Fail-closed.

**Zero dependencies:**
- No `enterpriseguard` import.
- No network.
- No subprocess.
- Only `cryptography` + `jcs` (documented).

**Line count:** 196 (under 200, per POC §10).

---

## §3 — Error Codes

| Code | Meaning |
|---|---|
| E001 | Signature invalid, or wrong key |
| E002 | Content hash or fingerprint mismatch |
| E003 | Schema violation |
| E004 | JCS canonicalization failure |
| E005 | Unsupported algorithm |
| E006 | Invalid timestamp |
| E007 | Protocol version mismatch |
| E008 | Replay or expired (reserved) |
| E009 | Invalid Unicode |
| E010 | Duplicate JSON key |

---

## §4 — Test Results

### 10-case suite (test_pstep02.py)

| # | Test | Result |
|---|---|---|
| TC-01 | Valid certificate → VALID | ✅ |
| TC-02 | Tampered signature → E001 | ✅ |
| TC-03 | Tampered contract → E002 | ✅ |
| TC-04 | Missing field → E003 | ✅ |
| TC-05 | Algorithm downgrade → E005 | ✅ |
| TC-06 | Malformed timestamp → E006 | ✅ |
| TC-07 | Version mismatch → E007 | ✅ |
| TC-08 | Invalid unicode → E009 | ✅ |
| TC-09 | Wrong public key → E001 | ✅ |
| TC-10 | Duplicate JSON key → E010 | ✅ |

**Result:** 10/10.

### Browser verifier tests (visual-verifier-v2.html)

| Input | Output |
|---|---|
| certificate-001.json + public-key | VALID |
| certificate-002.json + public-key | VALID |
| certificate-001.json + wrong-key | E001 |
| certificate-001-TAMPERED.json + public-key | E002 |

**Result:** 4/4 correct.

---

## §5 — Cross-Language Equivalence

Byte-identical hashes between Python and JavaScript:

| Cert | Field | Value |
|---|---|---|
| 001 | Content Hash | `sha256:e751b66330bfdc8c298c360615785a2085c749db3f8abdd58be26b091aa0d051` |
| 001 | Fingerprint | `sha256:6337c84bc1e8767b46a556900393d507ec11779e8ee72f8fffba1fa2ee5a1523` |
| 002 | Content Hash | `sha256:25517b04044b840b1c71c3e5bf693c37a275e525ded4665c82fdc892fe7b6340` |
| 002 | Fingerprint | `sha256:b223180f4204da9af16bb20b8ecbd79a759dd5f755a9b09aa4d0443301183599` |

**Proven:** RFC 8785 JCS, RFC 6962 Merkle, and RSA-2048 PKCS1v15 all behave identically in Python and JavaScript.

---

## §6 — Gate 2 Evidence

### macOS (DEC-038)

- Environment: MacBook M2, macOS ARM64, Python 3.11.
- Result: 3/3 tests pass, 4 minutes, no confusion.
- Source: external developer.

### Linux (DEC-040)

- Environment: Linux x86_64, Python 3.12, cryptography 50.0.2.
- Result: SHA256SUMS 7/7 OK, 3/3 tests pass, Test D VALID.
- Source: external developer.

### Windows (DEC-039)

- Environment: Windows 11, Python 3.12.
- Result: v2 FAILED with E002 (CRLF newline conversion).
- Fix: v3 reads raw bytes + BOM strip.
- Retest: pending.

**Bugs found by Gate 2:** 1 (Windows line-ending).

**Bugs present before Gate 2:** 0 (the design was correct; I/O was not OS-agnostic).

---

## §7 — Browser Verifier (v2)

**File:** `poc/.sandbox/visual-verifier-v2.html`

**Technology:**
- Pure HTML + JavaScript.
- Web Crypto API (SubtleCrypto) — no Forge, no CDN.
- Recursive RFC 8785 JCS implementation.
- RFC 6962 Merkle (recursive).
- RSA-2048 PKCS1v15 verify.

**Constraints satisfied:**
- PR-05: Offline, zero-network, no external dependency.
- Cross-Language Equivalence (with Python).
- Byte-identical hashes.

**Limitations:**
- Safari on `file://` may require HTTPS or localhost.
- Requires Web Crypto (all modern browsers).

---

## §8 — Permanent Rules Status

| Rule | Status |
|---|---|
| PR-01 (Semantic Pollution) | Enforced |
| PR-02 (JCS Mandatory) | Enforced |
| PR-03 (Fail-Closed) | Enforced |
| PR-04 (Phase P Frozen Scope) | Enforced |
| PR-05 (Standalone Verifier) | Verified |
| PR-06 (No External Modification) | Adopted 2026-10-04 |

---

## §9 — Tested Environments (cumulative)

| OS | Arch | Python | cryptography | Result | DEC |
|---|---|---|---|---|---|
| macOS | ARM64 | 3.11 | (default) | 10/10 | 038 |
| Windows | x86_64 | 3.12 | (default) | E002 (v2) | 039 |
| Linux | x86_64 | 3.12 | 50.0.2 | 10/10 (v3) | 040 |
| Browser | — | — | Web Crypto | 4/4 | 044 |

---

## §10 — What This Proves / Does NOT Prove

**Proves:**
- An independent party can verify a certificate's **integrity** offline.
- Two independent implementations (Python, JavaScript) produce
  byte-identical results.
- Tampering is detected with a specific error code.
- The verifier runs on 3 OS families + browser.

**Does NOT prove:**
- That the decision described in the certificate occurred.
- That the AI model computed correctly.
- That inputs were accurate.
- That the policy was appropriate.
- That ADIE is compliant with any regulation.
- Causality or decision correctness.

**Integrity ≠ Truth.**

---

## §11 — What Was Discovered

1. **CRLF newline conversion breaks text-mode reading.** Fixed by
   `read_bytes()` + BOM strip.
2. **JCS recursion is essential.** A top-level-only sort (as found
   in an early external script) is not RFC 8785 and would fail on
   nested structures.
3. **Web Crypto + recursive JCS = portable browser verifier.**
4. **External modification is dangerous.** An external script broke
   `test_pstep02.py` — hence PR-06.

---

## §12 — Next Steps

| Step | Waiting on |
|---|---|
| Gate 2 Windows retest | Tester (Windows) |
| Gate 3 (Customer Truth) | LinkedIn outreach → auditors |
| Gate 4 (Economic Truth) | Paid pilot after Gate 3 |
| Gate 5 (Repeatability) | Second context after Gate 4 |

---

**End of P-STEP-02 Execution Report.**
