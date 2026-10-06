#!/usr/bin/env python3
"""ADIE E2E hybrid pilot — full DCP 2.1 issue+sign+verify cycle."""
import base64
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from dilithium_py.ml_dsa import ML_DSA_65 as DLP

from protocol.hybrid.certificate import (
    build_dcp21_payload, attach_signatures, emit_certificate,
)
from protocol.hybrid.sign import sign_hybrid
from protocol.hybrid.verify import verify_hybrid, HybridVerifyError


PASS_N = FAIL_N = 0
def check(name, cond, detail=""):
    global PASS_N, FAIL_N
    if cond:
        PASS_N += 1
        print(f"[PASS] {name}")
    else:
        FAIL_N += 1
        print(f"[FAIL] {name}: {detail}")


def make_fixture():
    """Returns a fully populated DCP 2.1 cert + keys."""
    rsa_priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    rsa_priv_pem = rsa_priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption())
    rsa_pub_pem = rsa_priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo)

    mldsa_pk, mldsa_sk = DLP.key_derive(bytes([0x42] * 32))

    payload = build_dcp21_payload(
        claim_id="e2e-001",
        issuer_did="did:adie:issuer-001",
        issuer_key_id="sha256:" + "0" * 64,   # placeholder, replaced below
        subject={"model_id": "credit-v7"},
        request={"id": "dec-4291", "amount": 25000, "currency": "EUR"},
        context={"locale": "en", "region": "EU"},
        policy={"id": "credit-risk", "version": "7"},
        model={"id": "credit-v7"},
        data={"commitment": "sha256:" + "c" * 64},
        runtime={"measurement": "sha256:" + "d" * 64},
        output={"result": "REJECTED", "reason": "low_score"},
        binding={"audience": "com.example.deployment",
                 "purpose": 7,
                 "resource": "model://sha256:" + "a" * 64,
                 "request_hash": "sha256:" + "0" * 64,
                 "nonce": "a" * 32,
                 "certificate_id": "e2e-001"},
        temporal={"issued_at": "2026-10-07T00:00:00Z"},
        evidence={"attestations": []},
        authoring={"compiler": "adie-0.1"},
    )
    sigs = sign_hybrid(payload, rsa_pub_pem, rsa_priv_pem, mldsa_pk, mldsa_sk)
    cert = attach_signatures(payload, sigs)
    return {
        "cert": cert,
        "payload": payload,
        "sigs": sigs,
        "rsa_pub_pem": rsa_pub_pem,
        "rsa_priv_pem": rsa_priv_pem,
        "mldsa_pk": mldsa_pk,
        "mldsa_sk": mldsa_sk,
    }


def main():
    print("=" * 72)
    print("ADIE E2E hybrid pilot — DCP 2.1 issue/sign/verify")
    print("=" * 72)

    f = make_fixture()
    cert = f["cert"]
    payload = f["payload"]
    sigs = f["sigs"]

    # E01: DCP 2.1 version
    check("E01 dcp_version is 2.1", cert["dcp_version"] == "2.1")

    # E02: signatures array has both, sorted
    check("E02 signatures sorted [ML-DSA-65, RS256]",
          [s["alg"] for s in cert["signatures"]] == ["ML-DSA-65", "RS256"],
          f"got {[s['alg'] for s in cert['signatures']]}")

    # E03: claim_root present and well-formed
    check("E03 claim_root format",
          cert["claim_root"].startswith("sha256:") and len(cert["claim_root"]) == 71)

    # E04: payload has no signatures field (TBS-input invariants)
    check("E04 payload has no signatures",
          "signatures" not in payload and "signature" not in payload)

    # E05: verify happy path
    r = verify_hybrid(payload, sigs, ["RS256", "ML-DSA-65"],
                      rs256_pub_pem=f["rsa_pub_pem"],
                      mldsa65_pub_raw=f["mldsa_pk"])
    check("E05 verify VALID", r["status"] == "VALID")

    # E06: verify with signature bytes round-trip via JSON
    cert_roundtrip = json.loads(json.dumps(cert))
    payload_rt = dict(cert_roundtrip)
    del payload_rt["signatures"]
    r = verify_hybrid(payload_rt, cert_roundtrip["signatures"],
                      ["RS256", "ML-DSA-65"],
                      rs256_pub_pem=f["rsa_pub_pem"],
                      mldsa65_pub_raw=f["mldsa_pk"])
    check("E06 verify after JSON roundtrip", r["status"] == "VALID")

    # E07: emit and re-parse
    emitted = emit_certificate(cert)
    reparsed = json.loads(emitted)
    payload_rp = dict(reparsed)
    del payload_rp["signatures"]
    r = verify_hybrid(payload_rp, reparsed["signatures"],
                      ["RS256", "ML-DSA-65"],
                      rs256_pub_pem=f["rsa_pub_pem"],
                      mldsa65_pub_raw=f["mldsa_pk"])
    check("E07 verify after emit+reparse", r["status"] == "VALID")

    # E08: tamper output field — both sigs fail
    cert_t = json.loads(json.dumps(cert))
    cert_t["output"]["result"] = "APPROVED"
    payload_t = dict(cert_t)
    del payload_t["signatures"]
    try:
        verify_hybrid(payload_t, cert_t["signatures"], ["RS256", "ML-DSA-65"],
                      rs256_pub_pem=f["rsa_pub_pem"],
                      mldsa65_pub_raw=f["mldsa_pk"])
        check("E08 tampered output rejected", False, "no raise")
    except HybridVerifyError as e:
        check("E08 tampered output rejected",
              e.code == "E_SIGNATURE_HYBRID_INVALID")

    # E09: tamper claim_root — both fail
    cert_t2 = json.loads(json.dumps(cert))
    cert_t2["claim_root"] = "sha256:" + "f" * 64
    payload_t2 = dict(cert_t2)
    del payload_t2["signatures"]
    try:
        verify_hybrid(payload_t2, cert_t2["signatures"], ["RS256", "ML-DSA-65"],
                      rs256_pub_pem=f["rsa_pub_pem"],
                      mldsa65_pub_raw=f["mldsa_pk"])
        check("E09 tampered claim_root rejected", False, "no raise")
    except HybridVerifyError as e:
        check("E09 tampered claim_root rejected",
              e.code == "E_SIGNATURE_HYBRID_INVALID")

    # E10: strip ML-DSA signature — downgrade attack
    only_rs = [s for s in cert["signatures"] if s["alg"] == "RS256"]
    try:
        verify_hybrid(payload, only_rs, ["RS256", "ML-DSA-65"],
                      rs256_pub_pem=f["rsa_pub_pem"],
                      mldsa65_pub_raw=f["mldsa_pk"])
        check("E10 downgrade rejected", False, "no raise")
    except HybridVerifyError as e:
        check("E10 downgrade rejected", e.code == "E_SIGNATURE_DOWNGRADE")

    # E11: deterministic issue — same inputs → same bytes
    f2 = make_fixture()
    # Note: RSA keys differ, so signatures differ. Only claim_root is stable.
    check("E11 claim_root deterministic given same semantic fields",
          f["cert"]["claim_root"] == f2["cert"]["claim_root"],
          f"c1={f['cert']['claim_root'][:30]} c2={f2['cert']['claim_root'][:30]}")

    print()
    print("=" * 72)
    print(f"TOTAL: {PASS_N + FAIL_N} | PASS: {PASS_N} | FAIL: {FAIL_N}")
    print("=" * 72)
    sys.exit(0 if FAIL_N == 0 else 1)


if __name__ == "__main__":
    main()
