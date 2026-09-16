#!/usr/bin/env python3
"""Verify an ADIE validation report as an independent third party."""
import json
import sys
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 verify_report.py <report.json> <public_key.pem>")
        sys.exit(1)

    report_path, pubkey_path = sys.argv[1], sys.argv[2]

    with open(report_path) as f:
        report = json.load(f)

    with open(pubkey_path, "rb") as f:
        pub = serialization.load_pem_public_key(f.read())

    # Recompute hash from body
    body = {k: v for k, v in report.items()
            if k not in ("report_hash", "signature", "signature_alg", "status")}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    import hashlib
    computed_hash = hashlib.sha256(canonical).hexdigest()

    print("=" * 60)
    print("  ADIE — Third-Party Report Verification")
    print("=" * 60)

    ok = True

    if computed_hash == report["report_hash"]:
        print(f"[✓] Report integrity CONFIRMED")
        print(f"    Hash: {computed_hash}")
    else:
        print(f"[✗] Report integrity FAILED")
        print(f"    Expected: {report['report_hash']}")
        print(f"    Computed: {computed_hash}")
        ok = False

    if report.get("signature") and report.get("signature_alg") == "Ed25519":
        try:
            pub.verify(bytes.fromhex(report["signature"]),
                       report["report_hash"].encode())
            print(f"[✓] Ed25519 signature VALID")
        except InvalidSignature:
            print(f"[✗] Ed25519 signature INVALID")
            ok = False
    else:
        print("[!] Report is unsigned")
        ok = False

    print("-" * 60)
    print(f"Tests     : {report['passed']}/{report['total']}")
    print(f"Version   : {report['validator_version']}")
    print(f"Git Commit: {report['git_commit']}")
    print(f"Seed      : {report['seed']}")
    print("=" * 60)

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
