# SIBB Key Management — Test Plan

**Project:** EnterpriseGuard ADIE  
**Component:** SIBB Key Management (`tools/sibb_keys.py`)  
**Version:** 1.1  
**Date:** 2026-09-08  
**Reference:** SRD v1.2, Threat Model v1.1

---

## 1. Introduction

This test plan defines the unit and security tests required to validate the SIBB Key Management component. It addresses the gaps identified in the previous version (v1.0) and is aligned with SRD v1.2 and Threat Model v1.1. Each test includes setup, inputs, and expected outcome where applicable.

---

## 2. Test Environment

- Python 3.10+
- `pytest`
- `cryptography` (for AES-GCM, PBKDF2, HKDF, HMAC)
- Local temporary directories (`tmp_path`) for share storage
- No network access required

---

## 3. Test Cases

### 3.1 Master Key Generation

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| KEY-01 | Generate a master key (32 bytes) | Call `generate_master_key()` | Key is 32 bytes, cryptographically random |
| KEY-02 | Generate two master keys | Call function twice | Keys are different |
| KEY-03 | Verify PBKDF2 iterations and key length | Inspect constants | `PBKDF2_ITERATIONS >= 480000`; key length 32 |
| KEY-04 | Generate two sets of shares from different master keys | Split two different master keys | Each set has a unique `key_id` |

### 3.2 Shamir Secret Sharing

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| SPLIT-01 | Split master key into N=5 shares, threshold K=3 | `split_master_key(key, n=5, k=3)` | Returns 5 shares, each different |
| SPLIT-02 | Reconstruct key from exactly K shares | Use any 3 valid shares | Returns original master key |
| SPLIT-03 | Reconstruct key from more than K shares (4 of 5) | Use 4 valid shares | Returns original master key |
| SPLIT-04 | Attempt reconstruction with K-1 shares | Provide only 2 shares | Raises `InsufficientSharesError` |
| SPLIT-05 | Attempt reconstruction with an invalid share (random bytes) | Replace one share with random data | Raises `ShareIntegrityError` |
| SPLIT-06 | Ensure shares have random identifiers and order does not matter | Reconstruct using any subset of K shares in arbitrary order | Reconstruction succeeds |

### 3.3 Encryption at Rest

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| ENC-01 | Encrypt shares with password | Split with password "StrongPass123!" | Share files on disk are not plaintext; ciphertext differs from original |
| ENC-02 | Decrypt and reconstruct with correct password | Provide correct password | Master key recovered |
| ENC-03 | Attempt reconstruction with wrong password | Provide wrong password | Raises generic `ShareIntegrityError` (no specific error) |
| ENC-04 | Verify each share uses unique salt/nonce | Inspect share files | Salts/nonces are different across shares |
| ENC-05 | Verify share file contains only encrypted data and metadata | Read share file | No plaintext master key or share |

### 3.4 HMAC Integrity

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| INTEG-01 | Generate shares and verify HMAC | `verify_share_integrity(share)` | Returns True |
| INTEG-02 | Tamper with one share ciphertext | Flip a byte in share file | Verification fails |
| INTEG-03 | Tamper with HMAC itself | Modify HMAC part of share file | Verification fails |
| INTEG-04 | Tamper with metadata (threshold) | Change threshold value in share structure | Verification fails (metadata protected) |
| INTEG-05 | Verify code uses constant-time comparison | Static review or mock test | `hmac.compare_digest` is used instead of `==` |

### 3.5 Access Control

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| AUTH-01 | Call split/reconstruct without password when password is required | No password provided | Operation fails |
| AUTH-02 | Call split/reconstruct with correct password | Correct password | Operation succeeds |
| AUTH-03 | Call split/reconstruct with wrong password | Wrong password | Operation fails, generic error |
| AUTH-04 | Check password is not logged or stored | Inspect audit log and share files | No plaintext password found |

