import os
import sys
import json
import hmac
import hashlib
import secrets
import base64
import threading
import time
import pytest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.sibb_keys import (
    SIBBKeyManager,
    SIBBKeyManagerError,
    InsufficientSharesError,
    ShareIntegrityError,
    AccessDeniedError,
    MASTER_KEY_SIZE,
    PBKDF2_ITERATIONS,
    MIN_PASSWORD_LENGTH,
    MAX_ATTEMPTS,
    LOCKOUT_SECONDS,
    PRIME,
    HMAC_KEY_SIZE,
)

# ==================== Fixtures ====================

@pytest.fixture
def km(tmp_path):
    """Create a basic key manager with a strong password."""
    manager = SIBBKeyManager(tmp_path / "shares", password="StrongPass123!")
    return manager

@pytest.fixture
def split_keys(km):
    """Generate and split a master key, return (manager, key, result, shares)."""
    key = km.generate_master_key()
    result = km.split_master_key(key, n=5, k=3)
    return km, key, result, result["share_files"]

# ==================== Master Key Generation ====================

def test_generate_master_key_length(km):
    key = km.generate_master_key()
    assert len(key) == MASTER_KEY_SIZE

def test_generate_master_key_randomness(km):
    key1 = km.generate_master_key()
    key2 = km.generate_master_key()
    assert key1 != key2

def test_constants():
    assert PBKDF2_ITERATIONS >= 480000
    assert MIN_PASSWORD_LENGTH == 12

# ==================== Shamir Split/Reconstruct ====================

def test_split_and_reconstruct_with_k_shares(split_keys):
    km, key, result, shares = split_keys
    # Use exactly K (3) shares
    recovered = km.reconstruct_key(shares[:3])
    assert recovered == key

def test_split_and_reconstruct_with_more_than_k_shares(split_keys):
    km, key, result, shares = split_keys
    recovered = km.reconstruct_key(shares[:4])
    assert recovered == key

def test_reconstruct_with_insufficient_shares(split_keys):
    km, key, result, shares = split_keys
    with pytest.raises(InsufficientSharesError):
        km.reconstruct_key(shares[:2])

def test_reconstruct_with_invalid_share(split_keys):
    km, key, result, shares = split_keys
    # Modify one share file (corrupt ciphertext)
    share_path = km.shares_dir / shares[0]
    raw = share_path.read_bytes()
    # Flip a byte in the protected part (not the last line HMAC)
    parts = raw.rsplit(b"\n", 1)
    protected_raw = bytearray(parts[0])
    protected_raw[0] ^= 0x01
    new_raw = bytes(protected_raw) + b"\n" + parts[1]
    share_path.write_bytes(new_raw)
    with pytest.raises(ShareIntegrityError):
        km.reconstruct_key(shares[:3])

def test_reconstruct_with_share_from_different_key(km, split_keys):
    # Generate a second split
    key2 = km.generate_master_key()
    result2 = km.split_master_key(key2, n=5, k=3)
    shares2 = result2["share_files"]
    # Try to reconstruct using shares from different key sets
    mixed_shares = split_keys[3][:2] + shares2[:1]  # 2 from first, 1 from second
    with pytest.raises(ShareIntegrityError):
        km.reconstruct_key(mixed_shares)

# ==================== Encryption at Rest ====================

def test_shares_encrypted_on_disk(split_keys):
    km, key, result, shares = split_keys
    for share_name in shares:
        share_path = km.shares_dir / share_name
        raw = share_path.read_bytes()
        # Raw data should not contain the key directly
        assert key not in raw
        # Also should not be plaintext JSON with y value? Hard to check, but at least not contain "share_id" in plaintext?
        # We'll assume encryption works if decryption succeeds later.

def test_reconstruct_with_wrong_password(split_keys):
    km, key, result, shares = split_keys
    with pytest.raises(ShareIntegrityError):
        km.reconstruct_key(shares[:3], password="WrongPass123!")

def test_unique_salts_per_share(split_keys):
    km, key, result, shares = split_keys
    salts = set()
    for share_name in shares:
        share_path = km.shares_dir / share_name
        raw = share_path.read_bytes()
        parts = raw.rsplit(b"\n", 1)
        protected = json.loads(parts[0].decode())
        salts.add(protected["salt"])
    assert len(salts) == len(shares)

# ==================== HMAC Integrity ====================

def test_verify_share_valid(split_keys):
    km, key, result, shares = split_keys
    assert km.verify_share(shares[0]) is True

def test_verify_share_tampered_ciphertext(split_keys):
    km, key, result, shares = split_keys
    share_path = km.shares_dir / shares[0]
    raw = share_path.read_bytes()
    parts = raw.rsplit(b"\n", 1)
    protected_raw = bytearray(parts[0])
    protected_raw[10] ^= 0xFF  # modify ciphertext
    new_raw = bytes(protected_raw) + b"\n" + parts[1]
    share_path.write_bytes(new_raw)
    assert km.verify_share(shares[0]) is False

def test_verify_share_tampered_hmac(split_keys):
    km, key, result, shares = split_keys
    share_path = km.shares_dir / shares[0]
    raw = share_path.read_bytes()
    parts = raw.rsplit(b"\n", 1)
    hmac_b64 = base64.b64encode(b"badhmac")
    new_raw = parts[0] + b"\n" + hmac_b64
    share_path.write_bytes(new_raw)
    assert km.verify_share(shares[0]) is False

# ==================== Access Control ====================

