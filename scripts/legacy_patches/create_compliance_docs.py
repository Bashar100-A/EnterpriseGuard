import sys, shutil, tempfile, os
from pathlib import Path
from datetime import datetime, timezone

sys.dont_write_bytecode = True
ROOT = Path('.')

def atomic_write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f'.{path.name}.', suffix='.tmp', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as fh:
            fh.write(content)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise

guide = '''# AAAC Compliance Guide — EU AI Act Articles 12 & 14

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
'''

use_case = '''# AAAC Legal Use Case — Credit Decision by AI Agent

**Version:** 0.1.0  
**Date:** 2026-09-06  
**Status:** Draft for internal use and customer conversations

## Scenario

A European bank (the "Bank") uses an AI agent to assist in creditworthiness assessments for loan applications. The agent automatically processes certain applications and issues a recommendation (approve or deny). In one case, the agent denies a loan to a customer, who later claims discrimination and files a lawsuit.

The Bank must demonstrate that:

1. The decision was authorized and within the agent's permitted scope.
2. The decision was based on correct and complete data.
3. The record of the decision has not been altered after the fact.

## How AAAC Helps the Bank

### 1. Proving Authorization and Scope

- The agent's actions are recorded in the Innocence Chain with metadata including `agent_id`, `command`, and a hash of the input. The chain's genesis signature proves the chain originated from a known, trusted system (Hardware Identity + Genesis Seed).
- The Bank can show that the agent was configured with specific policies (e.g., "only use approved credit models") and that the action falls within those policies. This is supported by the `actor_type: agent` and the signed event.

### 2. Proving Data Integrity and Correctness

- For each decision, the input data (e.g., customer information, credit score) is hashed and included in the chain. Any subsequent change to that data would produce a different hash, breaking the chain. Therefore, the Bank can prove the data used at decision time has not been tampered with.

### 3. Proving Non-Repudiation and Timeliness

- Each ring is digitally signed (RSA-2048) and includes a trusted timestamp from a TSA (e.g., Certum for demo; QTSP in production). This proves the decision record existed at a specific time and cannot be backdated.

### 4. Providing a Verifiable Audit Trail

- The Bank can run the open-source verifier (`tools/open_verifier.py`) to independently confirm the chain's integrity without relying on the Bank's internal systems. This provides transparency to the court.

## Legal Considerations

- Under eIDAS, qualified electronic timestamps and seals carry a presumption of integrity and authenticity. Using a QTSP would strengthen the evidentiary value.
- Under the EU AI Act Article 12, the Bank is required to keep logs for high-risk AI systems. A tamper-evident chain helps satisfy this.
- Under Article 14, the Bank must demonstrate effective human oversight. If a human reviewed and approved the decision, that intervention should also be logged and signed (planned).

## Conclusion

AAAC provides a technical foundation for proving the integrity and authenticity of AI agent decisions. While not a substitute for legal advice, it can serve as a robust digital evidence layer in disputes and regulatory audits.

---

*End of Use Case*
'''

# إنشاء الملفين
atomic_write(ROOT / 'docs' / 'AAAC_EU_AI_ACT_COMPLIANCE_GUIDE.md', guide)
atomic_write(ROOT / 'docs' / 'AAAC_LEGAL_USE_CASE.md', use_case)

print("Created AAAC_EU_AI_ACT_COMPLIANCE_GUIDE.md and AAAC_LEGAL_USE_CASE.md")
