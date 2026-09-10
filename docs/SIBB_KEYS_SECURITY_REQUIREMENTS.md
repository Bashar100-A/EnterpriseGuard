# SIBB Key Management — Security Requirements Document (SRD)

**Project:** EnterpriseGuard ADIE  
**Component:** SIBB Key Management (`tools/sibb_keys.py`)  
**Version:** 1.1  
**Status:** Revised after expert review  
**Date:** 2026-09-08  
**Methodology:** OWASP ASVS 4.0, NIST SP 800-218, STRIDE

---

## 1. Introduction

This document defines the security requirements for the SIBB Key Management component. The component is responsible for generating, splitting, storing, reconstructing, and verifying cryptographic master keys using Shamir's Secret Sharing. It ensures that the master key is never stored in a single location and that a minimum number of shares are required for recovery.

---

## 2. Assets to Protect

| Asset | Description | Criticality |
|-------|-------------|-------------|
| **Master Key** | The root encryption/HMAC key to be protected | Critical |
| **Shares** | Pieces of the master key distributed among multiple locations | Critical |
| **Share Metadata** | Information about split (threshold, number, identifiers) | High |
| **HMAC Key** | Independent key used to authenticate shares | Critical |
| **Passwords** | User passwords used to derive encryption keys | Critical |
| **Generation Parameters** | Random salts, nonces, etc. | Medium |
| **Audit Logs** | Records of all key management operations | Medium |

---

## 3. Threat Actors

| Actor | Description | Capabilities |
|-------|-------------|--------------|
| **Local Attacker** | Unauthorized user with file system access | Read/write within limited scope, attempt to steal shares |
| **Insider Threat** | Person with legitimate access to some shares | Combine shares without authorization, tamper shares |
| **Compromised System** | Malicious process running with user privileges | Access files, intercept memory |
| **Natural Failure** | Loss or corruption of one or more shares | Partial key loss |

---

## 4. Security Properties (CIA + Non-Repudiation)

- **Confidentiality:** Shares must be encrypted at rest; without quorum, master key cannot be reconstructed.
- **Integrity:** Each share must be tamper-evident (AEAD or HMAC). Share metadata must also be integrity-protected.
- **Availability:** Tolerate loss of up to `n - threshold` shares without losing reconstruction ability.
- **Non-Repudiation:** All operations must be logged; failed attempts must be logged as well.

---

## 5. Functional Requirements (FR)

- **FR-1:** Generate a cryptographically strong master key (32 bytes for AES-256) using `secrets` or equivalent CSPRNG.
- **FR-2:** Split the master key into N shares using Shamir's Secret Sharing over a safe prime, with configurable threshold K (default N=5, K=3).
- **FR-3:** Store each share as a separate file with permissions `0600`.
- **FR-4:** Encrypt each share using an AEAD scheme (AES-256-GCM) with a unique key derived from a user password.
- **FR-5:** Reconstruct the master key from at least K valid, decrypted shares.
- **FR-6:** Verify the integrity of each share (HMAC) before decryption and use.
- **FR-7:** Reject reconstruction attempts with fewer than K shares.
- **FR-8:** Support periodic integrity verification of all shares (`verify_shares`).
- **FR-9:** Support secure deletion of a share (overwrite with zeros and remove file).
- **FR-10:** Enforce access control: only authorized users (current UID or provided password) may perform key operations.
- **FR-11:** Log every operation (success and failure) to the project audit chain via `append_activity`.

---

## 6. Security Requirements (SR)

- **SR-1:** Encryption scheme: For each share, derive a unique encryption key using HKDF from a master key derived from the user password (PBKDF2-HMAC-SHA256, minimum 12 chars, 480,000 iterations, random salt). Then encrypt the share data with AES-256-GCM using a random 12-byte nonce and store the salt, nonce, ciphertext, and tag together in the share file. The file must be protected by HMAC-SHA256 using an independent key.
- **SR-2:** The HMAC key must be 32 random bytes, stored in a separate file (`hmac_key.bin`) with permissions `0600`, outside the shares directory. It must not be derivable from the user password; if it needs to be encrypted at rest, use a separate password or OS keyring.
- **SR-3:** The master key and all intermediate keys (password-derived keys, share encryption keys) must be zeroized from memory after use. In Python, use `bytearray` and fill with zeros.
- **SR-4:** No plaintext shares or master key may be written to disk.
- **SR-5:** Use constant-time comparison (`hmac.compare_digest`) for HMAC verification.
- **SR-6:** Share metadata (threshold, number, identifiers) must be protected by HMAC or stored in the shares file and covered by the HMAC.
- **SR-7:** When a share fails integrity verification or decryption, return a generic error "Invalid share" without revealing the specific reason.
- **SR-8:** All shares must be encrypted at rest; no plaintext shares allowed.
- **SR-9:** The system must be resilient to corruption of individual shares (detected via HMAC).
- **SR-10:** The system must provide a function to verify all shares' integrity without reconstructing the key.
- **SR-11:** Temporary files used during generation or reconstruction must be created with permissions `0600` and securely deleted after use (using `os.unlink` after closing).
- **SR-12:** Access to key management functions must be restricted to the current user (or require a password). If password is used, it must be verified via a KDF before any operation.

---

## 7. Constraints and Assumptions

- **Environment:** Local filesystem storage for shares; network distribution is out of scope, but exported shares must be encrypted (e.g., using `age` or GPG).
- **Library:** Use `cryptography` for PBKDF2, HKDF, AES-GCM, and HMAC. Implement Shamir's Secret Sharing internally with `secrets` for coefficient generation and `galois` or `math` over a safe prime. If using an external Shamir library, it must be audited and pinned.
- **Password Policy:** Minimum 12 characters, no password storage, use PBKDF2 with 480,000 iterations (adjustable).
- **Performance:** Share generation and reconstruction are infrequent; performance is not critical.
- **Audit:** Integration with `append_activity` is mandatory; all operations must be logged.

---

## 8. Acceptance Criteria

- All unit tests pass (test plan to be defined).
- No High/Medium findings in Bandit.
- Successfully split and reconstruct key with K shares; reject with K-1 shares.
- Detect tampered share and refuse to use it; return generic error.
- Shares are encrypted at rest; HMAC key has 0600 permissions.
- Memory zeroization tests (where possible) pass.
- Audit log contains entries for operations.

---

## 9. Next Steps

1. **Threat Model (STRIDE)** – Map each threat to controls.
2. **Test Plan** – Define unit tests for split/reconstruct, tamper detection, encryption, access control.
3. **Code Review** – Examine existing `sibb_keys.py` if any, else write from scratch.
4. **Code Implementation** – Ensure compliance with requirements.
5. **Documentation** – Record decision (e.g., DC-124).

---

**End of Security Requirements Document (v1.1)**
