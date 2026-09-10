# DC-038 — EnterpriseGuard ADIE Compliance Matrix

**Document purpose:** Map EnterpriseGuard ADIE capabilities to globally recognized security standards and frameworks.
**Status:** Draft for review
**Generated:** 2026-09-01
**Owner approval required before commercial use.**

---

## 1. Standards Overview

| Standard / Framework | Domain | Relevance to ADIE | Target Status |
|----------------------|--------|-------------------|---------------|
| ISO/IEC 27001 | Information Security Management | Governance, risk, audit | Planned |
| SOC 2 Type II | Trust Services (Security, Availability) | Continuous monitoring, evidence | Planned |
| NIST SP 800-53 | Federal security controls | Control mapping, traceability | Planned |
| GDPR | Data protection (EU) | Log integrity, consent, audit | Planned |
| PCI DSS | Payment card security | Tamper-evident audit trails | Planned |
| HIPAA | Health information security | Access controls, audit logs | Planned |
| CIS Controls | Practical cyber defense | Baseline hardening, monitoring | Planned |
| OWASP ASVS | Application security verification | Secure development, validation | Planned |
| MITRE ATT&CK | Threat modeling and coverage | Detection mapping, attack taxonomy | Planned |
| STIX/TAXII | Threat intelligence exchange | Future integration for threat feeds | Planned |
| Common Criteria (ISO/IEC 15408) | Formal security evaluation | Assurance levels, formal claims | Deferred |

---

## 2. ADIE Capability Mapping

| ADIE Capability | ISO 27001 | SOC 2 | NIST 800-53 | GDPR | PCI DSS | HIPAA | CIS | OWASP ASVS | MITRE ATT&CK |
|-----------------|-----------|--------|-------------|------|---------|-------|-----|------------|---------------|
| Decision Plane separation | A.8.1 | CC6.3 | AC-3 | Art. 25 | Req. 7 | §164.312 | 3.3 | V4.1.1 | n/a |
| Governance audit chain | A.12.4 | CC7.2 | AU-2 | Art. 30 | Req. 10 | §164.312 | 8.2 | V4.5.1 | n/a |
| Integrity monitoring | A.14.2 | CC7.1 | SI-7 | Art. 32 | Req. 11 | §164.312 | 3.10 | V4.5.3 | n/a |
| Time-drift detection | A.12.4 | CC6.1 | AU-8 | Art. 32 | Req. 10 | §164.312 | 8.2 | V4.5.1 | n/a |
| Protected core isolation | A.8.3 | CC6.1 | SC-7 | Art. 25 | Req. 7 | §164.312 | 3.12 | V4.1.2 | n/a |
| Ephemeral archiving | A.12.3 | CC7.2 | AU-11 | Art. 5 | Req. 10 | §164.312 | 8.2 | V4.5.2 | n/a |

---

## 3. Current Evidence Checklist

- [x] tools/checklist.py exists and executes
- [x] tools/integrity_monitor.py exists and validates baseline
- [x] tools/audit_chain.py exists and validates hash chain
- [x] tools/time_drift.py exists and checks timestamp ordering
- [x] tools/ephemeral_archiver.py exists and archives logs
- [x] tools/installer.py exists and validates repository
- [x] tools/uninstall.py exists and removes safely
- [ ] External penetration test (not yet performed)
- [ ] Red team exercise (not yet performed)
- [ ] Formal third-party audit (not yet performed)

---

## 4. Next Steps for Compliance

1. Complete formal mapping to ISO/IEC 27001 Annex A controls.
2. Define SOC 2 trust services criteria evidence per ADIE component.
3. Map NIST SP 800-53 controls to ADIE modules.
4. Draft GDPR data protection impact assessment for log handling.
5. Prepare PCI DSS evidence for audit trail integrity.
6. Document HIPAA administrative and technical safeguards.
7. Implement CIS hardening baseline for deployment.
8. Align development lifecycle with OWASP ASVS.
9. Define MITRE ATT&CK detection coverage goals.
10. Evaluate STIX/TAXII integration for threat intelligence.

---

## 5. Ownership and Review

- **Owner:** Project owner
- **Architect:** ChatGPT (expert reviewer)
- **Reviewer:** Gemini (secondary reviewer)
- **Execution:** Qwen (implementation only)

**This document remains a draft until formally approved by the owner.**
