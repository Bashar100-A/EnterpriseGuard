# AAAC Legal Use Case — Credit Decision by AI Agent

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
