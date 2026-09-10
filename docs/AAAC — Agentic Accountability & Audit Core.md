# AAAC — Agentic Accountability & Audit Core

## Technical Whitepaper  
**Version 0.2**  
**Date: 2026-09-07**

---

## 1. Executive Summary

AAAC is a sovereign proof layer that provides tamper-evident, cryptographically verifiable records of AI agent actions. It addresses a critical gap in enterprise AI adoption: the inability to prove that an agent acted within its authority, used correct data, and that its decision record has not been altered.

AAAC combines a hardware identity, a signed hash chain (Innocence Chain), dynamic compliance rules, trusted timestamps (RFC 3161), and optional blockchain anchoring to create an audit trail that is both technically robust and legally defensible.

This whitepaper describes the architecture, core components, security properties, integration approach, and roadmap.

---

## 2. Problem Statement

AI agents are increasingly used in high-stakes contexts—credit scoring, fraud detection, customer service, and regulatory reporting. However, existing monitoring tools such as LangSmith and Langfuse provide **observability**, not **proof**. They can show what happened, but they cannot prove that the recorded events are authentic, untampered, and compliant with internal policies.

Key challenges:

- **Non-repudiation**: logs can be edited by system administrators.
- **Regulatory pressure**: EU AI Act Article 12 requires automatic recording of events for high-risk systems; Article 14 requires effective human oversight.
- **Lack of compliance automation**: organizations manually compile evidence during audits, leading to high cost and risk.
- **No standardized trust anchor**: no widely adopted mechanism to bind agent actions to a verifiable, immutable record.

---

## 3. Solution Overview

AAAC is a **proof layer** that sits above existing monitoring tools. It does not replace observability; it enhances it by adding cryptographic integrity, policy enforcement, and external anchoring.

### Core principles

1. **Sovereignty**: private keys and proof generation are controlled by the deploying organization.
2. **Tamper-evident history**: any change to historical records breaks the hash chain.
3. **Dynamic compliance**: events are evaluated against configurable rules before being accepted.
4. **External verifiability**: a public verifier allows third parties to validate the chain without trusting the system.

---

## 4. Architecture

### 4.1 High-level flow

```
AI Agent → Monitoring Tool (Langfuse/LangSmith)
             ↓
       Event Connector
             ↓
    Compliance Engine (policy check)
             ↓
       Ring Storage (JSONL/SQLite)
             ↓
      Innocence Chain Generation
             ↓
    Signing Backend (RSA/KMS/TPM)
             ↓
    RFC 3161 Timestamp + optional Blockchain Anchor
             ↓
      HTTP API / Dashboard / Verifier
```

### 4.2 Components

| Component | File | Purpose |
|-----------|------|---------|
| Hardware Identity | `tools/hardware_identity.py` | Binds proof to a specific machine/hardware |
| Genesis Seed | `tools/genesis_seed.py` | Proves origin of chain |
| Relational Memory | `tools/relational_memory.py` | Stores causal links between events |
| Distributed Proof | `tools/distributed_proof.py` | Splits evidence into three shards |
| Innocence Chain | `tools/innocence_chain.py` | Signed hash chain with genesis signature |
| Compliance Engine | `tools/compliance_engine.py` | Rules-based policy evaluation |
| Native Connectors | `tools/native_connectors.py` | Fetch traces from LangSmith/Langfuse |
| Blockchain Anchor | `tools/blockchain_anchor.py` | Anchor ring hashes on Ethereum (Sepolia) |
| Sovereign HTTP Server | `tools/sovereign_http_server.py` | REST API with dashboard and reports |
| Open Verifier | `tools/open_verifier.py` | Third-party chain verification |

---

## 5. Cryptographic Details

### 5.1 Innocence Chain

Each ring in the chain contains:

- `prev_ring_hash`
- `identity_key`
- `integrity_status`
- `relational_memory_snapshot`
- `realtime_events_hash`
- `agent_events_hash`
- `chain_id`
- `signature` (RSA-2048)
- `genesis_signature` (first ring only)
- `rfc3161_token` (trusted timestamp)
- `tsa_provider`

The ring hash is computed as:

```
sha256(prev_ring_hash + identity_key + integrity_status + snapshot + realtime_hash + chain_id + agent_events_hash)
```

### 5.2 Signing

