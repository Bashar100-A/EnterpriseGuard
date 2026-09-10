# SIBB Key Management — Threat Model (STRIDE)

**Project:** EnterpriseGuard ADIE  
**Component:** SIBB Key Management (`tools/sibb_keys.py`)  
**Version:** 1.1  
**Date:** 2026-09-08  
**Reference:** Security Requirements Document v1.2

---

## 1. Introduction

This threat model analyzes potential threats against the SIBB Key Management component using the STRIDE methodology (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege). It is aligned with SRD v1.2 and addresses the gaps identified in the previous version.

---

## 2. Assets

| Asset ID | Asset |
|----------|-------|
| A1 | Master Key |
| A2 | Shares (encrypted) |
| A3 | Share Metadata |
| A4 | HMAC Key |
| A5 | User Passwords |
| A6 | Generation Parameters (salts, nonces) |
| A7 | Audit Logs |

---

## 3. Threat Actors

| Actor ID | Actor |
|----------|-------|
| T1 | Local Attacker |
| T2 | Insider Threat |
| T3 | Compromised System |
| T4 | Natural Failure |

---

## 4. STRIDE Analysis

### 4.1 Spoofing (S)

| Threat | Asset | Scenario | Controls (FR/SR) | Status |
|--------|-------|----------|------------------|--------|
| S-1: Spoofed share file | A2 | Attacker replaces a valid share with a fake one to disrupt reconstruction or gain information | FR-6, SR-1, SR-5, SR-7 | HMAC verification detects; generic error returned |
| S-2: Spoofed HMAC key | A4 | Attacker replaces HMAC key to bypass integrity checks | SR-2 (including fingerprint verification) | HMAC key stored outside shares dir with 0600; fingerprint stored separately to detect replacement |
| S-3: Spoofed metadata | A3 | Attacker modifies metadata (threshold, identifiers) to affect share handling | SR-6 (metadata included in HMAC-protected share file) | Metadata is part of share file and protected |

### 4.2 Tampering (T)

| Threat | Asset | Scenario | Controls | Status |
|--------|-------|----------|----------|--------|
| T-1: Tampered share ciphertext | A2 | Attacker modifies encrypted share data | SR-1 (AEAD AES-GCM), SR-5 | Tag verification fails; share rejected |
| T-2: Tampered share HMAC | A2 | Attacker modifies HMAC to match tampered data | SR-2 (HMAC key independent) | Needs HMAC key; if key is compromised, additional measures needed |
| T-3: Tampered HMAC key | A4 | Attacker alters HMAC key file to control integrity | SR-2 (fingerprint stored) | Detection via fingerprint mismatch; system alerts |
| T-4: Tampered metadata | A3 | Attacker changes split threshold or identifiers | SR-6 | Integrity protected |
| T-5: Tampered password-derived key parameters | A6 | Attacker changes salt/iterations to weaken derivation | SR-1 (parameters stored inside HMAC-protected share) | Protected together with share |

### 4.3 Repudiation (R)

| Threat | Asset | Scenario | Controls | Status |
|--------|-------|----------|----------|--------|
| R-1: Deny performing key split | A1, A2 | User denies generating shares | FR-11 (mandatory audit) | Audit log |
| R-2: Deny reconstruction attempt | A1 | User denies attempting to reconstruct master key | FR-11 | Audit log |
| R-3: Deny deleting a share | A2 | User denies deleting a share | FR-9, FR-11 | Secure deletion logged |

### 4.4 Information Disclosure (I)

| Threat | Asset | Scenario | Controls | Status |
|--------|-------|----------|----------|--------|
| I-1: Read plaintext shares from disk | A2 | If shares not encrypted, attacker can read them | SR-8 (encrypted at rest) | AES-GCM encryption |
| I-2: Read master key from memory | A1 | Attacker dumps process memory to extract key | SR-3 (zeroization) | Use bytearray and overwrite; best effort in Python |
| I-3: Read HMAC key | A4 | Attacker reads HMAC key file to forge shares | SR-2 (0600, outside shares dir) | File permissions; outside shares dir |
| I-4: Extract password from memory or logs | A5 | Attacker gets password from memory dump or log file | SR-3, SR-12 | No password logging; zeroization |
| I-5: Leak generation parameters | A6 | Salt/nonce may be exposed, but they are not secret | SR-1 | Not critical; uniqueness matters |

