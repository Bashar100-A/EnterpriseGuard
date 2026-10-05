#!/usr/bin/env python3
"""ADIE CLI — Decision certificate issuance and verification."""
import argparse, json, hashlib, base64, secrets, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

SCHEMA_VERSION = "1.0"
REQUIRED_FIELDS = [
    "version", "issuer", "issuer_fingerprint", "issued_at", "expires_at",
    "nonce", "decision_hash", "policy_version", "evidence_ref", "signature"
]


def canonicalize(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False).encode('utf-8')


def sha256_hex(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def fail(code, message=""):
    print(f"INVALID: {code}" + (f" ({message})" if message else ""))
    sys.exit(1)


def cmd_keygen(args):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    Path(args.out).write_bytes(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()))
    Path(args.pub).write_bytes(key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo))
    print(f"Private: {args.out}")
    print(f"Public:  {args.pub}")


def cmd_fingerprint(args):
    try:
        pub = serialization.load_pem_public_key(Path(args.pub).read_bytes())
    except Exception as e:
        fail("E020_CANNOT_LOAD_PUBLIC_KEY", str(e)[:60])
    der = pub.public_bytes(encoding=serialization.Encoding.DER,
                          format=serialization.PublicFormat.SubjectPublicKeyInfo)
    print("sha256:" + hashlib.sha256(der).hexdigest())


def cmd_issue(args):
    try:
        decision = json.loads(Path(args.decision).read_text())
    except json.JSONDecodeError as e:
        fail("E004_MALFORMED_JSON", f"decision: {e}")
    try:
        evidence = json.loads(Path(args.evidence).read_text()) if args.evidence else {}
    except json.JSONDecodeError as e:
        fail("E004_MALFORMED_JSON", f"evidence: {e}")
    try:
        key = serialization.load_pem_private_key(
            Path(args.key).read_bytes(), password=None)
    except Exception as e:
        fail("E021_CANNOT_LOAD_PRIVATE_KEY", str(e)[:60])

    pub_der = key.public_key().public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo)
    issuer_fp = "sha256:" + hashlib.sha256(pub_der).hexdigest()

    now = datetime.now(timezone.utc)
    cert = {
        "version": SCHEMA_VERSION,
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
    try:
        raw = Path(args.cert).read_bytes()
    except Exception as e:
        fail("E030_CANNOT_READ_CERT", str(e)[:60])

    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError as e:
        fail("E010_INVALID_UNICODE", str(e)[:60])

    try:
        cert = json.loads(text)
    except json.JSONDecodeError as e:
        fail("E004_MALFORMED_JSON", str(e)[:60])

    if not isinstance(cert, dict):
        fail("E011_SCHEMA_VIOLATION", "certificate must be a JSON object")

    for field in REQUIRED_FIELDS:
        if field not in cert:
            fail("E005_MISSING_FIELD", field)

    if cert.get("version") != SCHEMA_VERSION:
        fail("E009_VERSION_MISMATCH",
             f"expected {SCHEMA_VERSION}, got {cert.get('version')!r}")

    fp = cert.get("issuer_fingerprint", "")
    if (not isinstance(fp, str) or not fp.startswith("sha256:")
            or len(fp) != 71 or fp != fp.lower()):
        fail("E007_INVALID_FINGERPRINT_FORMAT", str(fp)[:30])
    try:
        int(fp[7:], 16)
    except ValueError:
        fail("E007_INVALID_FINGERPRINT_FORMAT", "not hex")

    try:
        issued = datetime.fromisoformat(cert["issued_at"].replace("Z", "+00:00"))
        exp = datetime.fromisoformat(cert["expires_at"].replace("Z", "+00:00"))
    except Exception as e:
        fail("E008_INVALID_TIMESTAMP", str(e)[:60])

    if issued.tzinfo is None or exp.tzinfo is None:
        fail("E008_INVALID_TIMESTAMP", "missing timezone")
    if issued > exp:
        fail("E008_INVALID_TIMESTAMP", "issued_at > expires_at")

    now = datetime.now(timezone.utc)
    if now > exp:
        fail("E001_EXPIRED", f"expired at {exp.isoformat()}")

    try:
        pub = serialization.load_pem_public_key(Path(args.pub).read_bytes())
    except Exception as e:
        fail("E020_CANNOT_LOAD_PUBLIC_KEY", str(e)[:60])

    pub_der = pub.public_bytes(encoding=serialization.Encoding.DER,
                               format=serialization.PublicFormat.SubjectPublicKeyInfo)
    expected_fp = "sha256:" + hashlib.sha256(pub_der).hexdigest()
    if cert["issuer_fingerprint"] != expected_fp:
        fail("E003_KEY_SUBSTITUTION",
             f"cert says {cert['issuer_fingerprint'][:20]}, key is {expected_fp[:20]}")

    sig_field = cert.get("signature", "")
    if not isinstance(sig_field, str) or not sig_field.startswith("base64:"):
        fail("E006_INVALID_SIGNATURE_FORMAT")
    try:
        sig = base64.b64decode(sig_field[7:], validate=True)
    except Exception as e:
        fail("E006_INVALID_SIGNATURE_FORMAT", str(e)[:60])
    if not sig:
        fail("E006_INVALID_SIGNATURE_FORMAT", "empty signature")

    payload = canonicalize({k: v for k, v in cert.items() if k != "signature"})
    try:
        pub.verify(sig, payload, padding.PKCS1v15(), hashes.SHA256())
    except Exception as e:
        fail("E002_HASH_MISMATCH", str(e)[:60])

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
