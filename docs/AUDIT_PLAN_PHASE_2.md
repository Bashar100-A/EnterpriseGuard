# Project Plan Document: ADIE - Phase 2 (Trusted Intelligence & Model Provenance)
**File Path:** `docs/AUDIT_PLAN_PHASE_2.md`

---

## Status Legend
*   ⬜ Not Started
*   🟡 In Progress
*   🔁 Under Review
*   ✅ Completed
*   ⛔ Blocked/On Hold
*   🔒 Approved/Frozen

---

## 1. Document Information
| Attribute | Details |
| :--- | :--- |
| **Project Name** | ADIE System - Phase 2 (Trusted Intelligence Subsystem)[cite: 2] |
| **Version** | v1.1 |
| **Release Date** | September 30, 2026 |
| **Owner** | Chief Architect / Information Security Team[cite: 2] |
| **Status** | 🟡 In Progress (Core SDK Development & Testing Active) |

### Revision History
| Version | Date | Description | Author/Editor |
| :--- | :--- | :--- | :--- |
| 0.1 | [TBD] | Initial Draft[cite: 2] | Development Team[cite: 2] |
| 1.0 | 2026-09-28 | Major restructure aligning with FROZEN v1.0 Errata A[cite: 2] | AI Agent[cite: 2] |
| 1.1 | 2026-09-30 | Status update: AAAC connector (Ring Storage/Tracing) stabilized, 294 tests passing, test coverage at 10% | Bashar GH & AI Agent |

---

## 2. Executive Summary
Phase 2 of the ADIE project aims to transform generative and machine learning models from "decision makers" into "cryptographically trusted evidence producers."[cite: 2] This phase will deliver a Core SDK that ensures model artifact provenance, deterministic serialization, and a strict architectural separation between inference (Prediction) and action (Decision).[cite: 2] The project guarantees that AI models hold zero authority to issue ALLOW/BLOCK commands without traversing the deterministic Policy Engine.[cite: 2]

---

## 3. Phase Objective
Build and deliver the `ADIE Core SDK`, providing a deterministic infrastructure for model inference.[cite: 2] At any historical point in time, the system must be able to cryptographically prove: why an inference was trusted, which exact artifact produced it, which key signed it, and what features it relied on, all while ensuring total architectural isolation from the decision-making core.[cite: 2]

---

## 4. In Scope
* Implement the RFC 8785 standard to ensure Canonical Serialization (JCS).[cite: 2]
* Manage ECDSA Key Lifecycle incorporating Effective Time Semantics.[cite: 2]
* Construct the `TypedFeatureSnapshot` and `PredictionContract` data structures.[cite: 2]
* Develop a secure inference pipeline using `onnxruntime` that strictly adheres to predefined Runtime Contracts.[cite: 2]
* Generate Cryptographic Test Vectors to ensure interoperability and determinism.[cite: 2]
* Integrate SDK outputs natively with the `ADIE Decision Core`.[cite: 2]

---

## 5. Out of Scope
* Training new ML models or optimizing the accuracy of existing ones (Focus is strictly on trust infrastructure, not ML performance).[cite: 2]
* Modifying the internal rules or logic of ADIE's Policy Engine.[cite: 2]
* Developing Graphical User Interfaces (GUIs) or Dashboards (excluding CLI outputs for testing purposes).[cite: 2]

---

## 6. Stakeholders
| Name / Department | Role | Impact Level |
| :--- | :--- | :--- |
| [TBD] | Executive Sponsor[cite: 2] | High[cite: 2] |
| Chief Architect | Architectural Approval & Final Evaluation[cite: 2] | High[cite: 2] |
| Data Engineering Team | Feature Schema Definitions[cite: 2] | Medium[cite: 2] |
| DevSecOps Team | Infrastructure, Key Management & Security Audits[cite: 2] | High[cite: 2] |

---

## 7. RACI Matrix
*(R: Responsible, A: Accountable, C: Consulted, I: Informed)*

| Task | Software Engineer | Security Engineer | Chief Architect | Project Manager |
| :--- | :--- | :--- | :--- | :--- |
| Core SDK Development | R | C | A | I |
| Generate Test Vectors | R | R | C | I |
| Key Lifecycle Audit | C | R | A | I |
| Decision Core Integration | R | I | C | A |
| Final E2E Proof Review | I | C | A | R |

---

## 8. Key Deliverables
1. `ADIE Trusted Intelligence SDK` (Python Package).[cite: 2]
2. Deterministic Test Suite (Test Vectors JSON & Binaries).[cite: 2]
3. End-to-End Provenance Proof Report.[cite: 2]
4. API Technical Documentation.[cite: 2]

