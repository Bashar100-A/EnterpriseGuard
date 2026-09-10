# SIBB-Innocence Integration — Test Plan

**Project:** EnterpriseGuard ADIE  
**Component:** SIBB-Innocence Integration (`tools/sibb_innocence_integration.py`)  
**Version:** 1.1  
**Date:** 2026-09-08  
**Reference:** SRD v1.1, Threat Model v1.1

---

## 1. Introduction

This test plan defines the unit and security tests required to validate the integration between SIBB storage and the Innocence Chain. It covers functional correctness, chain continuity, signature verification, encryption, distributed mode, error handling, TOCTOU prevention, WORM enforcement, and the threats identified in STRIDE v1.1.

---

## 2. Test Environment

- Python 3.8+
- `pytest`
- `cryptography`
- Temporary directories for SIBB storage and keys
- Mock or real `innocence_chain` functions (preferably use actual module with test keys)
- No network access required

---

## 3. Test Cases

### 3.1 Ring Storage and Retrieval

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| INT-01 | Store a valid signed ring | Provide a ring with correct signature, prev_ring_hash matching current head, valid chain_id | Ring stored successfully; `store_ring` returns True |
| INT-02 | Retrieve a stored ring | After storing, call `retrieve_ring` with the ring_id | Returns original ring data and metadata |
| INT-03 | Store duplicate ring_id | Attempt to store same ring_id again | Rejected with WORM error, no overwrite |
| INT-04 | Store ring with invalid signature | Provide ring with wrong signature | Storage refused |
| INT-05 | Store ring with mismatched prev_ring_hash | Ring's prev_ring_hash != current chain head | Storage refused (chain continuity violation) |
| INT-06 | Store ring with different chain_id | Ring's chain_id differs from genesis chain_id | Storage refused |

### 3.2 Chain Continuity Enforcement

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| CONT-01 | Store first ring when no previous rings | prev_ring_hash equals genesis hash | Accept |
| CONT-02 | Store subsequent ring with correct prev_ring_hash | After storing first ring, store second ring with prev_ring_hash = hash(first) | Accept |
| CONT-03 | Store subsequent ring with wrong prev_ring_hash | Second ring's prev_ring_hash = random | Reject |
| CONT-04 | Attempt rollback by storing older signed chain | Try to store a ring from a valid but older chain (same chain_id but earlier prev) | Rejected due to mismatch with current head |

### 3.3 TOCTOU Prevention on Chain Head

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| TOCTOU-01 | Concurrent writes to same chain head | Use multiple threads or processes to attempt storing two different rings simultaneously, both with prev_ring_hash matching the same current head | Only one write succeeds; the other is rejected |
| TOCTOU-02 | Atomic lock around read-verify-write | Verify that the integration uses a lock (e.g., `threading.Lock` or file lock) during the sequence: read last ring hash → verify new ring → store new ring | Lock is acquired and released properly; no race condition |

### 3.4 Signature Verification

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| SIG-01 | Verify signature before storage using trusted public key | Mock `innocence_chain.verify_ring` to return True; provide ring with valid signature | Pass verification and store |
| SIG-02 | Detect forged signature | Mock `innocence_chain.verify_ring` to return False; provide ring with invalid signature | Storage rejected |
| SIG-03 | Verify genesis signature | Ring includes genesis_signature; mock verification to check genesis_signature is called | Reject if genesis signature invalid |
| SIG-04 | Public key replacement | Swap public key with attacker key; attempt to store ring signed by attacker | Rejected because fingerprint/key mismatch or chain_id mismatch |
| SIG-05 | Ensure correct verification function called | Mock `innocence_chain.verify_chain` or `verify_ring` and assert it is called with expected parameters | Mock is called exactly once with ring data and public key |

### 3.5 Encryption (if enabled)

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| ENC-01 | Store ring with encryption enabled | Provide password; store ring | Ring stored encrypted; raw data on disk is not plaintext |
| ENC-02 | Retrieve ring with correct password | Use correct password | Returns decrypted ring data |
| ENC-03 | Retrieve ring with wrong password | Use wrong password | Decryption fails, generic error |
| ENC-04 | Ensure no plaintext key stored | Inspect stored files | No password or plaintext key visible |
| ENC-05 | Unique salt/nonce per ring | Inspect multiple stored rings' encrypted structures | Each ring has unique salt and nonce |
| ENC-06 | AEAD integrity verification | Corrupt ciphertext of a stored ring; attempt retrieve | Retrieval fails with integrity error |

