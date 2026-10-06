#!/usr/bin/env python3
"""Hybrid verifier — Python conformance tests."""
import base64
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from dilithium_py.ml_dsa import ML_DSA_65 as DLP

from protocol.hybrid.sign import sign_hybrid, sign_mldsa65, sign_rs256
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


def raises_code(fn, code):
    try:
        fn()
        return False
    except HybridVerifyError as e:
        return e.code == code


def main():
    print("=" * 72)
    print("ADIE hybrid verifier — Python conformance")
    print("=" * 72)

    # keys
    rsa_priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    rsa_priv_pem = rsa_priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption())
    rsa_pub_pem = rsa_priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo)

    rsa2 = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    rsa2_pub_pem = rsa2.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo)

    mldsa_pk, mldsa_sk = DLP.key_derive(bytes([0x42] * 32))
    mldsa2_pk, mldsa2_sk = DLP.key_derive(bytes([0x43] * 32))

    cert = {"dcp_version": "2.1", "claim_id": "c1"}
    sigs = sign_hybrid(cert, rsa_pub_pem, rsa_priv_pem, mldsa_pk, mldsa_sk)

    # V01: happy path both
    r = verify_hybrid(cert, sigs, ["RS256", "ML-DSA-65"],
                     rs256_pub_pem=rsa_pub_pem, mldsa65_pub_raw=mldsa_pk)
    check("V01 both valid", r["status"] == "VALID" and
          r["checks"] == {"RS256": "PASS", "ML-DSA-65": "PASS"})

    # V02: RS256 only (required RS256)
    r = verify_hybrid(cert, sigs, ["RS256"], rs256_pub_pem=rsa_pub_pem)
    check("V02 RS256-only required", r["status"] == "VALID")

    # V03: ML-DSA-65 only required
    r = verify_hybrid(cert, sigs, ["ML-DSA-65"], mldsa65_pub_raw=mldsa_pk)
    check("V03 ML-DSA-65-only required", r["status"] == "VALID")

    # V04: empty signatures
    check("V04 empty signatures → E_SIGNATURE_HYBRID_MISSING",
          raises_code(lambda: verify_hybrid(cert, [], ["RS256"], rs256_pub_pem=rsa_pub_pem),
                     "E_SIGNATURE_HYBRID_MISSING"))

    # V05: duplicate alg
    dup = [sigs[0], sigs[0]]
    check("V05 duplicate alg → E_SIGNATURE_DUPLICATE_ALG",
          raises_code(lambda: verify_hybrid(cert, dup, ["ML-DSA-65"],
                                            mldsa65_pub_raw=mldsa_pk),
                     "E_SIGNATURE_DUPLICATE_ALG"))

    # V06: unknown alg
    unknown = [{"alg": "ED25519", "key_id": "sha256:" + "0"*64, "value": "base64:AA=="}]
    check("V06 unknown alg → E_SIGNATURE_UNKNOWN_ALG",
          raises_code(lambda: verify_hybrid(cert, unknown, ["ED25519"]),
                     "E_SIGNATURE_UNKNOWN_ALG"))

    # V07: downgrade (required both, only RS256 present)
    rs_only = [s for s in sigs if s["alg"] == "RS256"]
    check("V07 downgrade → E_SIGNATURE_DOWNGRADE",
          raises_code(lambda: verify_hybrid(cert, rs_only, ["RS256", "ML-DSA-65"],
                                            rs256_pub_pem=rsa_pub_pem,
                                            mldsa65_pub_raw=mldsa_pk),
                     "E_SIGNATURE_DOWNGRADE"))

    # V08: ML-DSA tampered
    bad = [dict(s) for s in sigs]
    for s in bad:
        if s["alg"] == "ML-DSA-65":
            s["value"] = "base64:" + base64.b64encode(b"\x00" * 3309).decode()
    check("V08 tampered ML-DSA → E_SIGNATURE_HYBRID_INVALID",
          raises_code(lambda: verify_hybrid(cert, bad, ["RS256", "ML-DSA-65"],
                                            rs256_pub_pem=rsa_pub_pem,
                                            mldsa65_pub_raw=mldsa_pk),
                     "E_SIGNATURE_HYBRID_INVALID"))

    # V09: RS256 tampered
    bad2 = [dict(s) for s in sigs]
    for s in bad2:
        if s["alg"] == "RS256":
            s["value"] = "base64:" + base64.b64encode(b"\x00" * 256).decode()
    check("V09 tampered RS256 → E_SIGNATURE_HYBRID_INVALID",
          raises_code(lambda: verify_hybrid(cert, bad2, ["RS256", "ML-DSA-65"],
                                            rs256_pub_pem=rsa_pub_pem,
                                            mldsa65_pub_raw=mldsa_pk),
                     "E_SIGNATURE_HYBRID_INVALID"))

    # V10: wrong RS256 key_id
    bad3 = [dict(s) for s in sigs]
    for s in bad3:
        if s["alg"] == "RS256":
            s["key_id"] = "sha256:" + "0" * 64
    check("V10 wrong RS256 key_id → E_SIGNATURE_KEY_MISMATCH",
          raises_code(lambda: verify_hybrid(cert, bad3, ["RS256"],
                                            rs256_pub_pem=rsa_pub_pem),
                     "E_SIGNATURE_KEY_MISMATCH"))

    # V11: wrong ML-DSA key_id
    bad4 = [dict(s) for s in sigs]
    for s in bad4:
        if s["alg"] == "ML-DSA-65":
            s["key_id"] = "sha256:" + "f" * 64
    check("V11 wrong ML-DSA key_id → E_SIGNATURE_KEY_MISMATCH",
          raises_code(lambda: verify_hybrid(cert, bad4, ["ML-DSA-65"],
                                            mldsa65_pub_raw=mldsa_pk),
                     "E_SIGNATURE_KEY_MISMATCH"))

    # V12: different RS256 key (valid sig, wrong key)
    check("V12 wrong RS256 public key → E_SIGNATURE_KEY_MISMATCH",
          raises_code(lambda: verify_hybrid(cert, sigs, ["RS256"],
                                            rs256_pub_pem=rsa2_pub_pem),
                     "E_SIGNATURE_KEY_MISMATCH"))

    # V13: different ML-DSA key
    check("V13 wrong ML-DSA public key → E_SIGNATURE_KEY_MISMATCH",
          raises_code(lambda: verify_hybrid(cert, sigs, ["ML-DSA-65"],
                                            mldsa65_pub_raw=mldsa2_pk),
                     "E_SIGNATURE_KEY_MISMATCH"))

    # V14: missing RS256 pubkey but RS256 required
    check("V14 missing RS256 pubkey → E_SIGNATURE_HYBRID_MISSING",
          raises_code(lambda: verify_hybrid(cert, sigs, ["RS256"]),
                     "E_SIGNATURE_HYBRID_MISSING"))

    # V15: missing ML-DSA pubkey but required
    check("V15 missing ML-DSA pubkey → E_SIGNATURE_HYBRID_MISSING",
          raises_code(lambda: verify_hybrid(cert, sigs, ["ML-DSA-65"]),
                     "E_SIGNATURE_HYBRID_MISSING"))

    # V16: sig value without base64 prefix
    bad5 = [dict(s) for s in sigs]
    bad5[0]["value"] = "hex:abc"
    check("V16 bad base64 prefix → E_SIGNATURE_HYBRID_INVALID",
          raises_code(lambda: verify_hybrid(cert, bad5, ["ML-DSA-65"],
                                            mldsa65_pub_raw=mldsa_pk),
                     "E_SIGNATURE_HYBRID_INVALID"))

    # V17: tampered cert (changes TBS → both fail)
    cert_tampered = {"dcp_version": "2.1", "claim_id": "c1-evil"}
    check("V17 tampered cert → E_SIGNATURE_HYBRID_INVALID",
          raises_code(lambda: verify_hybrid(cert_tampered, sigs, ["RS256", "ML-DSA-65"],
                                            rs256_pub_pem=rsa_pub_pem,
                                            mldsa65_pub_raw=mldsa_pk),
                     "E_SIGNATURE_HYBRID_INVALID"))

    # V18: signatures not a list
    check("V18 signatures not list → E_SIGNATURE_HYBRID_MISSING",
          raises_code(lambda: verify_hybrid(cert, "not-a-list", ["RS256"],
                                            rs256_pub_pem=rsa_pub_pem),
                     "E_SIGNATURE_HYBRID_MISSING"))

    # V19: required_algs contains unknown
    check("V19 required alg not in signatures → E_SIGNATURE_DOWNGRADE",
          raises_code(lambda: verify_hybrid(cert, sigs, ["RS256", "ED25519"],
                                            rs256_pub_pem=rsa_pub_pem),
                     "E_SIGNATURE_DOWNGRADE"))

    # V20: RS256 key_id format valid but sig invalid
    bad6 = [dict(s) for s in sigs]
    for s in bad6:
        if s["alg"] == "RS256":
            s["value"] = "base64:" + base64.b64encode(b"\xAA" * 256).decode()
    check("V20 invalid RS256 sig bytes → E_SIGNATURE_HYBRID_INVALID",
          raises_code(lambda: verify_hybrid(cert, bad6, ["RS256"],
                                            rs256_pub_pem=rsa_pub_pem),
                     "E_SIGNATURE_HYBRID_INVALID"))

    print()
    print("=" * 72)
    print(f"TOTAL: {PASS_N + FAIL_N} | PASS: {PASS_N} | FAIL: {FAIL_N}")
    print("=" * 72)
    sys.exit(0 if FAIL_N == 0 else 1)


if __name__ == "__main__":
    main()