---

## 9. Acceptance Criteria
* **Determinism:** 100% byte-for-byte match for JCS serialization across different operating systems and environments.[cite: 2]
* **Security (Fail-Closed):** Immediate system rejection when encountering tampered model metadata or inference utilizing a revoked key.[cite: 2]
* **Independence:** The SDK must not contain any methods or functions capable of issuing final system decisions.[cite: 2]
* **Traceability & Proof:** The ability to retrieve a historical `PredictionContract` and cryptographically verify the validity of its signing key at the exact time of signing.[cite: 2]

---

## 10. Phases & Sub-phases

### 🔒 Phase 1: Architectural Freeze
* 🔒 1.1 Define Canonical Contracts.[cite: 2]
* 🔒 1.2 Isolate Authenticity from Continuity.[cite: 2]
* 🔒 1.3 Cement the principle: Model Approval ≠ Decision Authority.[cite: 2]
* **Phase Notes:** The architecture is fully approved and locked (FROZEN v1.0 Errata A).[cite: 2] No modifications are permitted without a formal Versioned Architectural Amendment.[cite: 2]

### 🟡 Phase 2: Core SDK Development
* 🟡 2.1 Build the deterministic serialization pipeline (RFC 8785).[cite: 2]
* 🟡 2.2 Implement the Key Lifecycle State Machine.
* 🟡 2.3 Code the `TypedFeatureSnapshot` and `PredictionContract` schemas.
* **Phase Notes:** Must utilize Pydantic's `model_dump(mode="json")` to extract primitives cleanly.[cite: 2] Historical validity functions must be logically separated from runtime operational validity functions.[cite: 2]

### 🟡 Phase 3: Cryptographic Test Vectors & Contract Tests
* 🟡 3.1 Generate static Test Vector files (Manifest -> Canonical Hash -> Signature).
* 🟡 3.2 Program Fail-Closed Edge Case tests.
* **Phase Notes:** Current testing suite is stable (294/294 tests passing, zero warnings), but core logic coverage is at ~10% and must be expanded to meet the 95% target. Any failure during this phase must trigger a hard stop in the CI/CD pipeline.[cite: 2]

### ⬜ Phase 4: Integration with ADIE Decision Core
* ⬜ 4.1 Pass the Evidence (`PredictionContract`) into the System State.[cite: 2]
* ⬜ 4.2 Verify the Policy Engine's capability to evaluate typed `ConfidenceMetrics`.[cite: 2]
* **Phase Notes:** Ensure that the `confidence` field is handled as a structured object (score, method, semantics_version), not a raw float.[cite: 2]

### 🟡 Phase 5: End-to-End Provenance Proof
* 🟡 5.1 Simulate a full lifecycle (Train -> Sign -> Execute Inference -> Revoke Key -> Historical Audit). (Ring Storage for tracing initialized via `aaac_connector`)
* ⬜ 5.2 Extract and finalize the Cryptographic Compliance Report.[cite: 2]
* **Phase Notes:** The ultimate success metric is the system's ability to legally and mathematically justify a historical inference even after its authorizing key has been revoked.[cite: 2]

---

## 11. Detailed Tasks & Activities

| # | Task (Description) | Assignee | Inputs | Outputs | Duration (Days) | Dependencies | Completion Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Code `CanonicalModelManifest` and apply JCS | Bashar GH | Frozen Architecture | Python code with Tests | 3 | - | Exact byte match for JCS |
| 2 | Code `is_historically_valid_for` & `is_model_trusted_for_inference` | Sec Eng | Key Lifecycle Rules | Time-bound validation code | 2 | 1 | Pass Half-open interval tests |
| 3 | Build `TypedFeatureSnapshot` rejecting undefined values (NaN/Inf) | Bashar GH | Feature Schema | Strict Pydantic Object | 2 | 1 | Throws Exception on NaN/Inf |
| 4 | Generate `Expected_Canonical.bin` & `Expected_Signature.hex` | Sec Eng | JSON Manifest | Test Vectors | 3 | 1, 2 | 100% Unit Test pass across environments |
| 5 | Integrate SDK with `ADIE Decision Core` | System Arch | Core SDK | API Integration Point | 4 | 3, 4 | Prediction successfully transitions to Evidence in State |

---

