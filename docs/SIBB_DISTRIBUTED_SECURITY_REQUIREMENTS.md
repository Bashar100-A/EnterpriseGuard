# SIBB Distributed Storage — Security Requirements Document (SRD)

**Project:** EnterpriseGuard ADIE  
**Component:** SIBB Distributed Storage (`tools/sibb_distributed.py`)  
**Version:** 1.0  
**Status:** Draft for review  
**Date:** 2026-09-08  
**Methodology:** OWASP ASVS 4.0, NIST SP 800-218, STRIDE

---

## 1. Introduction

This document defines the security requirements for the SIBB Distributed Storage component. This component provides replication across multiple storage nodes (local or remote) to ensure availability and resilience against data loss or tampering. It integrates with the core `sibb_storage.py` and adds mechanisms for distributed writes, reads, and verification.

---

## 2. Assets to Protect

| Asset | Description | Criticality |
|-------|-------------|-------------|
| **Stored Data** | File contents (proof rings, arbitrary blobs) replicated across nodes | High |
| **Distributed Metadata** | Indexes, hashes, and status information per node | High |
| **Encryption and HMAC Keys** | Keys used to protect data and metadata | Critical |
| **Node Communication** | Node addresses, authentication material between nodes | Medium |
| **Health Status** | Reports on each node's integrity and availability | Medium |

---

## 3. Threat Actors

| Actor | Description | Capabilities |
|-------|-------------|--------------|
| **Local Attacker** | Unauthorized user attempting to access files | Read/write within limited scope, tamper/delete |
| **Network Attacker** | External party intercepting node-to-node communication | Eavesdrop, modify, block traffic |
| **Compromised Node** | One node under attacker control | Serve fake data, refuse service, break quorum |
| **Malicious Administrator** | Insider with elevated privileges | Attempt to alter replicas or metadata |
| **Natural Failure** | Node loss or disk corruption | Partial data loss |

---

## 4. Security Properties (CIA + Non-Repudiation)

- **Confidentiality:** Data stored on nodes remains encrypted when encryption is enabled; only authorized users can decrypt.
- **Integrity:** Any unauthorized modification on any node must be detected and rejected. Metadata is protected by HMAC.
- **Availability:** The system must continue to operate even if a number of nodes fail (according to quorum). Replication ensures data is not lost.
- **Non-Repudiation:** Write operations should be recorded and signed where possible, preventing denial.

---

## 5. Functional Requirements (FR)

- **FR-1:** The system must support at least 3 storage nodes (expandable) for redundancy.
- **FR-2:** A minimum success threshold (quorum) must be defined; default is 2 of 3 nodes.
- **FR-3:** On write, data must be sent to all nodes, and the operation is considered successful if at least `quorum` nodes succeed.
- **FR-4:** On read, the system should attempt to read from any available node and verify data integrity (hash match).
- **FR-5:** The system must provide a manual or periodic verification function (`verify`) to check the integrity of all replicas across nodes.
- **FR-6:** If replicas differ between nodes, the system must identify and isolate the offending node(s).
- **FR-7:** The system must handle failure of one node without data loss or service interruption (as long as remaining nodes ≥ quorum).
- **FR-8:** Communication between nodes must be encrypted and authenticated if distributed over untrusted networks (optional for local setup, to be implemented later).
- **FR-9:** Each node must use `WORMStorage` to ensure per-file immutability.
- **FR-10:** All operations (write, read, node failure) should be logged to the audit chain (future integration with `append_activity`).

---

## 6. Security Requirements (SR)

- **SR-1:** HMAC or digital signatures must be used to verify metadata integrity on each node.
- **SR-2:** Data from a node must be accepted only if its hash matches the value recorded in the node's metadata.
- **SR-3:** Metadata must only be modifiable through a trusted process (e.g., `WORMStorage` itself).
- **SR-4:** Inter-node communication must be encrypted and authenticated if over an untrusted network (postponed).
- **SR-5:** Strict quorum enforcement: a write that does not meet the minimum number of successful nodes is considered failed and must not be acknowledged.
- **SR-6:** When tampering is detected on a node, that node must be excluded from subsequent operations until re-verified.
- **SR-7:** HMAC/encryption keys must be stored outside node directories with permissions `0600`.
- **SR-8:** All writes within each node must be atomic (using `WORMStorage`).
- **SR-9:** TOCTOU attacks at the node level must be prevented (each node handles its files securely).
- **SR-10:** A mechanism must be provided to restore a node from a healthy replica if its data is corrupted (cloning).

---

## 7. Constraints and Assumptions

- **Current environment:** Distribution is on local nodes (different directories on the same machine or shared paths). Secure network support is not yet implemented.
- **Performance:** Concurrent writes to multiple nodes may be slower; performance must be measured.
- **Communication:** No encryption between nodes currently; it is assumed nodes are in a trusted environment or use secure channels.
- **Partial failure:** The system tolerates failure of up to `n - quorum` nodes, but does not guarantee strong consistency in network partition scenarios.
- **Authentication:** No node-level authentication at this stage; will be added for untrusted networks.

---

## 8. Acceptance Criteria

The component is accepted if:

- It passes all unit tests defined in the upcoming test plan.
- Bandit reports no High or Medium findings on the code.
- It successfully recovers from a single-node failure.
- Security limitations are documented.

---

## 9. Next Steps

1. **Threat Modeling (STRIDE)** – Detailed analysis of distributed threats.
2. **Test Plan** – Define tests covering failure, tampering, and concurrency.
3. **Code Review** – Examine current `sibb_distributed.py` and identify gaps.
4. **Code Modification** – Fix vulnerabilities and ensure tests pass.
5. **Decision Documentation** – Add decision (e.g., DC-124).

---

**End of Security Requirements Document**
