#!/usr/bin/env python3
"""Rust hybrid verifier parity — Phase 3, Gate 0.

For every DCP 2.1 certificate produced by our Python code, compare:
  (a) Python verify_hybrid output (JSON)
  (b) Rust adie-hybrid-verify output (JSON)
Assert byte-identical strings.
"""
import base64
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from dilithium_py.ml_dsa import ML_DSA_65 as DLP

from protocol.hybrid.certificate import build_dcp21_payload, attach_signatures
from protocol.hybrid.sign import sign_hybrid
from protocol.hybrid.verify import verify_hybrid, HybridVerifyError


RUST_BIN = ROOT / "rust" / "adie-primitives" / "target" / "release" / "adie-hybrid-verify"

PASS_N = FAIL_N = 0


def check(name, cond, detail=""):
    global PASS_N, FAIL_N
    if cond:
        PASS_N += 1
        print(f"[PASS] {name}")
    else:
        FAIL_N += 1
        print(f"[FAIL] {name}: {detail}")


def py_verify(cert, pk_rsa_pem, pk_mldsa_raw, required, audience=None):
    payload = dict(cert)
    payload.pop("signatures", None)
    sigs = cert["signatures"]
    try:
        r = verify_hybrid(
            payload, sigs, required,
            rs256_pub_pem=pk_rsa_pem,
            mldsa65_pub_raw=pk_mldsa_raw,
        )
        return {"status": "VALID", "checks": r["checks"]}
    except HybridVerifyError as e:
        return {"status": "INVALID", "code": e.code,
                "message": str(e)[:200]}


def rust_verify(cert, pk_rsa_pem, pk_mldsa_raw, required, audience=None):
    inp = {
        "cert": cert,
        "public_keys": {
            "RS256": pk_rsa_pem.decode() if isinstance(pk_rsa_pem, bytes) else pk_rsa_pem,
            "ML-DSA-65": pk_mldsa_raw.hex() if isinstance(pk_mldsa_raw, bytes) else pk_mldsa_raw,
        },
        "required_algs": required,
    }
    if audience:
        inp["expected_audience"] = audience
    r = subprocess.run([str(RUST_BIN)], input=json.dumps(inp),
                       capture_output=True, text=True, timeout=30)
    try:
        return json.loads(r.stdout.strip())
    except Exception:
        return {"status": "PARSE_FAIL", "raw": r.stdout[:200], "stderr": r.stderr[:200]}


def make_cert():
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
        claim_id="parity-001",
        issuer_did="did:adie:issuer-001",
        issuer_key_id="sha256:" + "0" * 64,
        subject={"model_id": "credit-v7"},
        request={"id": "r1"},
        context={"locale": "en"},
        policy={"id": "credit-risk", "version": "7"},
        model={"id": "credit-v7"},
        data={"commitment": "sha256:" + "c" * 64},
        runtime={"measurement": "sha256:" + "d" * 64},
        output={"result": "REJECTED"},
        binding={"audience": "com.example.deployment", "purpose": 7,
                 "resource": "model://sha256:" + "a" * 64,
                 "request_hash": "sha256:" + "0" * 64,
                 "nonce": "a" * 32, "certificate_id": "parity-001"},
        temporal={"issued_at": "2026-10-07T00:00:00Z"},
        evidence={"attestations": []},
        authoring={"compiler": "adie-0.1"},
    )
    sigs = sign_hybrid(payload, rsa_pub_pem, rsa_priv_pem, mldsa_pk, mldsa_sk)
    cert = attach_signatures(payload, sigs)
    return cert, rsa_pub_pem, mldsa_pk, rsa_priv_pem, mldsa_sk


