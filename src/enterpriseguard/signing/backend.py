#!/usr/bin/env python3
"""SDK signing backend.

RSA-2048 (PKCS1v15, SHA-256) and ECDSA P-256 (SHA-256) signing for SDK
consumers. Independent from tools/signing_backend.py by design:

- No genesis signing (tools/-internal).
- No KMS/TPM/Azure (deferred to v2).
- No mock mode (tests use real ephemeral keys).
- No env var backend selection.

See continuity/DC-137_SDK_SIGNING_MODULE.md for rationale.
"""

from __future__ import annotations

from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa


DEFAULT_KEY_DIR = Path.home() / ".enterpriseguard" / "keys"

SUPPORTED_BACKENDS = ("rsa_local", "ecdsa_local")


class SigningError(RuntimeError):
    """Base exception for SDK signing errors."""


class SigningKeyNotFoundError(SigningError):
    """Raised when the private key file is missing."""


class SigningKeyInvalidError(SigningError):
    """Raised when the private key file cannot be loaded or has the wrong type."""


def _rsa_private_path(key_dir: Path) -> Path:
    return key_dir / "private_key.pem"


def _rsa_public_path(key_dir: Path) -> Path:
    return key_dir / "public_key.pem"


def _ecdsa_private_path(key_dir: Path) -> Path:
    return key_dir / "ecdsa" / "private_key.pem"


def _ecdsa_public_path(key_dir: Path) -> Path:
    return key_dir / "ecdsa" / "public_key.pem"


def _load_private_key(path: Path):
    if not path.exists():
        raise SigningKeyNotFoundError(f"Private key not found: {path}")
    try:
        with open(path, "rb") as handle:
            return serialization.load_pem_private_key(handle.read(), password=None)
    except Exception as exc:
        raise SigningKeyInvalidError(f"Failed to load private key: {path}") from exc


def _load_public_key(path: Path):
    if not path.exists():
        return None
    try:
        with open(path, "rb") as handle:
            return serialization.load_pem_public_key(handle.read())
    except Exception:
        return None


def sign_bytes(
    data: str,
    *,
    backend: str = "rsa_local",
    key_dir: Path | None = None,
) -> str:
    """Sign a UTF-8 string; return hex-encoded signature.

    Raises SigningKeyNotFoundError if the private key is missing.
    Raises SigningKeyInvalidError if the private key cannot be loaded
    or has the wrong type for the selected backend.
    Raises ValueError for an unknown backend.
    """
    if backend not in SUPPORTED_BACKENDS:
        raise ValueError(f"Unsupported backend: {backend}")
    if key_dir is None:
        key_dir = DEFAULT_KEY_DIR

    payload = data.encode("utf-8")

    if backend == "rsa_local":
        private_key = _load_private_key(_rsa_private_path(key_dir))
        try:
            sig = private_key.sign(payload, padding.PKCS1v15(), hashes.SHA256())
        except Exception as exc:
            raise SigningKeyInvalidError(
                f"Private key is not an RSA key: {_rsa_private_path(key_dir)}"
            ) from exc
        return sig.hex()

    private_key = _load_private_key(_ecdsa_private_path(key_dir))
    try:
        sig = private_key.sign(payload, ec.ECDSA(hashes.SHA256()))
    except Exception as exc:
        raise SigningKeyInvalidError(
            f"Private key is not an ECDSA key: {_ecdsa_private_path(key_dir)}"
        ) from exc
    return sig.hex()


def verify_signature_hex(
    data: str,
    signature_hex: str,
    *,
    backend: str = "rsa_local",
    key_dir: Path | None = None,
) -> bool:
    """Verify a hex-encoded signature.

    Returns False (never raises) on missing/invalid keys or bad
    signatures. Raises ValueError only for an unknown backend.
    """
    if backend not in SUPPORTED_BACKENDS:
        raise ValueError(f"Unsupported backend: {backend}")
    if key_dir is None:
        key_dir = DEFAULT_KEY_DIR

    try:
        sig = bytes.fromhex(signature_hex)
    except (ValueError, TypeError):
        return False

    payload = data.encode("utf-8")

    if backend == "rsa_local":
        public_key = _load_public_key(_rsa_public_path(key_dir))
        if public_key is None:
            return False
        try:
            public_key.verify(sig, payload, padding.PKCS1v15(), hashes.SHA256())
            return True
        except Exception:
            return False

    public_key = _load_public_key(_ecdsa_public_path(key_dir))
    if public_key is None:
        return False
    try:
        public_key.verify(sig, payload, ec.ECDSA(hashes.SHA256()))
        return True
    except Exception:
        return False
