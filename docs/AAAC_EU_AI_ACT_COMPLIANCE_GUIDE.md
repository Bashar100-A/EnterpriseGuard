# AAAC Compliance Guide — EU AI Act Articles 12 & 14

**Version:** 0.1.0  
**Date:** 2026-09-06  
**Status:** Draft for internal review and customer discussions

## Purpose

This document explains how AAAC (Agentic Accountability & Audit Core) can help financial institutions satisfy key obligations under the EU AI Act for high-risk AI systems, specifically:

- Article 12: Record-keeping (automatic logging)
- Article 14: Human oversight

It is written for compliance officers, data protection officers, and AI governance leads.

## Important Disclaimer

AAAC is a technical proof layer, not a legal service. This document does **not** constitute legal advice. Compliance with the EU AI Act requires a case-by-case legal assessment by qualified professionals. The statements below are based on our understanding of the regulation and should be validated by your legal team.

---

## 1. How AAAC Addresses Article 12 (Record-keeping)

Article 12 requires high-risk AI systems to technically allow for the automatic recording of events (logs) over the lifetime of the system, ensuring a level of traceability appropriate to the intended purpose.

### Key Requirements and AAAC Mapping

| Requirement | How AAAC Helps |
|-------------|----------------|
| Logs must be **tamper-resistant** | AAAC creates a hash chain (Innocence Chain) using SHA-256. Each new event is linked to the previous one, making undetected modification infeasible. |
| Logs must cover **lifetime of the system** | The chain is designed to be append-only and can be extended continuously. Retention can be configured (e.g., 6 months minimum per Art. 12(5)). |
| Logs must record **periods of use** | Each ring (block) includes timestamps (both system and external trusted time via RFC 3161) and event summaries. |
| Logs must support **reconstruction of events** | The chain stores hashes of agent inputs, outputs, and actions, enabling forensic verification of what happened. |
| **Non-repudiation** | Each ring is digitally signed using RSA-2048. The private key is stored outside the repository (e.g., in an HSM or secure environment), providing non-repudiation. |

### Current Implementation Status

- **Hash chain:** Fully implemented and tested (`VERIFIED_OK`).
- **Digital signatures:** Implemented using RSA-2048 with genesis signature to prevent chain replacement.
- **Trusted timestamp:** Using free TSA (Certum) for demonstration; production should use a Qualified Trust Service Provider (QTSP) under eIDAS.
- **Storage:** Events stored in `ring_storage.jsonl` and hashed into the chain. For production, recommend WORM storage or append-only database.

### Gap Analysis

| Feature | Current | Required for EU AI Act |
|---------|---------|------------------------|
| Tamper-evident chain | ✅ | ✅ |
| Digital signature | ✅ (RSA-2048) | ✅ (qualified seal recommended) |
| Trusted timestamp | ⚠️ Free TSA (demo only) | ⚠️ QTSP eIDAS qualified timestamp |
| Retention | ⚠️ Manual | ⚠️ Configurable, at least 6 months |
| Access control | ⚠️ Basic | ⚠️ Role-based, audit of access |

**Conclusion:** The core mechanism is in place, but additional hardening is needed for full legal reliance. AAAC can be integrated with customer-provided TSA/HSM to meet higher assurance levels (BYO-TSA/BYO-HSM model).

---

## 2. How AAAC Addresses Article 14 (Human Oversight)

Article 14 requires high-risk AI systems to be designed so that they can be effectively overseen by natural persons.

### Key Requirements and AAAC Mapping

| Requirement | How AAAC Helps |
|-------------|----------------|
| Oversight must be **effective and exercisable** | AAAC records every agent action, enabling supervisors to review decisions and intervene. |
| Human intervention must be **possible at any time** | The dashboard and event API allow real-time monitoring and alerting (future enhancement: alert on abnormal events). |
| Oversight measures must be **proportionate** | The proof layer does not replace human judgment but provides an audit trail that supports oversight. |
| **Identification of the human operator** | AAAC can log human interventions as events with actor type `human` (to be implemented). Currently records `actor_type: agent`. |

### Current Implementation Status

- **Logging of human interventions:** Not yet implemented (planned). Current system only records agent actions. We recommend adding an API endpoint for human approvals/rejections, which would be signed and included in the chain.

### Gap Analysis

| Feature | Current | Required |
|---------|---------|----------|
| Record of human interventions | ❌ | ✅ |
| Signing of human interventions | ❌ | ✅ (using same chain) |
| Real-time monitoring | ✅ (dashboard, events) | ✅ |
| Alerts | ❌ | ⚠️ recommended |

**Conclusion:** Article 14 compliance is partially addressed. The technical foundation supports adding human oversight events easily. We recommend implementing a `human_action` event type in the next iteration.

---

## 3. Summary and Recommendations

1. **Technical readiness:** AAAC's hash chain and digital signatures provide a strong basis for Article 12.
2. **For legal reliance in EU:** Integrate with a Qualified Trust Service Provider (QTSP) for timestamps and electronic seals (eIDAS).
3. **For Article 14:** Add human intervention event type and ensure it is signed and included in the chain.
4. **Retention:** Implement configurable retention and WORM storage for production.
5. **Access control:** Add role-based access control for the dashboard and APIs.

This document will be updated as the product evolves.

---

*End of Guide*
