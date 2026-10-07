#!/usr/bin/env python3
"""3D-R1 FINDING-3D-01: real cryptographic verification in E2E."""
import sys, copy, base64
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import *
from enterpriseguard.adie.canonical.integration import (
    evaluate_end_to_end, E2EOutcome)

h = Harness("3D-R1 F-01: E2E crypto verification")

cert, rsa_pub, rsa_priv, mldsa_pk, mldsa_sk = make_signed_fixture("cv-1")
evidence = make_evidence()
authority = make_authority()

def _e2e(c, **kw):
    return evaluate_end_to_end(
        certificate=c, evidence=evidence, authority=authority,
        scope="decide", trust_assertions=[], at=T1,
        target_resource_id="res-1", require_wire_roundtrip=False,
        require_crypto_verification=True,
        rs256_pub_pem=rsa_pub, mldsa65_pub_raw=mldsa_pk,
        **kw)

# C01: valid hybrid -> ACCEPTED
r = _e2e(cert)
h.check("C01 valid hybrid -> ACCEPTED", r.outcome is E2EOutcome.ACCEPTED,
        r.rejection_reason)
h.check("C01b crypto stage verified", r.stages.get("crypto") == "verified")

# C02: corrupted RS256 -> REJECTED_CRYPTO
c = copy.deepcopy(cert)
for s in c["signatures"]:
    if s["alg"] == "RS256":
        raw = bytearray(base64.b64decode(s["value"][7:]))
        raw[0] ^= 0xFF
        s["value"] = "base64:" + base64.b64encode(bytes(raw)).decode()
r = _e2e(c)
h.check("C02 corrupted RS256 -> REJECTED_CRYPTO",
        r.outcome is E2EOutcome.REJECTED_CRYPTO, r.rejection_reason)

# C03: valid RS256 alone (PQ removed) -> downgrade -> REJECTED_CRYPTO
c = copy.deepcopy(cert)
c["signatures"] = [s for s in c["signatures"] if s["alg"] == "RS256"]
r = _e2e(c)
h.check("C03 RS-only -> REJECTED_CRYPTO (downgrade)",
        r.outcome is E2EOutcome.REJECTED_CRYPTO, r.rejection_reason)

# C04: corrupted ML-DSA-65 -> REJECTED_CRYPTO
c = copy.deepcopy(cert)
for s in c["signatures"]:
    if s["alg"] == "ML-DSA-65":
        raw = bytearray(base64.b64decode(s["value"][7:]))
        raw[100] ^= 0xFF
        s["value"] = "base64:" + base64.b64encode(bytes(raw)).decode()
r = _e2e(c)
h.check("C04 corrupted ML-DSA-65 -> REJECTED_CRYPTO",
        r.outcome is E2EOutcome.REJECTED_CRYPTO, r.rejection_reason)

# C05: PQ-only -> REJECTED_CRYPTO (downgrade)
c = copy.deepcopy(cert)
c["signatures"] = [s for s in c["signatures"] if s["alg"] == "ML-DSA-65"]
r = _e2e(c)
h.check("C05 PQ-only -> REJECTED_CRYPTO (downgrade)",
        r.outcome is E2EOutcome.REJECTED_CRYPTO, r.rejection_reason)

# C06: signature bytes tampered by 1 in middle (both) -> REJECTED_CRYPTO
c = copy.deepcopy(cert)
for s in c["signatures"]:
    raw = bytearray(base64.b64decode(s["value"][7:]))
    raw[len(raw)//2] ^= 0x01
    s["value"] = "base64:" + base64.b64encode(bytes(raw)).decode()
r = _e2e(c)
h.check("C06 both sigs tampered -> REJECTED_CRYPTO",
        r.outcome is E2EOutcome.REJECTED_CRYPTO, r.rejection_reason)

# C07: signatures missing -> REJECTED_CRYPTO
c = copy.deepcopy(cert)
c["signatures"] = []
r = _e2e(c)
h.check("C07 empty signatures -> REJECTED_CRYPTO",
        r.outcome is E2EOutcome.REJECTED_CRYPTO, r.rejection_reason)

# C08: malformed base64 in value -> REJECTED_CRYPTO
c = copy.deepcopy(cert)
c["signatures"][0]["value"] = "base64:!!!not-base64!!!"
r = _e2e(c)
h.check("C08 malformed base64 -> REJECTED_CRYPTO",
        r.outcome is E2EOutcome.REJECTED_CRYPTO, r.rejection_reason)

# C09: valid structure, wrong sig bytes (all zeros) -> REJECTED_CRYPTO
c = copy.deepcopy(cert)
for s in c["signatures"]:
    raw = b"\x00" * (256 if s["alg"] == "RS256" else 3309)
    s["value"] = "base64:" + base64.b64encode(raw).decode()
r = _e2e(c)
h.check("C09 wrong sig bytes (zeros) -> REJECTED_CRYPTO",
        r.outcome is E2EOutcome.REJECTED_CRYPTO, r.rejection_reason)

# C10: valid crypto + revoked trust -> REJECTED_TRUST (not CRYPTO)
r = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=authority,
    scope="decide",
    trust_assertions=[make_revoke_assertion(effective_at=T0)],
    at=T1, target_resource_id="res-1", require_wire_roundtrip=False,
    require_crypto_verification=True,
    rs256_pub_pem=rsa_pub, mldsa65_pub_raw=mldsa_pk)
h.check("C10 valid crypto + revoked -> REJECTED_TRUST (not CRYPTO)",
        r.outcome is E2EOutcome.REJECTED_TRUST, r.rejection_reason)

# C11: crypto verification required but no keys -> REJECTED_CRYPTO
r = evaluate_end_to_end(
    certificate=cert, evidence=evidence, authority=authority,
    scope="decide", trust_assertions=[], at=T1, target_resource_id="res-1",
    require_wire_roundtrip=False, require_crypto_verification=True)
h.check("C11 missing keys -> REJECTED_CRYPTO",
        r.outcome is E2EOutcome.REJECTED_CRYPTO, r.rejection_reason)

h.finish()
