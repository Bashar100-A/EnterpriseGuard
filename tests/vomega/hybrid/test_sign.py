#!/usr/bin/env python3
"""Hybrid signer — Python conformance tests."""
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

from protocol.hybrid.sign import (
    sign_hybrid,
    sign_mldsa65,
    sign_rs256,
    mldsa65_key_id_from_public_bytes,
    rs256_key_id_from_public_pem,
)


PASS_N = FAIL_N = 0
def check(name, cond, detail=""):
    global PASS_N, FAIL_N
    if cond:
        PASS_N += 1
        print(f"[PASS] {name}")
    else:
        FAIL_N += 1
        print(f"[FAIL] {name}: {detail}")


def main():
    print("=" * 72)
    print("ADIE hybrid signer — Python conformance")
    print("=" * 72)

    # Prepare keys
    rsa_priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    rsa_priv_pem = rsa_priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption())
    rsa_pub_pem = rsa_priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo)

    xi = bytes([0x42] * 32)
    mldsa_pk, mldsa_sk = DLP.key_derive(xi)

    cert = {"dcp_version": "2.1", "claim_id": "c1"}

    # S01: key_id format
    rs_id = rs256_key_id_from_public_pem(rsa_pub_pem)
    check("S01 RS256 key_id format",
          rs_id.startswith("sha256:") and len(rs_id) == 71,
          f"got {rs_id[:20]}")

    mldsa_id = mldsa65_key_id_from_public_bytes(mldsa_pk)
    check("S02 ML-DSA-65 key_id format",
          mldsa_id.startswith("sha256:") and len(mldsa_id) == 71,
          f"got {mldsa_id[:20]}")

    check("S03 ML-DSA-65 rejects wrong pk length",
          _raises(lambda: mldsa65_key_id_from_public_bytes(b"x" * 100), ValueError))

    # S04: RS256 signature object
    tbs = b"test-tbs-bytes"
    rs_sig = sign_rs256(rsa_pub_pem, rsa_priv_pem, tbs)
    check("S04 RS256 sig object schema",
          set(rs_sig.keys()) == {"alg", "key_id", "value"},
          f"keys={list(rs_sig.keys())}")
    check("S05 RS256 alg field",
          rs_sig["alg"] == "RS256")
    check("S06 RS256 value prefix",
          rs_sig["value"].startswith("base64:"))
    sig_bytes = base64.b64decode(rs_sig["value"][7:])
    check("S07 RS256 sig length 256",
          len(sig_bytes) == 256, f"got {len(sig_bytes)}")

    # S08: ML-DSA-65 signature object
    mldsa_sig = sign_mldsa65(mldsa_pk, mldsa_sk, tbs)
    check("S08 ML-DSA-65 sig object schema",
          set(mldsa_sig.keys()) == {"alg", "key_id", "value"})
    check("S09 ML-DSA-65 alg field",
          mldsa_sig["alg"] == "ML-DSA-65")
    mldsa_sig_bytes = base64.b64decode(mldsa_sig["value"][7:])
    check("S10 ML-DSA-65 sig length 3309",
          len(mldsa_sig_bytes) == 3309, f"got {len(mldsa_sig_bytes)}")

    # S11: ML-DSA-65 deterministic
    sig1 = sign_mldsa65(mldsa_pk, mldsa_sk, tbs)
    sig2 = sign_mldsa65(mldsa_pk, mldsa_sk, tbs)
    check("S11 ML-DSA-65 deterministic", sig1["value"] == sig2["value"])

    # S12: RS256 rejects sk length
    check("S12 ML-DSA-65 rejects wrong sk length",
          _raises(lambda: sign_mldsa65(mldsa_pk, b"x" * 100, tbs), ValueError))

    # S13: hybrid sign returns sorted array
    sigs = sign_hybrid(cert, rsa_pub_pem, rsa_priv_pem, mldsa_pk, mldsa_sk)
    check("S13 hybrid returns array of 2", len(sigs) == 2)
    check("S14 hybrid sorted by alg",
          [s["alg"] for s in sigs] == ["ML-DSA-65", "RS256"],
          f"got {[s['alg'] for s in sigs]}")

    # S15: hybrid deterministic
    sigs2 = sign_hybrid(cert, rsa_pub_pem, rsa_priv_pem, mldsa_pk, mldsa_sk)
    check("S15 hybrid deterministic (JSON equal)",
          json.dumps(sigs, sort_keys=True) == json.dumps(sigs2, sort_keys=True))

    # S16: signature over same TBS
    from protocol.hybrid.tbs import build_tbs
    tbs_expected = build_tbs(cert)
    mldsa_sig_expected = sign_mldsa65(mldsa_pk, mldsa_sk, tbs_expected)
    check("S16 hybrid ML-DSA sig matches direct",
          sigs[0]["value"] == mldsa_sig_expected["value"])

    print()
    print("=" * 72)
    print(f"TOTAL: {PASS_N + FAIL_N} | PASS: {PASS_N} | FAIL: {FAIL_N}")
    print("=" * 72)
    sys.exit(0 if FAIL_N == 0 else 1)


def _raises(fn, exc_type):
    try:
        fn()
        return False
    except exc_type:
        return True
    except Exception:
        return False


if __name__ == "__main__":
    main()
