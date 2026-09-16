#!/usr/bin/env python3
"""Generate Ed25519 keypair for ADIE report signing."""
import os
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

KEYS_DIR = "keys"
os.makedirs(KEYS_DIR, exist_ok=True)

private_path = os.path.join(KEYS_DIR, "adie_private.pem")
public_path = os.path.join(KEYS_DIR, "adie_public.pem")

if os.path.exists(private_path):
    print(f"[!] Private key already exists: {private_path}")
    print("    Delete it manually if you want to regenerate.")
    raise SystemExit(0)

private_key = Ed25519PrivateKey.generate()
public_key = private_key.public_key()

with open(private_path, "wb") as f:
    f.write(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ))

with open(public_path, "wb") as f:
    f.write(public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ))

os.chmod(private_path, 0o600)

print("[✓] Ed25519 keypair generated:")
print(f"    Private: {private_path}  (keep SECRET, never share)")
print(f"    Public : {public_path}   (publish this, share with auditors)")