def main():
    print("=" * 72)
    print("ADIE hybrid verifier parity — Python vs Rust (DCP 2.1)")
    print("=" * 72)

    if not RUST_BIN.exists():
        print(f"MISSING {RUST_BIN}")
        sys.exit(1)

    cert, rsa_pub_pem, mldsa_pk, _, _ = make_cert()
    required = ["RS256", "ML-DSA-65"]

    # R01: happy path
    py = py_verify(cert, rsa_pub_pem, mldsa_pk, required)
    rs = rust_verify(cert, rsa_pub_pem, mldsa_pk, required)
    check("R01 both VALID",
          py.get("status") == "VALID" and rs.get("status") == "VALID",
          f"py={py} rs={rs}")
    check("R02 checks maps equal",
          py.get("checks") == rs.get("checks"),
          f"py={py.get('checks')} rs={rs.get('checks')}")

    # R03: RS256-only required
    py = py_verify(cert, rsa_pub_pem, mldsa_pk, ["RS256"])
    rs = rust_verify(cert, rsa_pub_pem, mldsa_pk, ["RS256"])
    check("R03 RS256-only both VALID",
          py.get("status") == "VALID" and rs.get("status") == "VALID")

    # R04: ML-DSA-only required
    py = py_verify(cert, rsa_pub_pem, mldsa_pk, ["ML-DSA-65"])
    rs = rust_verify(cert, rsa_pub_pem, mldsa_pk, ["ML-DSA-65"])
    check("R04 ML-DSA-only both VALID",
          py.get("status") == "VALID" and rs.get("status") == "VALID")

    # R05: duplicate alg
    cert_dup = dict(cert)
    cert_dup["signatures"] = [cert["signatures"][0], cert["signatures"][0]]
    py = py_verify(cert_dup, rsa_pub_pem, mldsa_pk, ["ML-DSA-65"])
    rs = rust_verify(cert_dup, rsa_pub_pem, mldsa_pk, ["ML-DSA-65"])
    check("R05 duplicate alg codes match",
          py.get("code") == rs.get("code") == "E_SIGNATURE_DUPLICATE_ALG",
          f"py={py.get('code')} rs={rs.get('code')}")

    # R06: unknown alg
    cert_unk = dict(cert)
    cert_unk["signatures"] = [{"alg": "ED25519", "key_id": "sha256:" + "0"*64, "value": "base64:AAAA"}]
    py = py_verify(cert_unk, rsa_pub_pem, mldsa_pk, ["ED25519"])
    rs = rust_verify(cert_unk, rsa_pub_pem, mldsa_pk, ["ED25519"])
    check("R06 unknown alg codes match",
          py.get("code") == rs.get("code") == "E_SIGNATURE_UNKNOWN_ALG",
          f"py={py.get('code')} rs={rs.get('code')}")

    # R07: downgrade (required both, only RS256 present)
    cert_rs = dict(cert)
    cert_rs["signatures"] = [s for s in cert["signatures"] if s["alg"] == "RS256"]
    py = py_verify(cert_rs, rsa_pub_pem, mldsa_pk, required)
    rs = rust_verify(cert_rs, rsa_pub_pem, mldsa_pk, required)
    check("R07 downgrade codes match",
          py.get("code") == rs.get("code") == "E_SIGNATURE_DOWNGRADE",
          f"py={py.get('code')} rs={rs.get('code')}")

    # R08: tampered output (both must reject)
    cert_t = json.loads(json.dumps(cert))
    cert_t["output"]["result"] = "APPROVED"
    py = py_verify(cert_t, rsa_pub_pem, mldsa_pk, required)
    rs = rust_verify(cert_t, rsa_pub_pem, mldsa_pk, required)
    check("R08 tampered output both INVALID",
          py.get("status") == "INVALID" and rs.get("status") == "INVALID",
          f"py={py.get('code')} rs={rs.get('code')}")
    check("R09 tampered output codes match",
          py.get("code") == rs.get("code"),
          f"py={py.get('code')} rs={rs.get('code')}")

    # R10: tampered ML-DSA signature
    bad = [dict(s) for s in cert["signatures"]]
    for s in bad:
        if s["alg"] == "ML-DSA-65":
            s["value"] = "base64:" + base64.b64encode(b"\x00" * 3309).decode()
    cert_bad = dict(cert)
    cert_bad["signatures"] = bad
    py = py_verify(cert_bad, rsa_pub_pem, mldsa_pk, required)
    rs = rust_verify(cert_bad, rsa_pub_pem, mldsa_pk, required)
    check("R10 tampered ML-DSA codes match",
          py.get("code") == rs.get("code") == "E_SIGNATURE_HYBRID_INVALID",
          f"py={py.get('code')} rs={rs.get('code')}")

    # R11: tampered RS256 signature
    bad = [dict(s) for s in cert["signatures"]]
    for s in bad:
        if s["alg"] == "RS256":
            s["value"] = "base64:" + base64.b64encode(b"\x00" * 256).decode()
    cert_bad = dict(cert)
    cert_bad["signatures"] = bad
    py = py_verify(cert_bad, rsa_pub_pem, mldsa_pk, required)
    rs = rust_verify(cert_bad, rsa_pub_pem, mldsa_pk, required)
    check("R11 tampered RS256 codes match",
          py.get("code") == rs.get("code") == "E_SIGNATURE_HYBRID_INVALID",
          f"py={py.get('code')} rs={rs.get('code')}")

    # R12: different public key
    rsa2 = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    rsa2_pub = rsa2.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo)
    mldsa2_pk, _ = DLP.key_derive(bytes([0x43] * 32))
    py = py_verify(cert, rsa2_pub, mldsa2_pk, required)
    rs = rust_verify(cert, rsa2_pub, mldsa2_pk, required)
    check("R12 wrong keys codes match",
          py.get("code") == rs.get("code"),
          f"py={py.get('code')} rs={rs.get('code')}")

    # R13: empty signatures
    cert_e = dict(cert)
    cert_e["signatures"] = []
    py = py_verify(cert_e, rsa_pub_pem, mldsa_pk, required)
    rs = rust_verify(cert_e, rsa_pub_pem, mldsa_pk, required)
    check("R13 empty signatures codes match",
          py.get("code") == rs.get("code"),
          f"py={py.get('code')} rs={rs.get('code')}")

    print()
    print("=" * 72)
    print(f"TOTAL: {PASS_N + FAIL_N} | PASS: {PASS_N} | FAIL: {FAIL_N}")
    print("=" * 72)
    sys.exit(0 if FAIL_N == 0 else 1)


if __name__ == "__main__":
    main()