### 4.5 Denial of Service (DoS)

| Threat | Asset | Scenario | Controls | Status |
|--------|-------|----------|----------|--------|
| D-1: Delete or corrupt shares | A2 | Attacker deletes enough shares to prevent reconstruction | FR-5 (threshold), FR-7, availability strategy (future) | Need backup/replication; otherwise master key lost |
| D-2: Lock file or resource exhaustion | A1, A2 | Attacker fills disk or holds locks | (not yet in SRD) | Add resource limits later |
| D-3: Modify metadata to invalidate shares | A3 | Change threshold to impossible value | SR-6 | Integrity protects |
| D-4: Repeated failed reconstruction attempts | A1 | Attacker attempts many wrong passwords causing resource exhaustion | FR-10, SR-12 (lockout) | Implement temporary lockout after N failures |

### 4.6 Elevation of Privilege (E)

| Threat | Asset | Scenario | Controls | Status |
|--------|-------|----------|----------|--------|
| E-1: Local attacker gains root to read all files | A1, A2, A4 | Root can bypass permissions and read encrypted shares, HMAC key, memory | SR-2, SR-8, HSM recommended | Encryption helps, but root can access memory; HSM recommended |
| E-2: Exploit TOCTOU in file operations | A2 | Race condition between checking share file and using it | SR-5, SR-6, use O_NOFOLLOW | Atomic reads and verification |
| E-3: Malicious process with same UID | A1, A2 | If process runs as same user, it can read/write shares | FR-10, SR-12 | Password verification required; separate user recommended |
| E-4: Code tampering | All | Attacker modifies `sibb_keys.py` to leak secrets | Code signing, integrity checks | Must sign code and verify before execution (future) |
| E-5: Side-channel attacks on Shamir | A1 | Timing leakage during share generation/reconstruction | Use constant-time operations | Implement constant-time Shamir if possible |
| E-6: Replay of old shares | A2 | Attacker reuses shares from previous key to confuse reconstruction | Use unique key ID (UUID) per master key | Incorporate key ID into share structure |

---

## 5. Mapping Threats to Requirements (Updated)

| Threat ID | Mitigated by FR/SR | Priority |
|-----------|-------------------|----------|
| S-1 | FR-6, SR-1, SR-5, SR-7 | High |
| S-2 | SR-2 (fingerprint) | High |
| S-3 | SR-6 | High |
| T-1 | SR-1, SR-5 | High |
| T-2 | SR-2 | High |
| T-3 | SR-2 (fingerprint) | High |
| T-4 | SR-6 | High |
| T-5 | SR-1 | High |
| R-1, R-2, R-3 | FR-11 | High (mandatory) |
| I-1 | SR-8 | High |
| I-2, I-4 | SR-3 | High |
| I-3 | SR-2 | High |
| D-1 | FR-5, FR-7, availability | High |
| D-2 | Resource limits (future) | Medium |
| D-3 | SR-6 | High |
| D-4 | FR-10, SR-12 | High |
| E-1 | SR-2, SR-8, HSM | High |
| E-2 | SR-5, SR-6 | High |
| E-3 | FR-10, SR-12 | High |
| E-4 | Code signing | Medium |
| E-5 | Constant-time Shamir | Medium |
| E-6 | Unique key ID | High |

---

## 6. Next Steps

1. **Test Plan** – Define unit tests for split/reconstruct, tamper detection, encryption, access control, audit logging, and lockout.
2. **Code Review** – Examine existing `sibb_keys.py` if present; else write from scratch.
3. **Code Implementation** – Ensure compliance with SRD v1.2 and threat model.
4. **Documentation** – Record decision DC-124 after successful tests.

---

**End of Threat Model v1.1**