## 12. Timeline & Milestones
* **Milestone 1 (M1):** 🟡 Completion of the Core SDK codebase (Date: [TBD]). 
* **Milestone 2 (M2):** 🟡 Passing 100% of Cryptographic Test Vectors (Date: [TBD]). *(Note: Currently 294 baseline tests are passing flawlessly, transitioning to cryptography vectors)*
* **Milestone 3 (M3):** ⬜ Successful integration with the Decision Core (Date: [TBD]).[cite: 2]
* **Milestone 4 (M4):** ⬜ E2E Provenance Proof presentation to management and phase closure (Date: [TBD]).[cite: 2]

---

## 13. Required Resources
* **Human:** 1 Senior Software Engineer, 1 Cryptography/Security Engineer, 1 Systems Engineer (DevOps).[cite: 2]
* **Technical:** Isolated CI/CD environments, core libraries (`pydantic>=2.0`, `jcs`, `cryptography`, `onnxruntime`).[cite: 2]
* **Tools:** WORM Storage Mock/Local Instance for continuity testing.[cite: 2]

---

## 14. Estimated Budget / Cost Parameters
* Infrastructure costs for isolated testing environments: [TBD][cite: 2]
* Engineering development hours: Estimated 120-160 technical hours.[cite: 2]
* External Security Audit costs (if applicable): [TBD][cite: 2]

---

## 15. Risk Management
| Risk | Probability | Impact | Mitigation Plan | Owner |
| :--- | :--- | :--- | :--- | :--- |
| JCS output mismatch across Python versions | Low | Catastrophic | Enforce `jcs` library usage, pin library versions, and enforce strict Test Vectors | Sec Eng |
| SDK inadvertently acquiring decision authority | Medium | Catastrophic | Mandatory strict Code Reviews ensuring zero `allow/block` capabilities within the layer | System Arch |
| Inference latency overhead due to crypto validation | Medium | Medium | Optimize crypto checks using C++ bindings if necessary, benchmark performance | Bashar GH |

---

## 16. Assumptions
* **[TBD-01]:** It is assumed that the `ADIE Decision Core` is prepared to ingest and parse `PredictionContract` objects without requiring a ground-up rebuild.[cite: 2]
* It is assumed that Trust Anchors (Signing Keys) are securely generated and managed externally via a KMS, and the SDK will only receive Public Keys for verification purposes.[cite: 2]

---

## 17. Constraints
* Modifying the `Errata A` specifications during implementation is strictly prohibited without a formal amendment request.[cite: 2]
* All time validation logic must explicitly utilize half-open intervals (`[valid_from, effective_end)`).[cite: 2]

---

## 18. Quality & Test Plan
* **Contract Tests:** 100% strict type and schema validation.[cite: 2]
* **Cryptographic Tests:** Implement static Test Vectors to ensure cryptographic integrity remains unbroken across updates.[cite: 2]
* **Edge Case Testing:** Extensive simulation of edge cases, including an inference request occurring on the exact millisecond a key is revoked.[cite: 2]

---

## 19. Communication & Reporting Plan
* Weekly progress reports submitted to the Chief Architect focusing on Test Vector pass rates.[cite: 2]
* Technical review meeting scheduled immediately upon reaching Milestone 2 (M2).[cite: 2]

---

## 20. Change Management
* Any structural change to serialization or hashing algorithms requires bumping the Architectural Version (Architectural Amendment).[cite: 2]
* Major deviations require explicit sign-off from the Chief Architect and the Executive Sponsor.[cite: 2]

---

## 21. Key Performance Indicators (KPIs)
* Code Test Coverage: 🟡 ~10% (Target: ≥ 95%).
* Cryptographic Vectors Test Success Rate: 🟡 100% (294/294 baseline tests passing; expanding to cryptographic vectors).
* Added Inference Latency (Crypto Verification Overhead): ≤ [TBD] ms.[cite: 2]

---

## 22. Release Plan
* Publish the Core SDK to the internal artifact repository (Internal PyPI / Artifactory).[cite: 2]
* Deploy to a Staging environment running a Shadow Mode parallel to the Decision Core.[cite: 2]

---

## 23. Closure & Final Handover Plan
* Conduct an independent Security Audit on the Core SDK.[cite: 2]
* Issue the final "E2E Provenance Proof" document demonstrating architectural success.[cite: 2]
* Obtain final formal sign-off from all stakeholders on the proof document.[cite: 2]

---

## 24. General Notes
* This English version of `AUDIT_PLAN_PHASE_2` translates all implementation invariants established in the Frozen Architecture, ready to be utilized as the master implementation guide for the engineering team.[cite: 2]
