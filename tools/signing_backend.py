#!/usr/bin/env python3
"""Pluggable signing backend for AAAC (Local RSA, ECDSA, Mock, AWS KMS, TPM)."""

import os
import sys
import hashlib
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, ec, rsa

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent

PRIVATE_KEY_PATH = Path.home() / ".enterpriseguard" / "keys" / "private_key.pem"
PUBLIC_KEY_PATH = Path.home() / ".enterpriseguard" / "keys" / "public_key.pem"
GENESIS_PUBLIC_KEY_PATH = ROOT / "tools" / "genesis_public_key.pem"
GENESIS_PRIVATE_KEY_PATH = Path.home() / ".enterpriseguard" / "keys" / "genesis_private_key.pem"

ECDSA_PRIVATE_KEY_PATH = Path.home() / ".enterpriseguard" / "keys" / "ecdsa" / "private_key.pem"
ECDSA_PUBLIC_KEY_PATH = Path.home() / ".enterpriseguard" / "keys" / "ecdsa" / "public_key.pem"
ECDSA_GENESIS_PRIVATE_KEY_PATH = Path.home() / ".enterpriseguard" / "keys" / "ecdsa" / "genesis_private_key.pem"
ECDSA_GENESIS_PUBLIC_KEY_PATH = ROOT / "tools" / "genesis_public_ecdsa.pem"


def _load_private_key(path: Path):
    """Load a private key from PEM file."""
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def _load_public_key(path: Path):
    """Load a public key from PEM file."""
    with open(path, "rb") as f:
        return serialization.load_pem_public_key(f.read())


def _sign_rsa(data: bytes, private_key) -> bytes:
    return private_key.sign(data, padding.PKCS1v15(), hashes.SHA256())


def _verify_rsa(data: bytes, signature: bytes, public_key) -> bool:
    try:
        public_key.verify(signature, data, padding.PKCS1v15(), hashes.SHA256())
        return True
    except Exception:
        return False


def _sign_ecdsa(data: bytes, private_key) -> bytes:
    return private_key.sign(data, ec.ECDSA(hashes.SHA256()))


def _verify_ecdsa(data: bytes, signature: bytes, public_key) -> bool:
    try:
        public_key.verify(signature, data, ec.ECDSA(hashes.SHA256()))
        return True
    except Exception:
        return False


def sign_bytes(data: str) -> str:
    """Sign a string and return hex-encoded signature using configured backend."""
    backend = os.environ.get("AAAC_SIGNING_BACKEND", "local")
    data_bytes = data.encode("utf-8")

    if backend == "local":
        if not PRIVATE_KEY_PATH.exists():
            raise RuntimeError("Local private key not found")
        private_key = _load_private_key(PRIVATE_KEY_PATH)
        sig = _sign_rsa(data_bytes, private_key)
        return sig.hex()
    elif backend == "ecdsa_local":
        if not ECDSA_PRIVATE_KEY_PATH.exists():
            raise RuntimeError("ECDSA private key not found")
        private_key = _load_private_key(ECDSA_PRIVATE_KEY_PATH)
        sig = _sign_ecdsa(data_bytes, private_key)
        return sig.hex()
    elif backend == "mock":
        return hashlib.sha256(("mock:" + data).encode("utf-8")).hexdigest()
    elif backend == "aws_kms":
        # AWS KMS still uses subprocess/boto3; keep as placeholder
        raise RuntimeError("AWS KMS backend not implemented in this version")
    elif backend == "tpm":
        # TPM still uses subprocess; keep as placeholder
        raise RuntimeError("TPM backend not implemented in this version")
    else:
        raise ValueError(f"Unsupported signing backend: {backend}")


def verify_signature_hex(data: str, signature_hex: str) -> bool:
    """Verify a hex signature using the configured backend's public key."""
    backend = os.environ.get("AAAC_SIGNING_BACKEND", "local")
    data_bytes = data.encode("utf-8")
    try:
        sig_bytes = bytes.fromhex(signature_hex)
    except ValueError:
        return False

    if backend == "local":
        if not PUBLIC_KEY_PATH.exists():
            return False
        public_key = _load_public_key(PUBLIC_KEY_PATH)
        return _verify_rsa(data_bytes, sig_bytes, public_key)
    elif backend == "ecdsa_local":
        if not ECDSA_PUBLIC_KEY_PATH.exists():
            return False
        public_key = _load_public_key(ECDSA_PUBLIC_KEY_PATH)
        return _verify_ecdsa(data_bytes, sig_bytes, public_key)
    elif backend == "mock":
        expected = hashlib.sha256(("mock:" + data).encode("utf-8")).hexdigest()
        return signature_hex == expected
    else:
        return False


def sign_genesis_chain_id_hex(chain_id: str) -> str:
    """Sign genesis chain ID using configured backend."""
    backend = os.environ.get("AAAC_SIGNING_BACKEND", "local")
    data_bytes = chain_id.encode("utf-8")

    if backend == "local":
        if not GENESIS_PRIVATE_KEY_PATH.exists():
            raise RuntimeError("Genesis private key not found")
        private_key = _load_private_key(GENESIS_PRIVATE_KEY_PATH)
        sig = _sign_rsa(data_bytes, private_key)
        return sig.hex()
    elif backend == "ecdsa_local":
        if not ECDSA_GENESIS_PRIVATE_KEY_PATH.exists():
            raise RuntimeError("ECDSA genesis private key not found")
        private_key = _load_private_key(ECDSA_GENESIS_PRIVATE_KEY_PATH)
        sig = _sign_ecdsa(data_bytes, private_key)
        return sig.hex()
    elif backend == "mock":
        return hashlib.sha256(("genesis-mock:" + chain_id).encode("utf-8")).hexdigest()
    else:
        raise ValueError(f"Unsupported signing backend: {backend}")


def verify_genesis_signature_hex(chain_id: str, signature_hex: str) -> bool:
    """Verify genesis signature using configured backend."""
    backend = os.environ.get("AAAC_SIGNING_BACKEND", "local")
    data_bytes = chain_id.encode("utf-8")
    try:
        sig_bytes = bytes.fromhex(signature_hex)
    except ValueError:
        return False

    if backend == "local":
        if not GENESIS_PUBLIC_KEY_PATH.exists():
            return False
        public_key = _load_public_key(GENESIS_PUBLIC_KEY_PATH)
        return _verify_rsa(data_bytes, sig_bytes, public_key)
    elif backend == "ecdsa_local":
        if not ECDSA_GENESIS_PUBLIC_KEY_PATH.exists():
            return False
        public_key = _load_public_key(ECDSA_GENESIS_PUBLIC_KEY_PATH)
        return _verify_ecdsa(data_bytes, sig_bytes, public_key)
    elif backend == "mock":
        expected = hashlib.sha256(("genesis-mock:" + chain_id).encode("utf-8")).hexdigest()
        return signature_hex == expected
    else:
        return False


if __name__ == "__main__":
    data = "test"
    sig = sign_bytes(data)
    print(f"Signature ({os.environ.get('AAAC_SIGNING_BACKEND', 'local')}): {sig[:16]}...")
    ok = verify_signature_hex(data, sig)
    print(f"Verify: {ok}")
