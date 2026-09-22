# EnterpriseGuard Phase 0 Threat Model

**Version:** 1.0  
**Status:** DRAFT / PHASE 0 baseline  
**Governed by:** `docs/EXECUTION_PLAN.md` (v3.0), `continuity/RULES.md`  
**Key Invariants:** DC-142 (Trust Minimization), DC-143 (Decision Certificate Boundary)

---

## 1. Executive Summary & Scope

This document defines the authoritative Phase 0 Threat Model for EnterpriseGuard. Its primary objective is to establish a rigorous security baseline, map assets, delineate explicit trust boundaries, and mitigate security risks associated with verifiable AI decision infrastructure.

### Core Invariant (DC-142)
> Independent verification MUST NOT depend on online EnterpriseGuard services, runtime availability, or vendor-specific private state. All cryptographic assumptions must remain explicit and enumerable.

---

## 2. System Assets & Criticality

| Asset ID | Asset Name | Description | Confidentiality | Integrity | Availability |
|---|---|---|---|---|---|
| **AST-01** | **Signing Private Keys** | RSA/ECDSA private keys used by issuers to sign Decision Certificates. | **CRITICAL** | **CRITICAL** | **HIGH** |
| **AST-02** | **Decision Certificates** | Portable proof objects binding decisions to evidence, state, and policy (E1-E8). | PUBLIC/LOW | **CRITICAL** | MEDIUM |
| **AST-03** | **Evidence Store** | Raw inputs, context references, and state bindings evaluated during decision-making. | HIGH | **CRITICAL** | MEDIUM |
| **AST-04** | **Policy Definitions** | Rule sets and versioned constraints governing decision authorization. | MEDIUM | **CRITICAL** | HIGH |
| **AST-05** | **Agent & Model Identity** | Cryptographic identities and hashes of AI models, agents, and configurations. | LOW | **CRITICAL** | MEDIUM |
| **AST-06** | **Verification Engine** | Code and logic executing offline verification of certificates and proofs. | N/A | **CRITICAL** | HIGH |

---

## 3. Trust Boundaries & Entities
[ External / Verifier Environment ]
│
│ (Independent Offline Verification Boundary)
▼
┌─────────────────────────────────────────────────────────┐
│ Verification Engine (Offline, Zero Vendor Dependency)   │
└─────────────────────────────────────────────────────────┘
▲
│ Portable Decision Certificate (AST-02)
┌─────────────────────────────────────────────────────────┐
│ Issuer Runtime Boundary (EnterpriseGuard Infrastructure) │
│                                                         │
│  ┌───────────────────────┐   ┌───────────────────────┐  │
│  │ Private Keys (AST-01)  │   │ Evidence Store        │  │
│  └───────────────────────┘   └───────────────────────┘  │
│  ┌───────────────────────┐   ┌───────────────────────┐  │
│  │ Policies (AST-04)     │   │ Model ID (AST-05)     │  │
│  └───────────────────────┘   └───────────────────────┘  │
└─────────────────────────────────────────────────────────┘


### Key Boundaries:
1. **Issuer vs. Verifier Boundary:** Separation between certificate generation (requires private state/keys) and certificate verification (strictly offline and stateless).
2. **Runtime vs. External Dependency Boundary:** Storage and network interfaces are external boundaries; verification logic must treat all inputs across this boundary as untrusted.

---

## 4. Threat Matrix & Remediation Controls

| Threat ID | Threat Category | Threat Description | Attack Vector | Phase 0 Mitigation Control |
|---|---|---|---|---|
| **THR-01** | **Tampering** | Alteration of Decision Certificate payload or context bindings (E1-E6) post-issuance. | Modifying JSON fields in transit or at rest. | Canonicalization (RFC 8785 JSON Canonicalization) + strict cryptographic signature verification. |
| **THR-02** | **Key Compromise** | Unauthorized exposure or theft of Issuer Private Keys (AST-01). | Exfiltrating secrets from environment variables or hardcoded values. | Strict secret isolation; zero hardcoded credentials; separation of production and dev keys. |
| **THR-03** | **Replay & Rollback** | Re-submitting historical valid decisions in outdated policy or expired state contexts. | Capturing old valid certificates and presenting them as current. | Explicit Policy Version Binding (E3) and Timestamps (E7/E8) evaluated deterministically. |
| **THR-04** | **Equivocation** | An issuer signing two conflicting certificates for the exact same decision context. | Malicious or buggy dual-issuance by runtime. | Provenance DAG hashing (Phase 5) and future transparency log inclusion rules. |
| **THR-05** | **Unauthorized Delegation** | Issuing decisions under an unapproved or expired delegation authority scope. | Forging delegation claims or bypassing parent authority checks. | Chain-of-trust authority checks with explicit scope and time boundaries (Phase 4). |
| **THR-06** | **Disclosure / Leakage** | Exposure of sensitive evidence data embedded within public certificate payloads. | Including raw unhashed PII/secrets inside certificate metadata. | Commitment/Hash references for evidence (E1) rather than raw sensitive evidence payloads. |
| **THR-07** | **ASVS Level 1 Deficiencies** | Unresolved security findings from the C3 Security Report. | OWASP ASVS Top-10 vulnerabilities in API/SDK boundaries. | Systematic vulnerability remediation and C3 findings disposition before Phase 1 activation. |

---

## 5. Security Gates & Acceptance Evidence

Before Phase 0 is declared **COMPLETE** and Phase 1 is authorized, the following binary gates must pass:

1. **C3 Disposition Record:** All findings identified in the C3 report must be remediated or explicitly accepted by owner decision.
2. **Dependency Vulnerability Clean Sweep:** Zero High/Critical vulnerabilities in project dependencies (`pip audit` / `npm audit` equivalents).
3. **Secret Isolation Audit:** Verified absence of hardcoded keys, API tokens, or secrets across the entire codebase.
4. **Negative Test Suite for Verifier:** Unit/integration tests proving that tampered certificates, mismatched policy versions, or invalid signatures are unconditionally rejected.
