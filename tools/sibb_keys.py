#!/usr/bin/env python3
"""
SIBB Key Management
Shamir's Secret Sharing with AES-GCM encryption and HMAC integrity.

Version: 1.0.3 (fixed audit logging fallback)
- Master salt and threshold values stored in protected share structure
- Strict threshold enforcement during reconstruction
- Working lockout mechanism
- Symlink-safe file handling with O_NOFOLLOW
- Atomic share file writes
- Improved zeroization
"""

import os
import sys
import json
import hmac
import hashlib
import secrets
import base64
import tempfile
import shutil
import threading
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    raise RuntimeError("cryptography library is required for SIBB Key Management")

sys.dont_write_bytecode = True

logger = logging.getLogger(__name__)

# Simple audit logging fallback (avoid dependency on audit_chain API)
def append_activity(event_type, details):
    logger.warning(f"Audit event: {event_type} | {details}")

# Constants
PRIME = 2**256 - 189  # Safe prime for Shamir operations
HMAC_KEY_SIZE = 32
MASTER_KEY_SIZE = 32
PBKDF2_ITERATIONS = 480000
MIN_PASSWORD_LENGTH = 12
MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 30


class SIBBKeyManagerError(Exception):
    """Base exception for key management errors."""


class InsufficientSharesError(SIBBKeyManagerError):
    """Raised when fewer than threshold shares are provided."""


class ShareIntegrityError(SIBBKeyManagerError):
    """Raised when a share fails integrity or decryption verification."""


class AccessDeniedError(SIBBKeyManagerError):
    """Raised when password or access key is invalid."""


