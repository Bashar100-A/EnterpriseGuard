#!/usr/bin/env python3
"""Wire bridge: adie/ -> protocol/ (one direction)."""
import sys, json, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

P = F = 0
def check(n, c, d=""):
    global P, F
    if c: P += 1; print(f"[PASS] {n}")
    else: F += 1; print(f"[FAIL] {n}: {d}")

print("="*72); print("Wire bridge"); print("="*72)

# 1. Import works
try:
    from enterpriseguard.adie.canonical.wire_bridge import (
        envelope_from_certificate, parse_envelope_to_certificate,
        WireBridgeError,
    )
    check("W01 bridge import", True)
except Exception as e:
    check("W01 bridge import", False, str(e)); sys.exit(1)

# 2. Direction: protocol/ does NOT import enterpriseguard
proto = ROOT / "protocol"
leaks = []
for p in proto.rglob("*.py"):
    txt = p.read_text(errors='ignore')
    if "src.enterpriseguard" in txt or "from enterpriseguard" in txt:
        leaks.append(str(p.relative_to(ROOT)))
check("W02 protocol/ does NOT import enterpriseguard.adie",
      len(leaks) == 0, f"leaks: {leaks}")

# 3. Envelope round-trip via bridge
cert = {
    "dcp_version": "2.1", "claim_id": "bridge-t01",
    "issuer": {"did": "did:adie:test", "key_id": "sha256:" + "0"*64},
    "subject": {"model_id": "credit-v7"},
    "request": {"id": "r1"},
    "context": {"locale": "en"},
    "policy": {"id": "credit-risk", "version": "7"},
    "model": {"id": "model-v1"},
    "data": {"commitment": "sha256:" + "c"*64},
    "runtime": {"measurement": "sha256:" + "d"*64},
    "output": {"result": "REJECTED"},
    "binding": {"audience": "com.example", "purpose": 7,
                "resource": "model://t01",
                "request_hash": "sha256:" + "e"*64,
                "nonce": "a"*32, "certificate_id": "bridge-t01"},
    "temporal": {"issued_at": "2026-10-07T00:00:00Z"},
    "evidence": {"attestations": []},
    "authoring": {"template_digest": "sha256:"+"0"*64,
                  "parameter_digest": "sha256:"+"1"*64,
                  "compiler_digest": "sha256:"+"2"*64,
                  "acl_version": "0.1",
                  "canonical_ast_digest": "sha256:"+"3"*64,
                  "meta_manifest_digest": "sha256:"+"4"*64},
    "proofs": [],
    "claim_root": "sha256:" + "a"*64,
    "signatures": [
        {"alg": "RS256", "key_id": "sha256:"+"0"*64,
         "value": "base64:" + __import__("base64").b64encode(b"\x41"*256).decode("ascii")},
        {"alg": "ML-DSA-65", "key_id": "sha256:"+"1"*64,
         "value": "base64:" + __import__("base64").b64encode(b"\x42"*3309).decode("ascii")},
    ],
}

try:
    env = envelope_from_certificate(cert)
    check("W03 envelope built via bridge", isinstance(env, bytes) and len(env) > 100)
except WireBridgeError as e:
    check("W03 envelope built via bridge", False, str(e)[:100])
    env = None

if env:
    try:
        cert2 = parse_envelope_to_certificate(env)
        check("W04 envelope parsed via bridge", cert2["claim_id"] == "bridge-t01")
        check("W05 round-trip preserves issuer", cert2["issuer"] == cert["issuer"])
        check("W06 round-trip preserves signatures",
              len(cert2["signatures"]) == len(cert["signatures"]))
    except WireBridgeError as e:
        check("W04 envelope parsed via bridge", False, str(e)[:100])

# 4. Missing binary path handling
from enterpriseguard.adie.canonical import wire_bridge as wb
check("W07 WireBridgeError class exists", issubclass(wb.WireBridgeError, Exception))

print(f"\nTOTAL: {P+F} | PASS: {P} | FAIL: {F}")
sys.exit(0 if F == 0 else 1)