### 3.6 Audit Logging

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| AUDIT-01 | Perform successful split operation | Call `split_master_key` | `append_activity` called with event type "key_split" |
| AUDIT-02 | Perform successful reconstruction | Call `reconstruct_key` | `append_activity` called with event type "key_reconstruct" |
| AUDIT-03 | Perform failed operation (wrong password) | Call `reconstruct_key` with wrong password | `append_activity` called with failure details |
| AUDIT-04 | Delete a share | Call `delete_share` | `append_activity` called |
| AUDIT-05 | Verify audit log does not contain password | Inspect log entries | No plaintext password in log |
| AUDIT-06 | Audit log is protected (HMAC) | Tamper with log file | Log verification fails (if implemented) |

### 3.7 Lockout Mechanism (SR-12)

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| LOCK-01 | Enter wrong password multiple times | Call reconstruction with wrong password N times | After N attempts, temporary lockout occurs |
| LOCK-02 | Wait for lockout period | Wait until lockout expiry | Can attempt again |
| LOCK-03 | Lockout does not affect other functions | During lockout, call split on a new key | Operation succeeds (lockout is per user/action) |

### 3.8 Zeroization and Secure Deletion

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| ZERO-01 | Sensitive data is cleared from memory (best effort) | Use a mock or inspect `bytearray` after function returns | Bytearray is zeroed or empty |
| ZERO-02 | Temporary files containing keys are deleted | Monitor temp directory during/after operations | No leftover temp files |
| DEL-01 | Delete a share securely | Call `delete_share` on a share file | File is removed; no plaintext remains (best effort) |

### 3.9 Path and Symlink Security

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| PATH-01 | Save share with filename containing `../` | Attempt `save_share` with path traversal | Raises `WORMStorageError` or equivalent |
| PATH-02 | Symlink attack on share directory | Create symlink in shares dir pointing to sensitive file | Operation refuses to write through symlink |
| PERM-01 | Verify share file permissions | After writing share, check `stat.st_mode & 0o777` | Permission is `0600` |
| PERM-02 | HMAC key file permissions | Check HMAC key file | Permission is `0600`, and file is outside shares directory |

### 3.10 Concurrency

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| CONC-01 | Concurrent split and reconstruct operations | Run multiple `split_master_key` and `reconstruct_key` in threads | No errors, data consistent |
| CONC-02 | Concurrent read while writing share | Simulate reading share while another thread writes | No partial reads; verification passes |
| CONC-03 | Lockout under concurrency | Multiple threads attempt wrong password simultaneously | Lockout counter works correctly |

### 3.11 HMAC Key Management

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| HMAC-01 | HMAC key is generated randomly | Generate HMAC key | Key is 32 bytes, random |
| HMAC-02 | HMAC key is not stored in shares directory | Check path | HMAC key file is outside shares directory |
| HMAC-03 | HMAC key file protected from tampering | Modify HMAC key file | Integrity check fails, system alerts |
| HMAC-04 | Backup/recovery of HMAC key | (Future) | Documented limitation |

### 3.12 Algorithm Parameters

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| ALGO-01 | Shamir uses a safe prime and constant-time operations | Inspect code or run performance test | No timing leakage (best effort) |
| ALGO-02 | PBKDF2 iterations meet minimum | Inspect constant | `PBKDF2_ITERATIONS >= 480000` |
| ALGO-03 | Master key length is 32 bytes | Inspect key generation | Key is 32 bytes |

---

## 4. Acceptance Criteria

- All tests pass.
- No High or Medium findings from Bandit on `tools/sibb_keys.py`.
- Master key can be reconstructed only with at least K valid shares.
- Shares are encrypted at rest; no plaintext on disk.
- HMAC key has `0600` permissions and is outside shares directory.
- Audit logging is functional and does not leak passwords.
- Lockout mechanism works (if implemented).
- Zeroization is attempted (best effort).
- Path traversal and symlink attacks are rejected.
- Share file permissions are `0600`.
- HMAC key management and integrity are covered.

---

## 5. Next Steps

1. **Code Review**: Examine existing `tools/sibb_keys.py` (if it exists) against this test plan and SRD v1.2.
2. **Code Implementation**: Write or update the code to meet requirements.
3. **Run Tests**: Execute the test suite and fix failures.
4. **Static Analysis**: Run Bandit and address findings.
5. **Documentation**: Record decision (e.g., DC-124) and update continuity files.

---

**End of Test Plan v1.1**