- Default: RSA-2048 using local private key.
- Pluggable backend supports:
  - `local` RSA (default)
  - `mock` (for development)
  - `aws_kms` (cloud HSM)
  - `tpm` (hardware TPM)
- Selected via `AAAC_SIGNING_BACKEND` environment variable.

### 5.3 Trusted Timestamp (RFC 3161)

Each ring requests a timestamp token from a pool of TSA providers (Certum, FreeTSA, DFN). The provider that succeeds is recorded. The token is verified against a CA chain if `AAAC_TSA_CAFILE` is set.

### 5.4 Blockchain Anchoring

The `ring_hash` can be written to a smart contract on Ethereum (currently Sepolia testnet). This provides public immutability and a time-stamped proof of existence.

---

## 6. Dynamic Compliance Engine

The engine evaluates events against a JSON policy with:

- **Default action**: `deny` or `allow`.
- **Rules**: each with priority, type (`allow`, `deny`, `require`, `deny_if_exceed`, `deny_if_match`).
- **Conditions**: support comparison (`==`, `!=`, `>`, `<`, `>=`, `<=`, `in`, `contains`, `matches_regex`) and logical `AND`/`OR`.
- **Per-agent and per-command policies**.

Example rules:

- Allow standard commands (`check_balance`, `transfer_funds`, etc.)
- Deny high-risk transfers above a threshold.
- Deny commands matching forbidden regex (`hack`, `sudo`, `rm -rf`).
- Require core fields (`timestamp`, `agent_id`, `trace_id`, `command`, `actor_type`).

Non-compliant events are either rejected (default) or flagged with a reason.

---

## 7. Integration

AAAC connects to existing monitoring systems through **native connectors**:

- **Langfuse**: fetch observations from `/api/public/v2/observations`.
- **LangSmith**: fetch runs via API.

The unified CLI (`tools/aaac_cli.py`) performs:

```
fetch → compliance check → store → generate ring → verify chain
```

---

## 8. Security Properties

- **Tamper-evident**: any modification to a ring breaks all subsequent hashes.
- **Non-repudiation**: signatures generated with private keys held by the operator.
- **Time-stamped**: RFC 3161 tokens prove existence before a certain time.
- **Immutable anchoring** (optional): ring hashes on public blockchain.
- **Fault-tolerant**: multiple TSA providers, duplicate avoidance, and atomic writes.
- **Least privilege**: private keys stored outside repository, file permissions enforced.

---

## 9. Known Limitations

- **No qualified eIDAS timestamp (QTSP)**: current TSA providers are free or unqualified. Production use may require a Qualified Trust Service Provider.
- **No hardware security module (HSM) integration tested**: code ready for AWS KMS/TPM, but not tested with real hardware.
- **No formal external audit**: internal security tests only.
- **HTML sovereign verifier**: in development; official verifiers (`open_verifier.py`, `/verify-chain`) work.

---

## 10. Test Results Summary

| Test | Result |
|------|--------|
| Unit tests (core components) | 5/5 passed |
| Advanced security tests (DoS, TOCTOU, Chain Spoofing, etc.) | Passed / mitigated |
| Bandit static analysis | High: 0, Medium: 0, Low: 35 (reduced) |
| Real-world agent simulation | 20 agent events captured, chained, verified |
| Blockchain anchoring | Successfully anchored on Sepolia testnet |
| Compliance engine | Allowed commands pass, forbidden commands denied |

---

## 11. Roadmap

- **Short term**:  
  - Migrate blockchain anchoring to mainnet or L2 (Arbitrum/Optimism).  
  - Replace free TSA with eIDAS-qualified QTSP.  
  - Integrate AWS KMS/TPM for production HSM.

- **Medium term**:  
  - Complete HTML sovereign verifier.  
  - Add role-based access control (RBAC).  
  - Implement distributed verification network (IPFS + smart contracts).  
  - Obtain SOC 2 Type I / ISO 42001.

- **Long term**:  
  - Multi-chain anchoring (Ethereum, Polkadot, Cosmos).  
  - Confidential computing (SGX/Nitro Enclaves) for signing.  
  - Standardization as an open protocol.

---

## 12. Conclusion

AAAC transforms AI agent accountability from a manual, trust-based process into a cryptographically enforced, automatically verifiable system. Its combination of signed hash chains, dynamic compliance, trusted timestamps, and blockchain anchoring is unique in the current market. The project is ready for pilot deployments and further hardening toward production-grade financial use.
