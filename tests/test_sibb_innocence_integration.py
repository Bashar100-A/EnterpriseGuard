import os
import sys
import json
import hmac
import hashlib
import base64
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.sibb_innocence_integration import (
    validate_ring_id,
    verify_ring_signature,
    compute_ring_hash,
    get_storage_backend,
    store_ring,
    retrieve_ring,
    verify_stored_rings,
    load_chain_head,
    save_chain_head,
    get_state_dir,
)
from tools.sibb_storage import WORMStorage, WORMStorageError

# ==================== Fixtures ====================

@pytest.fixture
def config_local(tmp_path):
    """Local configuration with a dummy public key file."""
    pub_key_path = tmp_path / "public_key.pem"
    # Generate a real RSA public key for signature verification tests
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    with open(pub_key_path, 'wb') as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    # Save private key for signing in tests
    priv_key_path = tmp_path / "private_key.pem"
    with open(priv_key_path, 'wb') as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    return {
        "storage_path": str(tmp_path / "sibb"),
        "distributed": False,
        "public_key_path": str(pub_key_path),
        "private_key_path": str(priv_key_path),
    }

@pytest.fixture
def config_distributed(tmp_path):
    """Distributed configuration with public key."""
    pub_key_path = tmp_path / "public_key.pem"
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    with open(pub_key_path, 'wb') as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    priv_key_path = tmp_path / "private_key.pem"
    with open(priv_key_path, 'wb') as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    return {
        "paths": [str(tmp_path / "node1"), str(tmp_path / "node2"), str(tmp_path / "node3")],
        "distributed": True,
        "quorum": 2,
        "public_key_path": str(pub_key_path),
        "private_key_path": str(priv_key_path),
    }

# ==================== Helper: sign ring ====================

