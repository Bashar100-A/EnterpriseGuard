# SIBB-Innocence Integration — Threat Model (STRIDE)

**Project:** EnterpriseGuard ADIE  
**Component:** SIBB-Innocence Integration (`tools/sibb_innocence_integration.py`)  
**Version:** 1.1  
**Date:** 2026-09-08  
**Reference:** Security Requirements Document v1.1

---

## 1. Introduction

This threat model analyzes potential threats against the integration of SIBB storage with the Innocence Chain. It follows the STRIDE methodology and maps each threat to the mitigating requirements from SRD v1.1. This version incorporates improvements based on a deep security review, adding rollback, TOCTOU, code tampering, key loss, and underlying storage failure scenarios.

---

## 2. Assets

| Asset ID | Asset |
|----------|-------|
| A1 | Innocence Rings |
| A2 | Stored Ring Data |
| A3 | Verification Keys |
| A4 | Chain State (prev_ring_hash, chain_id) |
| A5 | Configuration |
| A6 | Audit Logs |
| A7 | SIBB HMAC Key |

---

## 3. Threat Actors

| Actor ID | Actor |
|----------|-------|
| T1 | Local Attacker |
| T2 | Compromised Process |
| T3 | Insider Threat |
| T4 | Natural Failure |

---

## 4. STRIDE Analysis

### 4.1 Spoofing (S)

| Threat | Asset | Scenario | Controls (FR/SR) | Status |
|--------|-------|----------|------------------|--------|
| S-1: Spoofed ring data | A1, A2 | Attacker creates a ring with a valid signature but wrong chain context | FR-2, FR-11, SR-11 | Chain continuity check rejects mismatched prev_ring_hash or chain_id |
| S-2: Spoofed verification key | A3 | Attacker replaces public key to forge signatures | SR-2 (using trusted public key + fingerprint) | Public key stored outside SIBB; fingerprint verified |
| S-3: Spoofed chain state | A4 | Attacker modifies the stored chain head | SR-11, FR-12 | Integration uses immutable stored rings as reference; verify_chain detects mismatch |
| S-4: Tampered integration module | All | Attacker modifies `sibb_innocence_integration.py` to bypass checks | Code signing, integrity checks (future) | Document as limitation; recommend code signing and secure deployment |

### 4.2 Tampering (T)

| Threat | Asset | Scenario | Controls | Status |
|--------|-------|----------|----------|--------|
| T-1: Tampered stored ring | A2 | Attacker modifies a stored ring file | SR-1, SR-5 | SIBB HMAC detects tampering on retrieval |
| T-2: Tampered metadata of stored rings | A2 | Attacker changes SIBB metadata | SR-9 | SIBB metadata HMAC and backup recovery |
| T-3: Tampered chain continuity | A4 | Attempt to insert a fork by altering prev_ring_hash | FR-11, SR-11 | Strict prev_ring_hash verification before storage |
| T-4: Tampered configuration | A5 | Change encryption settings or storage paths | SR-6, configuration permissions | Config file 0600; validation on load |
| T-5: TOCTOU on chain head | A4 | Race between reading last ring hash and writing new ring | FR-12, SR-11 | Use atomic lock around read-verify-write; distributed lock for distributed mode |

### 4.3 Repudiation (R)

| Threat | Asset | Scenario | Controls | Status |
|--------|-------|----------|----------|--------|
| R-1: Deny storing a ring | A6 | User denies having stored a particular ring | FR-9, SR-7 | Audit log records store operation with ring_id and timestamp |
| R-2: Deny failed verification | A6 | User denies that a verification attempt failed | FR-9 | Audit log records failures |
| R-3: Deny deletion | A2 | User denies deleting a ring | SR-5 | WORM prevents deletion; any attempt is logged |
| R-4: Rollback of entire chain | A1, A2 | Attacker replaces current chain with an older signed version | FR-11, SR-11, unique chain_id | Chain_id fixed at genesis; deletion impossible (WORM); rollback would require overwriting existing rings, which WORM prevents |

### 4.4 Information Disclosure (I)

