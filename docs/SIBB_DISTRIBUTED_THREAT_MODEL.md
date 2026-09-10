# SIBB Distributed Storage — Test Plan

**Project:** EnterpriseGuard ADIE  
**Component:** SIBB Distributed Storage (`tools/sibb_distributed.py`)  
**Version:** 1.0  
**Date:** 2026-09-08  
**Reference:** SRD v1.0, Threat Model v1.0

## 1. Introduction

This test plan defines the unit and security tests required to validate the SIBB Distributed Storage component. The tests are derived from the Security Requirements Document and the STRIDE threat model. All tests must pass before the component is accepted.

## 2. Test Environment

- Python 3.8+
- pytest
- cryptography (optional, if encryption is tested)
- Local temporary directories for simulating nodes
- No network access required for initial tests

## 3. Test Cases

### 3.1 Basic Distributed Write/Read

| ID | Test Description | Expected Result |
|----|------------------|-----------------|
| DIST-01 | Write data to 3 nodes with quorum 2 | All 3 nodes receive data; write returns success |
| DIST-02 | Write data to 3 nodes but one node fails (simulate by making directory read-only) | Write succeeds if quorum met (2 nodes succeed) |
| DIST-03 | Read data from distributed storage | Returns correct data from any available node |
| DIST-04 | Read data when one node is missing the file | Should still return data from another node |

### 3.2 Quorum Enforcement

| ID | Test Description | Expected Result |
|----|------------------|-----------------|
| QUORUM-01 | Write with quorum=2 but only 1 node succeeds | Write fails and raises error |
| QUORUM-02 | Write with quorum=3 and all 3 nodes succeed | Write succeeds |
| QUORUM-03 | Write with quorum=3 but one node fails | Write fails because quorum not met |

### 3.3 Integrity Verification

| ID | Test Description | Expected Result |
|----|------------------|-----------------|
| INTEG-01 | Verify integrity across all nodes after successful write | All nodes report valid |
| INTEG-02 | Tamper a file on one node (modify content) | verify() detects mismatch on that node |
| INTEG-03 | Delete a file from one node | verify() reports missing file on that node |
| INTEG-04 | Add an unexpected file to a node | verify() reports unexpected file |

### 3.4 Node Failure Handling

| ID | Test Description | Expected Result |
|----|------------------|-----------------|
| FAIL-01 | Simulate complete node failure (directory missing) | System continues to operate with remaining nodes |
| FAIL-02 | Attempt to read when all nodes fail | Read raises an error |
| FAIL-03 | One node returns corrupted data | System should detect and use another node if possible |

### 3.5 Concurrency

| ID | Test Description | Expected Result |
|----|------------------|-----------------|
| CONC-01 | Multiple concurrent writes to different files | All writes succeed, no data corruption |
| CONC-02 | Multiple concurrent reads from same file | All reads return correct data |
| CONC-03 | Concurrent writes to same filename | Only one write succeeds, others fail with WORMStorageError |

### 3.6 Security

| ID | Test Description | Expected Result |
|----|------------------|-----------------|
| SEC-01 | Access key enforcement on distributed storage | Operations fail without correct access key |
| SEC-02 | HMAC key permissions (if applicable) | HMAC key file has 0600 permissions |
| SEC-03 | Path traversal attempt on node filename | Rejected |
| SEC-04 | Symlink attack on node path | Rejected |

### 3.7 Encryption (if enabled)

| ID | Test Description | Expected Result |
|----|------------------|-----------------|
| ENC-01 | Write encrypted data to distributed nodes | Data stored encrypted on disk |
| ENC-02 | Read encrypted data with correct password | Decryption succeeds |
| ENC-03 | Read encrypted data with wrong password | Decryption fails |

## 4. Acceptance Criteria

- All tests pass.
- No high or medium findings from Bandit on the component.
- The system recovers from one-node failure without data loss.
- Quorum rules are strictly enforced.

## 5. Next Steps

1. **Code Review**: Examine current `sibb_distributed.py` (if exists) against these tests and SRD.
2. **Code Modification**: Update or rewrite the code to meet requirements.
3. **Run Tests**: Execute the test suite and fix failures.
4. **Static Analysis**: Run Bandit and address findings.
5. **Documentation**: Update decision log and continuity files.

---

**End of Test Plan**
