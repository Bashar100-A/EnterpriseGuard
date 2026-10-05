#!/usr/bin/env python3
"""ADIE CLI — Decision certificate issuance and verification."""
import argparse, json, hashlib, base64, secrets, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding


def canonicalize(obj):
    """RFC 8785 subset: sorted keys, no whitespace, UTF-8."""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False).encode('utf-8')


def sha256_hex(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def cmd_keygen(args):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    Path(args.out).write_bytes(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ))
    Path(args.pub).write_bytes(key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ))
    print(f"Private: {args.out}")
    print(f"Public:  {args.pub}")


def cmd_fingerprint(args):
    pub = serialization.load_pem_public_key(Path(args.pub).read_bytes())
    der = pub.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    print("sha256:" + hashlib.sha256(der).hexdigest())


def cmd_issue(args):
    decision = json.loads(Path(args.decision).read_text())
    evidence = json.loads(Path(args.evidence).read_text()) if args.evidence else {}

    key = serialization.load_pem_private_key(
        Path(args.key).read_bytes(), password=None)

    pub_der = key.public_key().public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    issuer_fp = "sha256:" + hashlib.sha256(pub_der).hexdigest()

    now = datetime.now(timezone.utc)
    cert = {
        "version": "1.0",
        "issuer": args.issuer,
        "issuer_fingerprint": issuer_fp,
        "issued_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": (now + timedelta(days=365)).isoformat().replace("+00:00", "Z"),
        "nonce": secrets.token_hex(16),
        "decision_hash": sha256_hex(canonicalize(decision)),
        "policy_version": args.policy,
        "evidence_ref": sha256_hex(canonicalize(evidence)),
        "signature": ""
    }

    payload = canonicalize({k: v for k, v in cert.items() if k != "signature"})
    sig = key.sign(payload, padding.PKCS1v15(), hashes.SHA256())
    cert["signature"] = "base64:" + base64.b64encode(sig).decode()

    Path(args.out).write_text(json.dumps(cert, indent=2))
    print(f"Certificate written: {args.out}")


def cmd_verify(args):
    cert = json.loads(Path(args.cert).read_text())
    pub = serialization.load_pem_public_key(Path(args.pub).read_bytes())

    exp = datetime.fromisoformat(cert["expires_at"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > exp:
        print("INVALID: E001_EXPIRED")
        sys.exit(1)

    pub_der = pub.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    expected_fp = "sha256:" + hashlib.sha256(pub_der).hexdigest()
    if cert["issuer_fingerprint"] != expected_fp:
        print("INVALID: E003_KEY_SUBSTITUTION")
        sys.exit(1)

    sig = base64.b64decode(cert["signature"].replace("base64:", ""))
    payload = canonicalize({k: v for k, v in cert.items() if k != "signature"})
    try:
        pub.verify(sig, payload, padding.PKCS1v15(), hashes.SHA256())
    except Exception:
        print("INVALID: E002_HASH_MISMATCH")
        sys.exit(1)

    print("VALID")


def main():
    p = argparse.ArgumentParser(prog="adie")
    sub = p.add_subparsers(dest="cmd", required=True)

    kg = sub.add_parser("keygen")
    kg.add_argument("--out", default="private.pem")
    kg.add_argument("--pub", default="public.pem")
    kg.set_defaults(func=cmd_keygen)

    fp = sub.add_parser("fingerprint")
    fp.add_argument("--pub", default="public.pem")
    fp.set_defaults(func=cmd_fingerprint)

    iss = sub.add_parser("issue")
    iss.add_argument("--decision", required=True)
    iss.add_argument("--policy", required=True)
    iss.add_argument("--evidence")
    iss.add_argument("--key", required=True)
    iss.add_argument("--issuer", default="adie.local")
    iss.add_argument("--out", required=True)
    iss.set_defaults(func=cmd_issue)

    ver = sub.add_parser("verify")
    ver.add_argument("--cert", required=True)
    ver.add_argument("--pub", required=True)
    ver.set_defaults(func=cmd_verify)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