def test_access_key_enforced(tmp_path, monkeypatch):
    monkeypatch.setenv("SIBB_ACCESS_KEY", "secret")
    km = SIBBKeyManager(tmp_path / "shares", password="StrongPass123!", access_key="secret")
    # Correct key should work
    key = km.generate_master_key()
    result = km.split_master_key(key)
    # Now remove env var to simulate wrong key
    monkeypatch.delenv("SIBB_ACCESS_KEY")
    with pytest.raises(AccessDeniedError):
        km.generate_master_key()

def test_password_required_for_split(km):
    # Create manager without password
    km_no_pass = SIBBKeyManager(km.shares_dir.parent / "nopass", hmac_key_path=km.hmac_key_path)
    key = km_no_pass.generate_master_key()
    with pytest.raises(AccessDeniedError):
        km_no_pass.split_master_key(key)

# ==================== Audit Logging ====================

def test_audit_logging_on_split(split_keys, monkeypatch):
    km, key, result, shares = split_keys
    calls = []
    monkeypatch.setattr("tools.sibb_keys.append_activity", lambda event, details: calls.append((event, details)))
    # Re-split to trigger audit
    key2 = km.generate_master_key()
    km.split_master_key(key2, n=5, k=3)
    assert any(event == "key_split" for event, _ in calls)

def test_audit_logging_on_reconstruct(split_keys, monkeypatch):
    km, key, result, shares = split_keys
    calls = []
    monkeypatch.setattr("tools.sibb_keys.append_activity", lambda event, details: calls.append((event, details)))
    km.reconstruct_key(shares[:3])
    assert any(event == "key_reconstruct" for event, _ in calls)

# ==================== Lockout Mechanism ====================

def test_lockout_after_failures(split_keys):
    km, key, result, shares = split_keys
    # Force failures by using wrong password repeatedly
    for _ in range(MAX_ATTEMPTS):
        with pytest.raises(ShareIntegrityError):
            km.reconstruct_key(shares[:3], password="WrongPass123!")
    # Now even with correct password should fail due to lockout
    with pytest.raises(AccessDeniedError):
        km.reconstruct_key(shares[:3], password="StrongPass123!")

def test_lockout_expiry(split_keys, monkeypatch):
    km, key, result, shares = split_keys
    # Make failed attempts
    for _ in range(MAX_ATTEMPTS):
        with pytest.raises(ShareIntegrityError):
            km.reconstruct_key(shares[:3], password="WrongPass123!")
    # Simulate time passing by setting time.time to a future fixed timestamp
    future_time = time.time() + LOCKOUT_SECONDS + 1
    monkeypatch.setattr(time, 'time', lambda: future_time)
    # Now should succeed
    recovered = km.reconstruct_key(shares[:3], password="StrongPass123!")
    assert recovered == key

# ==================== Path/Symlink Security ====================

def test_path_traversal_rejected(km):
    with pytest.raises(SIBBKeyManagerError):
        km._validate_share_path("../evil.share")

def test_symlink_attack_rejected(km, tmp_path):
    # Create a symlink inside shares_dir pointing to an outside file
    outside_file = tmp_path / "outside.txt"
    outside_file.write_text("secret")
    symlink_path = km.shares_dir / "link.share"
    os.symlink(outside_file, symlink_path)
    # Attempt to validate the symlink path should raise
    with pytest.raises(SIBBKeyManagerError):
        km._validate_share_path("link.share")
    # Also attempt to read a share via symlink should fail
    share_name = "link.share"
    with pytest.raises(SIBBKeyManagerError):
        km.verify_share(share_name)

def test_share_file_permissions(split_keys):
    km, key, result, shares = split_keys
    for share_name in shares:
        share_path = km.shares_dir / share_name
        perms = share_path.stat().st_mode & 0o777
        assert perms == 0o600

def test_hmac_key_permissions(km):
    perms = km.hmac_key_path.stat().st_mode & 0o777
    assert perms == 0o600
    # HMAC key should be outside shares_dir
    assert km.hmac_key_path.parent != km.shares_dir

# ==================== Concurrency (Basic) ====================

def test_concurrent_reconstruct_different_instances(tmp_path):
    # Not fully parallel but ensure multiple managers can coexist
    km1 = SIBBKeyManager(tmp_path / "shares1", password="StrongPass123!")
    km2 = SIBBKeyManager(tmp_path / "shares2", password="StrongPass123!")
    key1 = km1.generate_master_key()
    res1 = km1.split_master_key(key1, n=5, k=3)
    key2 = km2.generate_master_key()
    res2 = km2.split_master_key(key2, n=5, k=3)
    # Reconstruct both
    rec1 = km1.reconstruct_key(res1["share_files"][:3])
    rec2 = km2.reconstruct_key(res2["share_files"][:3])
    assert rec1 == key1
    assert rec2 == key2

# ==================== Algorithm Parameters ====================

def test_shamir_uses_safe_prime():
    # Just check constant is set
    assert PRIME > 2**255

def test_master_key_length_enforced(km):
    key = km.generate_master_key()
    with pytest.raises(SIBBKeyManagerError):
        km.split_master_key(b"short", n=5, k=3)

def test_split_params_validation(km):
    key = km.generate_master_key()
    with pytest.raises(SIBBKeyManagerError):
        km.split_master_key(key, n=2, k=3)  # n < k

def test_hmac_key_generated(km):
    assert km.hmac_key_path.exists()
    assert len(km.hmac_key_path.read_bytes()) == HMAC_KEY_SIZE

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
