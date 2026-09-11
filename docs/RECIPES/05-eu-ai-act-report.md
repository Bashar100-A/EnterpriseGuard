# Recipe 05 — EU AI Act Compliance Report

**Scenario:** Generate a compliance evidence report for a high-risk AI system.

## Prerequisites

```bash
export SOVEREIGN_HTTP_KEY="<identity_key from tools/hardware_identity.json>"
```

## Steps

```bash
# 1. Start the sovereign HTTP server (background)
python3 tools/sovereign_http_server.py --host 127.0.0.1 --port 8443 &

# 2. Fetch the compliance report
curl -s -H "X-ADIE-Key: $SOVEREIGN_HTTP_KEY" \
  http://127.0.0.1:8443/compliance-report | python3 -m json.tool

# 3. Fetch the chain verification status
curl -s -H "X-ADIE-Key: $SOVEREIGN_HTTP_KEY" \
  http://127.0.0.1:8443/verify-chain | python3 -m json.tool

# 4. Stop the server
kill %1
```

**Result:** A JSON report containing chain ID, ring count, integrity status,
TSA provider, verification result, and the last ring hash — suitable as
Article 12 / Article 14 evidence for an EU AI Act audit.