class SIBBKeyManager:
    """
    Manage master key splitting, encryption, storage, and reconstruction.
    """

    def __init__(self, shares_dir: Path, hmac_key_path: Optional[Path] = None,
                 password: Optional[str] = None, access_key: Optional[str] = None):
        self.shares_dir = Path(shares_dir)
        self.shares_dir.mkdir(parents=True, exist_ok=True)
        self.password = password
        self.access_key = access_key
        self._lock = threading.RLock()
        self._failed_attempts = 0
        self._lockout_until = 0.0

        # HMAC key setup
        if hmac_key_path is None:
            key_dir = self.shares_dir.parent / ".hmac_keys"
            key_dir.mkdir(parents=True, exist_ok=True)
            hmac_key_path = key_dir / "hmac_key.bin"
        self.hmac_key_path = Path(hmac_key_path)
        self.hmac_key_path.parent.mkdir(parents=True, exist_ok=True)
        self._hmac_key = self._load_or_generate_hmac_key()

    # ==================== Helper functions ====================

    def _load_or_generate_hmac_key(self) -> bytes:
        fingerprint_path = self.hmac_key_path.with_suffix('.sha256')
        if self.hmac_key_path.exists():
            key = self.hmac_key_path.read_bytes()
            if len(key) == HMAC_KEY_SIZE:
                if fingerprint_path.exists():
                    expected_fp = fingerprint_path.read_bytes().strip().decode()
                    actual_fp = hashlib.sha256(key).hexdigest()
                    if hmac.compare_digest(expected_fp, actual_fp):
                        os.chmod(self.hmac_key_path, 0o600)
                        return key
                    else:
                        raise SIBBKeyManagerError("HMAC key fingerprint mismatch - possible tampering")
                else:
                    fp = hashlib.sha256(key).hexdigest()
                    self._atomic_write_text(fingerprint_path, fp)
                    os.chmod(self.hmac_key_path, 0o600)
                    return key
            else:
                raise SIBBKeyManagerError("Invalid HMAC key size")
        else:
            key = secrets.token_bytes(HMAC_KEY_SIZE)
            self._atomic_write_bytes(self.hmac_key_path, key, 0o600)
            fp = hashlib.sha256(key).hexdigest()
            self._atomic_write_text(fingerprint_path, fp)
            return key

    def _atomic_write_bytes(self, path: Path, data: bytes, perms: int):
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.chmod(tmp, perms)
            os.replace(tmp, path)
        except Exception:
            try:
                os.unlink(tmp)
            except Exception:
                pass
            raise

    def _atomic_write_text(self, path: Path, text: str):
        self._atomic_write_bytes(path, text.encode('utf-8'), 0o600)

    def _derive_password_key(self, password: str, salt: bytes) -> bytes:
        if len(password) < MIN_PASSWORD_LENGTH:
            raise AccessDeniedError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=MASTER_KEY_SIZE,
            salt=salt,
            iterations=PBKDF2_ITERATIONS,
        )
        return kdf.derive(password.encode())

    def _derive_file_key(self, master_key: bytes, salt: bytes) -> bytes:
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=b"SIBB_SHARE_ENCRYPTION",
        )
        return hkdf.derive(master_key)

    def _encrypt_share_data(self, plaintext: bytes, key: bytes) -> Tuple[bytes, bytes]:
        nonce = secrets.token_bytes(12)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        return ciphertext, nonce

    def _decrypt_share_data(self, ciphertext: bytes, nonce: bytes, key: bytes) -> bytes:
        aesgcm = AESGCM(key)
        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext
        except Exception as e:
            raise ShareIntegrityError("Invalid share") from e

    def _compute_share_hmac(self, data: bytes) -> bytes:
        return hmac.digest(self._hmac_key, data, hashlib.sha256)

    def _serialize_share(self, share_data: Dict[str, Any]) -> bytes:
        return json.dumps(share_data, sort_keys=True).encode('utf-8')

    def _deserialize_share(self, raw: bytes) -> Dict[str, Any]:
        return json.loads(raw.decode('utf-8'))

    def _check_access(self):
        # Access key check
        if self.access_key is not None:
            env_key = os.environ.get("SIBB_ACCESS_KEY")
            if env_key is None or not hmac.compare_digest(env_key, self.access_key):
                raise AccessDeniedError("Access denied: invalid access key")
        # Lockout check
        current = time.time()
        if current < self._lockout_until:
            raise AccessDeniedError("Too many failed attempts. Try again later.")

    def _record_failure(self):
        self._failed_attempts += 1
        if self._failed_attempts >= MAX_ATTEMPTS:
            self._lockout_until = time.time() + LOCKOUT_SECONDS
            # Do not reset failed_attempts here; it will be reset on successful operation

    def _record_success(self):
        self._failed_attempts = 0
        self._lockout_until = 0.0

    def _secure_delete_file(self, path: Path):
        try:
            if path.exists():
                with open(path, 'wb') as f:
                    f.write(b'\x00' * path.stat().st_size)
                os.unlink(path)
        except Exception:
            pass

    def _validate_share_path(self, share_name: str) -> Path:
        """
        Validate share filename, prevent path traversal and symlinks.
        Returns resolved path inside shares_dir.
        """
        if not share_name or ".." in share_name or share_name.startswith("/"):
            raise SIBBKeyManagerError("Invalid share name")
        full = (self.shares_dir / share_name).resolve()
        try:
            full.relative_to(self.shares_dir)
        except ValueError:
            raise SIBBKeyManagerError("Path outside shares directory")
        # Check for symlinks in path components
        current = self.shares_dir
        for part in full.relative_to(self.shares_dir).parts:
            current = current / part
            if current.is_symlink():
                raise SIBBKeyManagerError("Symlinks not allowed")
        return full

    def _open_share_file(self, share_path: Path, flags: int):
        """Open share file with O_NOFOLLOW to prevent symlink attacks."""
        fd = os.open(str(share_path), flags | getattr(os, 'O_NOFOLLOW', 0))
        return fd

    def _read_share_file(self, share_path: Path) -> bytes:
        fd = self._open_share_file(share_path, os.O_RDONLY)
        try:
            with os.fdopen(fd, 'rb') as f:
                return f.read()
        finally:
            pass  # The context manager will close the file descriptor

    def _write_share_file(self, share_path: Path, data: bytes):
        self._atomic_write_bytes(share_path, data, 0o600)

    # ==================== Shamir Implementation ====================

    @staticmethod
    def _eval_poly(coefficients: List[int], x: int) -> int:
        result = 0
        for coeff in reversed(coefficients):
            result = (result * x + coeff) % PRIME
        return result

    @staticmethod
    def _interpolate(points: List[Tuple[int, int]]) -> int:
        # Ensure x values are unique
        xs = [p[0] for p in points]
        if len(xs) != len(set(xs)):
            raise ShareIntegrityError("Duplicate share x values")
        secret = 0
        for i, (xi, yi) in enumerate(points):
            numerator = 1
            denominator = 1
            for j, (xj, _) in enumerate(points):
                if i == j:
                    continue
                numerator = (numerator * (0 - xj)) % PRIME
                denominator = (denominator * (xi - xj)) % PRIME
            lagrange = numerator * pow(denominator, -1, PRIME) % PRIME
            secret = (secret + yi * lagrange) % PRIME
        return secret

    def _split_secret(self, secret: bytes, n: int, k: int) -> List[Tuple[int, int]]:
        if n < k:
            raise SIBBKeyManagerError("Number of shares must be >= threshold")
        if k < 1:
            raise SIBBKeyManagerError("Threshold must be >= 1")

        secret_int = int.from_bytes(secret, 'big')
        if secret_int >= PRIME:
            raise SIBBKeyManagerError("Secret too large")

        coefficients = [secret_int] + [secrets.randbelow(PRIME) for _ in range(k - 1)]
        shares = []
        for i in range(1, n + 1):
            x = i
            y = self._eval_poly(coefficients, x)
            shares.append((x, y))
        return shares

    def _recover_secret(self, points: List[Tuple[int, int]]) -> bytes:
        if len(points) < 2:
            raise InsufficientSharesError("At least 2 shares required")
        secret_int = self._interpolate(points)
        secret = secret_int.to_bytes((secret_int.bit_length() + 7) // 8, 'big')
        if len(secret) < MASTER_KEY_SIZE:
            secret = secret.rjust(MASTER_KEY_SIZE, b'\x00')
        return secret

    # ==================== Core API ====================

    def generate_master_key(self) -> bytes:
        self._check_access()
        key = secrets.token_bytes(MASTER_KEY_SIZE)
        return key

    def split_master_key(self, master_key: bytes, n: int = 5, k: int = 3,
                         password: Optional[str] = None) -> Dict[str, Any]:
        self._check_access()
        if password is None:
            password = self.password
        if password is None:
            raise AccessDeniedError("Password is required to split key")
        if len(master_key) != MASTER_KEY_SIZE:
            raise SIBBKeyManagerError("Master key must be 32 bytes")

        # Global salt for password key derivation
        master_salt = secrets.token_bytes(16)
        password_key = self._derive_password_key(password, master_salt)

        key_id = secrets.token_hex(16)
        points = self._split_secret(master_key, n, k)

        share_files = []
        for idx, (x, y) in enumerate(points):
            share_data = {
                "key_id": key_id,
                "share_id": secrets.token_hex(8),
                "x": x,
                "y": y,
            }
            share_plain = self._serialize_share(share_data)
            share_salt = secrets.token_bytes(16)
            file_key = self._derive_file_key(password_key, share_salt)
            ciphertext, nonce = self._encrypt_share_data(share_plain, file_key)

            protected = {
                "key_id": key_id,
                "share_id": share_data["share_id"],
                "master_salt": base64.b64encode(master_salt).decode(),
                "salt": base64.b64encode(share_salt).decode(),
                "nonce": base64.b64encode(nonce).decode(),
                "ciphertext": base64.b64encode(ciphertext).decode(),
                "n": n,
                "k": k,
            }
            protected_raw = self._serialize_share(protected)
            share_hmac = self._compute_share_hmac(protected_raw)

            file_bytes = protected_raw + b"\n" + base64.b64encode(share_hmac)
            share_path = self._validate_share_path(f"{key_id}_{idx+1}.share")
            self._write_share_file(share_path, file_bytes)
            share_files.append(share_path.name)

            # Zeroize sensitive keys
            self._zeroize(password_key)
            self._zeroize(file_key)

        append_activity("key_split", {"key_id": key_id, "shares": n, "threshold": k})

        return {
            "key_id": key_id,
            "shares_created": len(share_files),
            "threshold": k,
            "share_files": share_files,
        }

    def reconstruct_key(self, share_files: List[str], password: Optional[str] = None) -> bytes:
        self._check_access()
        if password is None:
            password = self.password
        if password is None:
            raise AccessDeniedError("Password is required to reconstruct key")

        if len(share_files) < 2:
            raise InsufficientSharesError("Not enough shares provided")

        valid_points = []
        seen_key_ids = set()
        master_salt = None
        n = None
        k = None

        for share_name in share_files:
            share_path = self._validate_share_path(share_name)
            if not share_path.exists():
                raise ShareIntegrityError("Invalid share")

            raw = self._read_share_file(share_path)
            parts = raw.rsplit(b"\n", 1)
            if len(parts) != 2:
                raise ShareIntegrityError("Invalid share")
            protected_raw, hmac_b64 = parts
            expected_hmac = base64.b64decode(hmac_b64)
            actual_hmac = self._compute_share_hmac(protected_raw)
            if not hmac.compare_digest(expected_hmac, actual_hmac):
                self._record_failure()
                raise ShareIntegrityError("Invalid share")

            protected = self._deserialize_share(protected_raw)
            key_id = protected.get("key_id")
            if not key_id:
                self._record_failure()
                raise ShareIntegrityError("Invalid share")
            seen_key_ids.add(key_id)

            # Extract n and k
            if n is None:
                n = protected.get("n")
                k = protected.get("k")
                master_salt = base64.b64decode(protected["master_salt"])
            else:
                if protected.get("n") != n or protected.get("k") != k:
                    self._record_failure()
                    raise ShareIntegrityError("Inconsistent share parameters")
                if base64.b64decode(protected["master_salt"]) != master_salt:
                    self._record_failure()
                    raise ShareIntegrityError("Inconsistent master salt")

            # Derive password key from master_salt
            password_key = self._derive_password_key(password, master_salt)

            share_salt = base64.b64decode(protected["salt"])
            file_key = self._derive_file_key(password_key, share_salt)
            nonce = base64.b64decode(protected["nonce"])
            ciphertext = base64.b64decode(protected["ciphertext"])
            try:
                plaintext = self._decrypt_share_data(ciphertext, nonce, file_key)
            except ShareIntegrityError:
                self._record_failure()
                raise

            share_data = self._deserialize_share(plaintext)
            if share_data.get("key_id") != key_id:
                self._record_failure()
                raise ShareIntegrityError("Invalid share")

            x = share_data["x"]
            y = share_data["y"]
            if any(p[0] == x for p in valid_points):
                self._record_failure()
                raise ShareIntegrityError("Duplicate share x")
            valid_points.append((x, y))

            self._zeroize(password_key)
            self._zeroize(file_key)

        if k is not None and len(valid_points) < k:
            raise InsufficientSharesError(f"Need at least {k} valid shares, got {len(valid_points)}")

        secret = self._recover_secret(valid_points)

        self._record_success()
        append_activity("key_reconstruct", {"key_id": list(seen_key_ids)[0] if seen_key_ids else "unknown"})

        return secret

    def verify_share(self, share_name: str) -> bool:
        share_path = self._validate_share_path(share_name)
        if not share_path.exists():
            return False
        raw = self._read_share_file(share_path)
        parts = raw.rsplit(b"\n", 1)
        if len(parts) != 2:
            return False
        protected_raw, hmac_b64 = parts
        expected_hmac = base64.b64decode(hmac_b64)
        actual_hmac = self._compute_share_hmac(protected_raw)
        return hmac.compare_digest(expected_hmac, actual_hmac)

    def delete_share(self, share_name: str):
        self._check_access()
        share_path = self._validate_share_path(share_name)
        if share_path.exists():
            self._secure_delete_file(share_path)
            append_activity("share_delete", {"share": share_name})

    def list_shares(self) -> List[str]:
        self._check_access()
        files = []
        for p in self.shares_dir.iterdir():
            if p.is_file() and p.suffix == ".share":
                files.append(p.name)
        return files

    def get_status(self) -> Dict[str, Any]:
        return {
            "shares_dir": str(self.shares_dir),
            "hmac_key_path": str(self.hmac_key_path),
            "hmac_key_exists": self.hmac_key_path.exists(),
            "hmac_key_permissions": oct(self.hmac_key_path.stat().st_mode & 0o777) if self.hmac_key_path.exists() else None,
            "shares_count": len(self.list_shares()),
        }

    def _zeroize(self, data):
        """Attempt to zeroize sensitive data. Best effort in Python."""
        if isinstance(data, bytearray):
            for i in range(len(data)):
                data[i] = 0
        elif isinstance(data, bytes):
            ba = bytearray(data)
            for i in range(len(ba)):
                ba[i] = 0


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        km = SIBBKeyManager(Path(tmp) / "shares", password="StrongPass123!")
        key = km.generate_master_key()
        result = km.split_master_key(key, n=5, k=3)
        print("Split result:", result["key_id"], result["shares_created"], "shares")
        shares = result["share_files"]
        recovered = km.reconstruct_key(shares[:3])
        assert recovered == key
        print("Reconstruction successful")
