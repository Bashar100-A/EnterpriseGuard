# Recipe 04 — Verify Proof by a Third Party

**Scenario:** An external auditor verifies the chain without trusting your systems.

## Prerequisites

```bash
# Obtain from the deploying organization:
#   - tools/innocence_chain.json
#   - tools/hardware_identity.json
#   - ~/.enterpriseguard/keys/public_key.pem
#   - tools/genesis_public_key.pem
```

## Steps

```bash
# 1. Place the received artifacts in a clean directory
mkdir /tmp/audit && cd /tmp/audit
# Copy the four files above into the same relative layout

# 2. Run the open verifier (no trust in the producer required)
python3 tools/open_verifier.py

# 3. Expected output
#    VALID: chain is authentic
```

**Result:** The auditor confirms the chain is intact and signed by the
producer's published public key, without needing access to the producer's
private systems or internal tooling beyond the verifier itself.