### 3.6 Distributed Mode

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| DIST-01 | Store ring in distributed mode with quorum=2, 3 nodes | Provide 3 node paths, store ring | Ring stored on all nodes; success if at least 2 nodes write |
| DIST-02 | Node failure during write | Make one node read-only; store ring | Write succeeds if quorum met (2 nodes) |
| DIST-03 | Read ring from distributed storage | Retrieve ring after partial failure | Returns valid ring from healthy node |
| DIST-04 | Verify cross-node integrity | After store, run verification | All nodes report valid; any tampered node detected |
| DIST-05 | Quorum not met | Make two nodes fail; attempt store | Storage fails with error |
| DIST-06 | Hash consistency across nodes | After storing ring, compare hash of stored ring on each node | All nodes have identical hash; if one differs, detected and node marked corrupted |

### 3.7 WORM Enforcement

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| WORM-01 | Attempt to delete a stored ring | Call a delete function (if exists) or directly delete file through SIBB | Operation rejected or deletion detected on next verify |
| WORM-02 | Attempt to overwrite a stored ring | Try to store same ring_id with different data | Rejected with WORM error |
| WORM-03 | Symlink attack on ring directory | Create symlink inside rings directory pointing outside; attempt store through it | Storage refused |

### 3.8 verify_stored_rings

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| VERIFY-01 | Verify stored rings against live innocence chain | Store several rings, then run `verify_stored_rings` | Returns success if all rings match chain state |
| VERIFY-02 | Detect mismatch with live chain | After storing, modify or replace current innocence chain with older version (or different chain_id); run verify | Detects mismatch and reports error |
| VERIFY-03 | Corrupted ring detection | Tamper with one stored ring; run verify | Detects corrupted ring and reports |
| VERIFY-04 | Missing ring detection | Delete one ring file (if possible) or remove from metadata; run verify | Reports missing ring |

### 3.9 Error Handling and Logging

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| ERR-01 | Storage backend failure | Simulate SIBB write failure | `store_ring` returns error, logs critical event |
| ERR-02 | Verification after store fails | After store, corrupt chain state; run `verify_stored_rings` | Detects mismatch and raises error |
| ERR-03 | Audit logging on store | Call `store_ring` and check audit log | Event logged with ring_id, timestamp, no secret data |
| ERR-04 | Audit logging on retrieve | Call `retrieve_ring` and check audit log | Event logged |
| ERR-05 | Audit logging on failed operation | Attempt to store invalid ring | Failure logged |
| ERR-06 | No secret in logs | Inspect logs after encryption operation | No password or key material |
| ERR-07 | append_activity failure | Mock `append_activity` to raise exception; call store | Operation continues with warning (or fails according to policy), but no crash |
| ERR-08 | HMAC key missing | Remove SIBB HMAC key file; attempt store | Operation fails with clear error |

### 3.10 Input Validation

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| VAL-01 | Invalid ring_id (path traversal) | ring_id = `../../evil` | Rejected |
| VAL-02 | Invalid ring_id (special chars) | ring_id = `bad;rm` | Rejected |
| VAL-03 | Valid ring_id pattern | ring_id = `ring_001` | Accepted |
| VAL-04 | Ring_id too long | ring_id > 64 chars | Rejected |
| VAL-05 | Symlink in ring path | Create symlink in storage; attempt store using symlink path | Rejected |

### 3.11 Underlying SIBB Failure Simulation

| ID | Test Description | Setup/Input | Expected Result |
|----|------------------|-------------|-----------------|
| FAIL-01 | SIBB metadata corrupted | Manually corrupt SIBB metadata; attempt retrieve | Integration reports error, falls back to backup if available |
| FAIL-02 | SIBB HMAC key missing | Remove HMAC key file; attempt store | Operation fails with clear error |
| FAIL-03 | SIBB returns hash mismatch on read | Tamper with stored ring; retrieve | Integration detects mismatch and rejects |
| FAIL-04 | SIBB partial write (simulate crash) | Mock SIBB write to create file but not update metadata; attempt retrieve | Orphan detected, handled gracefully |

---

## 4. Acceptance Criteria

- All tests pass.
- No High or Medium findings in Bandit on `tools/sibb_innocence_integration.py`.
- Chain continuity and signature verification are strictly enforced.
- Encryption, if enabled, is effective and no secrets are leaked.
- Distributed mode respects quorum and tolerates node failures.
- Audit logging is functional for all mutating operations.
- Input validation blocks path traversal and injection.
- WORM semantics are enforced; deletion and overwrite attempts are rejected.
- Underlying SIBB failures are handled gracefully without data loss.

---

## 5. Next Steps

1. **Code Implementation** – Write `tools/sibb_innocence_integration.py`.
2. **Run Tests** – Execute the test suite and fix failures.
3. **Static Analysis** – Run Bandit and address findings.
4. **Documentation** – Record decision (e.g., DC-126) and update continuity files.

---

**End of Test Plan v1.1**
