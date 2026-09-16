# ADIE Threat Model v1.0

## Scope
ADIE is an independent control plane governing AI-driven enterprise decisions.
Out of scope: model training, inference quality, physical infrastructure.

## Adversaries
1. **Malicious Insider** — has admin access to the ledger server.
2. **External Attacker** — has network access, tries to inject/replay decisions.
3. **Compromised AI Model** — produces adversarially crafted decisions.
4. **Supply Chain Attacker** — modifies model weights or dependencies.

## Trust Boundaries
- Ledger storage: trusted for integrity, untrusted for confidentiality.
- Clock source: untrusted, guarded by Genesis Anchor + monotonic checks.
- Execution plane: fully untrusted, never writes to ledger.

## Attack Vectors & Mitigations
| Vector | ATT&CK | Mitigation |
|---|---|---|
| Time Spoofing | T1070.006 | Genesis timestamp + monotonic rollback rejection |
| TOCTOU | T1548 | Versioned causal lock |
| Hard Fork | T1565.002 | HMAC-signed chain + genesis isolation |
| DoS | T1499 | Token-bucket rate limiting |
| Supply Chain | T1195.001 | Static SHA-256 model verification |

## Assumptions
- Ed25519 private key is stored in HSM or OS keyring with 0600 perms.
- Genesis secret is generated via CSPRNG at first boot.
- Operators rotate signing keys quarterly.
