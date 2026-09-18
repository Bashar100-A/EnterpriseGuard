"""Tests for src/enterpriseguard/signing/ (SDK signing module).

Covers the 7 scenarios defined in DC-137 v2.
Tests never touch ~/.enterpriseguard/; all keys are ephemeral in tmp_path.
"""

from __future__ import annotations

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa

from enterpriseguard.signing import (
    SigningKeyInvalidError,
    SigningKeyNotFoundError,
    sign_bytes,
    verify_signature_hex,
)


# ─────────────────────── fixtures ───────────────────────

@pytest.fixture
def rsa_key_dir(tmp_path):
    """Generate ephemeral RSA-2048 keypair in tmp_path."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    key_dir = tmp_path / "keys"
    key_dir.mkdir()

    private_path = key_dir / "private_key.pem"
    public_path = key_dir / "public_key.pem"

    private_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    public_path.write_bytes(
        key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    return key_dir


@pytest.fixture
def ecdsa_key_dir(tmp_path):
    """Generate ephemeral ECDSA P-256 keypair in tmp_path/ecdsa/."""
    key = ec.generate_private_key(ec.SECP256R1())
    key_dir = tmp_path / "keys"
    ecdsa_dir = key_dir / "ecdsa"
    ecdsa_dir.mkdir(parents=True)

    private_path = ecdsa_dir / "private_key.pem"
    public_path = ecdsa_dir / "public_key.pem"

    private_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    public_path.write_bytes(
        key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    return key_dir


# ─────────── 1. RSA round-trip ───────────

def test_rsa_round_trip(rsa_key_dir):
    data = "hello-rsa"
    sig = sign_bytes(data, backend="rsa_local", key_dir=rsa_key_dir)
    assert isinstance(sig, str)
    assert len(sig) > 0
    assert verify_signature_hex(data, sig, backend="rsa_local", key_dir=rsa_key_dir) is True


# ─────────── 2. ECDSA round-trip ───────────

def test_ecdsa_round_trip(ecdsa_key_dir):
    data = "hello-ecdsa"
    sig = sign_bytes(data, backend="ecdsa_local", key_dir=ecdsa_key_dir)
    assert isinstance(sig, str)
    assert len(sig) > 0
    assert verify_signature_hex(data, sig, backend="ecdsa_local", key_dir=ecdsa_key_dir) is True


# ─────────── 3. Tampered data ───────────

def test_tampered_data_returns_false(rsa_key_dir):
    data = "original"
    sig = sign_bytes(data, backend="rsa_local", key_dir=rsa_key_dir)
    assert verify_signature_hex(data + "x", sig, backend="rsa_local", key_dir=rsa_key_dir) is False


# ─────────── 4. Tampered signature ───────────

def test_tampered_signature_returns_false(rsa_key_dir):
    data = "original"
    sig = sign_bytes(data, backend="rsa_local", key_dir=rsa_key_dir)

    # Corrupt one hex character
    corrupted = ("0" if sig[0] != "0" else "1") + sig[1:]
    assert verify_signature_hex(data, corrupted, backend="rsa_local", key_dir=rsa_key_dir) is False

    # Malformed hex
    assert verify_signature_hex(data, "zzzz", backend="rsa_local", key_dir=rsa_key_dir) is False


# ─────────── 5. Missing key ───────────

def test_missing_private_key_raises(tmp_path):
    empty_dir = tmp_path / "empty_keys"
    empty_dir.mkdir()
    with pytest.raises(SigningKeyNotFoundError):
        sign_bytes("data", backend="rsa_local", key_dir=empty_dir)


# ─────────── 6. Unknown backend ───────────

def test_unknown_backend_raises(rsa_key_dir):
    with pytest.raises(ValueError):
        sign_bytes("data", backend="does_not_exist", key_dir=rsa_key_dir)
    with pytest.raises(ValueError):
        verify_signature_hex("data", "abcd", backend="does_not_exist", key_dir=rsa_key_dir)


# ─────────── 7. Wrong key type (RSA path with EC key) ───────────

def test_wrong_key_type_raises(ecdsa_key_dir):
    """ECDSA key in RSA path should raise SigningKeyInvalidError."""
    # copy the ecdsa private key into the RSA private_key.pem location
    rsa_path = ecdsa_key_dir / "private_key.pem"
    ecdsa_path = ecdsa_key_dir / "ecdsa" / "private_key.pem"
    rsa_path.write_bytes(ecdsa_path.read_bytes())

    with pytest.raises(SigningKeyInvalidError):
        sign_bytes("data", backend="rsa_local", key_dir=ecdsa_key_dir)