def sign_ring(ring: dict, private_key_path: Path) -> str:
    """Sign the ring (excluding signature) with RSA-SHA256 and return base64 signature."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives import serialization
    with open(private_key_path, 'rb') as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)
    ring_for_sign = {k: v for k, v in ring.items() if k != "signature"}
    data = json.dumps(ring_for_sign, sort_keys=True).encode('utf-8')
    sig = private_key.sign(data, padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(sig).decode()

def create_ring(prev_hash=None, chain_id="testchain", ring_hash=None, data="somedata"):
    """Create a minimal ring dict without signature."""
    ring = {
        "chain_id": chain_id,
        "prev_ring_hash": prev_hash,
        "ring_hash": ring_hash if ring_hash else "dummy",
        "data": data,
    }
    # compute correct hash
    if ring_hash is None:
        hash_data = {k: v for k, v in ring.items() if k not in ("signature", "ring_hash")}
        ring["ring_hash"] = hashlib.sha256(json.dumps(hash_data, sort_keys=True).encode('utf-8')).hexdigest()
    return ring

# ==================== Basic Validation ====================

def test_validate_ring_id_valid():
    assert validate_ring_id("ring_001") == "ring_001"

def test_validate_ring_id_invalid():
    with pytest.raises(ValueError):
        validate_ring_id("../../evil")
    with pytest.raises(ValueError):
        validate_ring_id("bad;rm")
    with pytest.raises(ValueError):
        validate_ring_id("a" * 65)

def test_compute_ring_hash_excludes_signature_and_hash():
    ring = create_ring(prev_hash=None)
    ring["signature"] = "dummy"
    original_hash = compute_ring_hash(ring)
    # Changing signature or ring_hash should not affect computed hash
    ring2 = ring.copy()
    ring2["signature"] = "different"
    ring2["ring_hash"] = "different"
    assert compute_ring_hash(ring2) == original_hash

# ==================== Signature Verification ====================

def test_verify_signature_success(config_local):
    ring = create_ring(prev_hash=None)
    signature = sign_ring(ring, Path(config_local["private_key_path"]))
    ring["signature"] = signature
    assert verify_ring_signature(ring, Path(config_local["public_key_path"])) is True

def test_verify_signature_failure(config_local):
    ring = create_ring(prev_hash=None)
    ring["signature"] = base64.b64encode(b"badsig").decode()
    assert verify_ring_signature(ring, Path(config_local["public_key_path"])) is False

# ==================== Storage and Retrieval ====================

def test_store_and_retrieve_ring(config_local):
    ring = create_ring(prev_hash=None)
    ring["signature"] = sign_ring(ring, Path(config_local["private_key_path"]))
    assert store_ring(ring, "ring_001", config_local) is True
    retrieved = retrieve_ring("ring_001", config_local)
    assert retrieved is not None
    assert retrieved["ring_hash"] == ring["ring_hash"]

def test_store_ring_invalid_signature(config_local):
    ring = create_ring(prev_hash=None)
    ring["signature"] = "invalid"
    assert store_ring(ring, "ring_invalid", config_local) is False

def test_store_ring_duplicate_id(config_local):
    ring = create_ring(prev_hash=None)
    ring["signature"] = sign_ring(ring, Path(config_local["private_key_path"]))
    assert store_ring(ring, "dup", config_local) is True
    # Attempt same ID
    assert store_ring(ring, "dup", config_local) is False

# ==================== Chain Continuity ====================

def test_store_ring_chain_continuity(config_local):
    # First ring with no prev
    first = create_ring(prev_hash=None)
    first["signature"] = sign_ring(first, Path(config_local["private_key_path"]))
    assert store_ring(first, "r1", config_local) is True

    # Second ring with correct prev = first ring's hash
    second = create_ring(prev_hash=first["ring_hash"])
    second["signature"] = sign_ring(second, Path(config_local["private_key_path"]))
    assert store_ring(second, "r2", config_local) is True

    # Third ring with wrong prev
    third = create_ring(prev_hash="wrong")
    third["signature"] = sign_ring(third, Path(config_local["private_key_path"]))
    assert store_ring(third, "r3", config_local) is False

def test_store_ring_rollback_rejected(config_local):
    # Store first ring
    first = create_ring(prev_hash=None)
    first["signature"] = sign_ring(first, Path(config_local["private_key_path"]))
    assert store_ring(first, "r1", config_local) is True

    # Store second ring
    second = create_ring(prev_hash=first["ring_hash"])
    second["signature"] = sign_ring(second, Path(config_local["private_key_path"]))
    assert store_ring(second, "r2", config_local) is True

    # Try to store an older ring that has prev_hash = None (rollback attempt)
    old_ring = create_ring(prev_hash=None)
    old_ring["signature"] = sign_ring(old_ring, Path(config_local["private_key_path"]))
    assert store_ring(old_ring, "r3", config_local) is False  # Because prev should be second's hash

# ==================== WORM and Symlink ====================

def test_worm_overwrite_rejected(config_local):
    ring = create_ring(prev_hash=None)
    ring["signature"] = sign_ring(ring, Path(config_local["private_key_path"]))
    assert store_ring(ring, "worm_ring", config_local) is True
    # Attempt overwrite with different data
    ring2 = ring.copy()
    ring2["data"] = "changed"
    ring2["ring_hash"] = compute_ring_hash(ring2)
    ring2["signature"] = sign_ring(ring2, Path(config_local["private_key_path"]))
    assert store_ring(ring2, "worm_ring", config_local) is False

def test_symlink_attack_rejected(config_local, tmp_path):
    # Create symlink in storage directory
    storage_path = Path(config_local["storage_path"])
    storage_path.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside.txt"
    outside.write_text("secret")
    symlink = storage_path / "link.ring"
    os.symlink(outside, symlink)
    ring = create_ring(prev_hash=None)
    ring["signature"] = sign_ring(ring, Path(config_local["private_key_path"]))
    # Attempt to store with ring_id "link" should fail due to symlink or file exists
    result = store_ring(ring, "link", config_local)
    assert result is False

# ==================== Encryption ====================

def test_store_ring_encrypted(config_local):
    config_local["encrypt"] = True
    password = "StrongPass123!"
    ring = create_ring(prev_hash=None)
    ring["signature"] = sign_ring(ring, Path(config_local["private_key_path"]))
    assert store_ring(ring, "enc_ring", config_local, password=password) is True
    # Verify raw data is encrypted
    storage = get_storage_backend(config_local, encrypt=True, password=password)
    ring_path = Path(config_local["storage_path"]) / "enc_ring.ring"
    raw = ring_path.read_bytes()
    assert b"somedata" not in raw

# ==================== verify_stored_rings ====================

def test_verify_stored_rings_success(config_local):
    first = create_ring(prev_hash=None)
    first["signature"] = sign_ring(first, Path(config_local["private_key_path"]))
    store_ring(first, "r1", config_local)
    second = create_ring(prev_hash=first["ring_hash"])
    second["signature"] = sign_ring(second, Path(config_local["private_key_path"]))
    store_ring(second, "r2", config_local)
    assert verify_stored_rings(config_local) is True

def test_verify_stored_rings_corrupted(config_local):
    ring = create_ring(prev_hash=None)
    ring["signature"] = sign_ring(ring, Path(config_local["private_key_path"]))
    store_ring(ring, "corrupt_ring", config_local)
    # Corrupt the stored file after temporarily changing permissions
    ring_path = Path(config_local["storage_path"]) / "corrupt_ring.ring"
    os.chmod(ring_path, 0o600)  # allow write
    with open(ring_path, 'wb') as f:
        f.write(b"corrupted")
    os.chmod(ring_path, 0o444)  # restore read-only
    assert verify_stored_rings(config_local) is False

# ==================== Run ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