| Threat | Asset | Scenario | Controls | Status |
|--------|-------|----------|----------|--------|
| I-1: Ring contents exposed if not encrypted | A2 | Attacker reads stored ring files if encryption disabled | FR-4, SR-3 | Encryption optional but recommended; if enabled, data is AES-GCM encrypted |
| I-2: Password or key leaked | A3, A5 | Attacker obtains password from logs or environment | SR-7, SR-4, SR-3 | Passwords not logged; environment vars removed after use |
| I-3: Verification key exposed | A3 | Public key not secret, but replacement can forge rings | SR-2 | Key fingerprint verification; stored outside SIBB |
| I-4: HMAC key loss or theft | A7 | HMAC key for SIBB is lost or stolen, preventing integrity verification | SR-9 (fallback), key backup | Key stored with 0600; backup via Shamir or separate secure storage recommended |

### 4.5 Denial of Service (DoS)

| Threat | Asset | Scenario | Controls | Status |
|--------|-------|----------|----------|--------|
| D-1: Ring deletion or corruption | A2 | Attacker deletes enough rings to break chain | SR-5, SR-9, FR-10 | WORM, HMAC, backups, replication (if distributed) |
| D-2: Resource exhaustion via large number of rings | A2 | Attacker floods storage with many invalid rings | FR-8 (input validation), FR-11 (chain continuity) | Chain continuity prevents arbitrary ring storage; optional size limits to be added |
| D-3: Quorum failure in distributed mode | A2 | Attacker takes down nodes to prevent writes/reads | FR-10 | Quorum required; system tolerates up to n-quorum failures |
| D-4: Lock contention | A2 | Multiple processes attempt to write ring simultaneously | SR-6, atomic operations | SIBB locking mechanisms prevent corruption |
| D-5: Underlying SIBB failure | A2 | SIBB module crashes or returns errors | SR-9, FR-12 | Integration must handle exceptions, verify results by re-reading, and log critical errors |

### 4.6 Elevation of Privilege (E)

| Threat | Asset | Scenario | Controls | Status |
|--------|-------|----------|----------|--------|
| E-1: Running with root unnecessarily | A1, A2 | Integration runs as root, increasing impact of a vulnerability | FR-9 (least privilege) | Recommend least privilege; no root needed unless chattr |
| E-2: Command injection via ring_id | A2 | ring_id contains shell metacharacters or path traversal | FR-8, SR-12 | Strict pattern `^[A-Za-z0-9_-]{1,64}$`; used only as final component of predefined path |
| E-3: TOCTOU on file operations | A2 | Race between validation and file write | SR-6 | O_NOFOLLOW, symlink checks, atomic writes |
| E-4: Exploiting underlying SIBB weakness | A2 | Attacker exploits a bug in SIBB storage to bypass WORM | SR-5, SR-9 | SIBB modules have their own security controls; integration relies on them but verifies after write |
| E-5: Tampered integration module | All | Attacker modifies code to bypass checks | Code signing, integrity checks | Future; document as limitation |

---

## 5. Mapping Threats to Requirements

| Threat ID | Mitigated by FR/SR | Priority |
|-----------|-------------------|----------|
| S-1 | FR-2, FR-11, SR-11 | High |
| S-2 | SR-2 | High |
| S-3 | SR-11, FR-12 | High |
| S-4 | (future) | Medium |
| T-1 | SR-1, SR-5 | High |
| T-2 | SR-9 | High |
| T-3 | FR-11, SR-11 | High |
| T-4 | SR-6 | High |
| T-5 | FR-12, SR-11 | High |
| R-1, R-2, R-3 | FR-9, SR-7 | High |
| R-4 | FR-11, SR-11 | High |
| I-1 | FR-4, SR-3 | High |
| I-2 | SR-7, SR-4, SR-3 | High |
| I-3 | SR-2 | High |
| I-4 | SR-9, key backup | High |
| D-1 | SR-5, SR-9, FR-10 | High |
| D-2 | FR-8, FR-11 | High |
| D-3 | FR-10 | High |
| D-4 | SR-6 | High |
| D-5 | SR-9, FR-12 | High |
| E-1 | FR-9 | Medium |
| E-2 | FR-8, SR-12 | High |
| E-3 | SR-6 | High |
| E-4 | SR-5, SR-9 | High |
| E-5 | (future) | Medium |

---

## 6. Next Steps

1. **Test Plan** – Define unit tests for storage, retrieval, verification, and failure scenarios.
2. **Code Implementation** – Write `tools/sibb_innocence_integration.py`.
3. **Run Tests and Static Analysis** – Bandit and pytest.
4. **Documentation** – Record decision (e.g., DC-126).

---

**End of Threat Model v1.1**
