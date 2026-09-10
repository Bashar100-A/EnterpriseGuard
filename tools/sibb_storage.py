#!/usr/bin/env python3
"""
SIBB (Sovereign Immutable Black Box) Storage Layer
WORM (Write Once, Read Many) storage for AAAC proof chains.

Version: 7.3 (critical fixes)
- Master key derivation order fixed
- HMAC key regeneration on failure prevented
- Constant-time comparison for access keys
- O_NOFOLLOW for parent directories
- Salt corruption raises error
- Orphan handling disabled by default
- Additional safety checks
"""

import os
import sys
import json
import hmac
import hashlib
import tempfile
import secrets
import base64
import subprocess
import threading
import shutil
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
import logging

# Conditional imports for cross-platform file locking
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

try:
    import msvcrt
    HAS_MSVCRT = True
except ImportError:
    HAS_MSVCRT = False

# Cryptography library (optional)
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logging.warning("Cryptography library not installed - encryption disabled")

sys.dont_write_bytecode = True

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)
logger = logging.getLogger(__name__)


class WORMStorageError(Exception):
    """Base exception for WORM storage errors."""


class WORMStorage:
    """
    Immutable storage with WORM (Write Once, Read Many) semantics.

    Cross-platform security hardening (v7.3):
    - Exclusive file creation with O_CREAT|O_EXCL
    - Path traversal protection via resolve() and relative_to()
    - OS-level immutability (best-effort): chattr/chflags/readonly
    - Metadata integrity with HMAC-SHA256 and backups
    - Orphan file handling disabled by default (opt-in)
    - Access key enforcement via SIBB_ACCESS_KEY env var
    - Constant-time comparison for secrets
    - Efficient key derivation: PBKDF2 once + HKDF per file
    - Random per-file salts for encryption
    - Atomic writes for all sensitive files
    - Full I/O loops, strict hash verification on read
    - Metadata reload from disk before each operation
    """

    WORM_PERMISSIONS = 0o444
    METADATA_PERMISSIONS = 0o600
    KEY_PERMISSIONS = 0o600
    SALT_SIZE = 32
    HMAC_KEY_SIZE = 32
    PBKDF2_ITERATIONS = 480000
    MIN_PASSWORD_LENGTH = 12

    O_NOFOLLOW = getattr(os, 'O_NOFOLLOW', 0)
    HAS_DIR_FD = hasattr(os, 'open') and 'dir_fd' in os.open.__doc__ if hasattr(os, 'open') else False

    def __init__(self, base_path: Path, encrypt: bool = False, master_password: Optional[str] = None,
                 hmac_key_path: Optional[Path] = None, use_os_immutable: bool = True,
                 access_key: Optional[str] = None, hmac_key_encrypt: bool = False,
                 handle_orphans: bool = False):
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.encrypt = encrypt
        self.master_password = master_password
        self.use_os_immutable = use_os_immutable
        self.access_key = access_key
        self.hmac_key_encrypt = hmac_key_encrypt
        self.handle_orphans = handle_orphans

        if hmac_key_path is None:
            default_keys_dir = Path.home() / ".enterpriseguard" / "keys"
            default_keys_dir.mkdir(parents=True, exist_ok=True)
            hmac_key_path = default_keys_dir / "sibb_hmac_key.bin"
        self.hmac_key_path = Path(hmac_key_path)
        self.hmac_key_path.parent.mkdir(parents=True, exist_ok=True)

        self._local = threading.local()
        self._thread_lock = threading.RLock()

        self._salt_path = self.base_path / ".worm_salt.bin"
        self._salt = self._load_or_generate_salt()

        # Derive master key before HMAC key if encryption needed for HMAC
        self._master_key = None
        if encrypt:
            if not CRYPTO_AVAILABLE:
                raise WORMStorageError("Encryption requested but cryptography not available")
            if not master_password:
                raise WORMStorageError("Master password required when encrypt=True")
            if len(master_password) < self.MIN_PASSWORD_LENGTH:
                raise WORMStorageError(f"Master password must be at least {self.MIN_PASSWORD_LENGTH} characters")
            self._master_key = self._derive_master_key(master_password, self._salt)

        # Now load or generate HMAC key (can use master key if hmac_key_encrypt)
        self._hmac_key = self._load_or_generate_hmac_key()

        self.metadata_path = self.base_path / ".worm_metadata.json"
        self.metadata_hmac_path = self.base_path / ".worm_metadata.hmac"
        self.metadata_backup_path = self.base_path / ".worm_metadata.backup.json"
        self.metadata_hmac_backup_path = self.base_path / ".worm_metadata.hmac.backup"
        self._lock_path = self.base_path / ".worm_metadata.lock"
        self._lost_found_dir = self.base_path / "lost+found"

        self._acquire_metadata_lock()
        try:
            self._metadata = self._load_metadata_with_verification()
            if self.handle_orphans:
                self._handle_orphan_files()
        finally:
            self._release_metadata_lock()

        self._stats = {
            "total_writes": 0,
            "total_reads": 0,
            "last_write": None,
            "last_read": None,
            "total_files": len(self._metadata.get("files", []))
        }

        logger.info(f"WORMStorage v7.3 initialized at {self.base_path}")

    # ========================================================================
    # Authentication
    # ========================================================================
    def _check_access(self):
        if self.access_key is not None:
            env_key = os.environ.get("SIBB_ACCESS_KEY")
            if env_key is None or not hmac.compare_digest(env_key, self.access_key):
                raise WORMStorageError("Access denied: invalid access key")

    # ========================================================================
    # Platform-specific file locking
    # ========================================================================
    def _acquire_metadata_lock(self):
        """Acquire an exclusive lock on metadata file. Each thread gets its own fd."""
        try:
            fd = os.open(str(self._lock_path), os.O_CREAT | os.O_RDWR, 0o600)
            if HAS_FCNTL:
                fcntl.flock(fd, fcntl.LOCK_EX)
            elif HAS_MSVCRT:
                msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
            self._local.metadata_lock_fd = fd
        except Exception as e:
            raise WORMStorageError(f"Failed to acquire metadata lock: {e}")

    def _release_metadata_lock(self):
        fd = getattr(self._local, 'metadata_lock_fd', None)
        if fd is not None:
            try:
                if HAS_FCNTL:
                    fcntl.flock(fd, fcntl.LOCK_UN)
                elif HAS_MSVCRT:
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                os.close(fd)
            except Exception:
                pass
            finally:
                self._local.metadata_lock_fd = None

    # ========================================================================
    # Platform-specific immutability
    # ========================================================================
    def _make_immutable(self, path: Path):
        if not self.use_os_immutable:
            return
        try:
            if sys.platform.startswith('linux'):
                # check chattr exists
                if shutil.which("chattr") is None:
                    logger.warning("chattr not found; falling back to read-only permissions")
                    os.chmod(path, self.WORM_PERMISSIONS)
                else:
                    subprocess.run(["chattr", "+i", str(path)], check=False, capture_output=True)
            elif sys.platform == 'darwin':
                subprocess.run(["chflags", "uchg", str(path)], check=False, capture_output=True)
            elif sys.platform == 'win32':
                import ctypes
                FILE_ATTRIBUTE_READONLY = 0x01
                ctypes.windll.kernel32.SetFileAttributesW(str(path), FILE_ATTRIBUTE_READONLY)
            else:
                os.chmod(path, self.WORM_PERMISSIONS)
        except Exception as e:
            logger.warning(f"Could not set immutable attribute on {path}: {e}")

    def _remove_immutable(self, path: Path):
        if not self.use_os_immutable:
            return
        try:
            if sys.platform.startswith('linux'):
                if shutil.which("chattr") is None:
                    os.chmod(path, 0o600)  # fallback
                else:
                    subprocess.run(["chattr", "-i", str(path)], check=False, capture_output=True)
            elif sys.platform == 'darwin':
                subprocess.run(["chflags", "nouchg", str(path)], check=False, capture_output=True)
            elif sys.platform == 'win32':
                import ctypes
                FILE_ATTRIBUTE_READONLY = 0x01
                ctypes.windll.kernel32.SetFileAttributesW(str(path), 0x80)
        except Exception:
            pass

    # ========================================================================
    # Key and Salt Management
    # ========================================================================
    def _atomic_write_bytes(self, path: Path, data: bytes, permissions: int) -> None:
        fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.chmod(tmp_path, permissions)
            os.replace(tmp_path, path)
            self._sync_directory(path.parent)
        except Exception:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            raise

    def _sync_directory(self, path: Path) -> None:
        try:
            fd = os.open(str(path), os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        except Exception:
            pass

    def _load_or_generate_salt(self) -> bytes:
        if self._salt_path.exists():
            try:
                salt = self._salt_path.read_bytes()
                if len(salt) == self.SALT_SIZE:
                    return salt
                else:
                    raise WORMStorageError("Salt file has invalid size; cannot recover")
            except WORMStorageError:
                raise
            except Exception as e:
                raise WORMStorageError(f"Failed to read salt: {e}")
        else:
            salt = secrets.token_bytes(self.SALT_SIZE)
            self._atomic_write_bytes(self._salt_path, salt, self.KEY_PERMISSIONS)
            logger.info("Generated new random salt")
            return salt

    def _load_or_generate_hmac_key(self) -> bytes:
        if self.hmac_key_path.exists():
            try:
                key_data = self.hmac_key_path.read_bytes()
                if self.hmac_key_encrypt and self.encrypt and self.master_password:
                    if not self._master_key:
                        raise WORMStorageError("Master key not available for HMAC key decryption")
                    key = self._decrypt_hmac_key(key_data)
                else:
                    key = key_data
                if len(key) != self.HMAC_KEY_SIZE:
                    raise WORMStorageError("HMAC key file has invalid size")
                os.chmod(self.hmac_key_path, self.KEY_PERMISSIONS)
                return key
            except Exception as e:
                # Do not regenerate on failure; raise
                raise WORMStorageError(f"Failed to load HMAC key: {e}")
        else:
            key = secrets.token_bytes(self.HMAC_KEY_SIZE)
            if self.hmac_key_encrypt and self.encrypt and self.master_password:
                if not self._master_key:
                    raise WORMStorageError("Master key not available for HMAC key encryption")
                key_data = self._encrypt_hmac_key(key)
            else:
                key_data = key
            self._atomic_write_bytes(self.hmac_key_path, key_data, self.KEY_PERMISSIONS)
            logger.info(f"Generated new HMAC key at {self.hmac_key_path}")
            return key

    def _encrypt_hmac_key(self, key: bytes) -> bytes:
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._salt,
            info=b"SIBB_HMAC_KEY_ENCRYPTION",
        )
        derived = hkdf.derive(self._master_key)
        fernet = Fernet(base64.urlsafe_b64encode(derived))
        return fernet.encrypt(key)

    def _decrypt_hmac_key(self, encrypted_data: bytes) -> bytes:
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._salt,
            info=b"SIBB_HMAC_KEY_ENCRYPTION",
        )
        derived = hkdf.derive(self._master_key)
        fernet = Fernet(base64.urlsafe_b64encode(derived))
        return fernet.decrypt(encrypted_data)

    def _derive_master_key(self, password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.PBKDF2_ITERATIONS,
        )
        return kdf.derive(password.encode())

    def _derive_file_key(self, file_salt: bytes) -> bytes:
        if not self._master_key:
            raise WORMStorageError("Master key not available")
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=file_salt,
            info=b"SIBB_FILE_ENCRYPTION_KEY",
        )
        return hkdf.derive(self._master_key)

    def _get_fernet_for_file(self, file_salt: bytes) -> Fernet:
        key = self._derive_file_key(file_salt)
        return Fernet(base64.urlsafe_b64encode(key))

    # ========================================================================
    # Path Sanitization and Safe File Opening
    # ========================================================================
    def _sanitize_path(self, filename: str) -> Path:
        if not filename or ".." in filename or filename.startswith("/") or filename.startswith("~"):
            raise WORMStorageError(f"Path traversal not allowed: {filename}")

        parts = Path(filename).parts
        if any(part in ('', '.', '..') for part in parts):
            raise WORMStorageError(f"Invalid path components: {filename}")

        full_path = self.base_path / filename
        resolved = full_path.resolve()
        try:
            resolved.relative_to(self.base_path)
        except ValueError:
            raise WORMStorageError(f"Path outside storage: {filename}")
        return full_path

    def _open_parent_dirs(self, full_path: Path):
        if not self.HAS_DIR_FD:
            return None

        rel_parts = full_path.relative_to(self.base_path).parts
        if not rel_parts:
            raise WORMStorageError("Cannot open parent dirs for base_path itself")

        current = self.base_path
        parent_fd = os.open(str(current), os.O_RDONLY | os.O_DIRECTORY | self.O_NOFOLLOW)
        try:
            for part in rel_parts[:-1]:
                next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | self.O_NOFOLLOW, dir_fd=parent_fd)
                os.close(parent_fd)
                parent_fd = next_fd
            return parent_fd
        except Exception:
            if parent_fd:
                os.close(parent_fd)
            raise

    def _open_file_exclusive(self, full_path: Path):
        parent_fd = self._open_parent_dirs(full_path)
        filename = full_path.name
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | self.O_NOFOLLOW
        try:
            if parent_fd is not None:
                fd = os.open(filename, flags, self.WORM_PERMISSIONS, dir_fd=parent_fd)
            else:
                fd = os.open(str(full_path), flags, self.WORM_PERMISSIONS)
            return fd
        except FileExistsError:
            raise WORMStorageError(f"File already exists (WORM): {full_path}")
        except OSError as e:
            raise WORMStorageError(f"Failed to open file: {e}")
        finally:
            if parent_fd is not None:
                try:
                    os.close(parent_fd)
                except Exception:
                    pass

    # ========================================================================
    # Metadata Management
    # ========================================================================
    def _calculate_metadata_hmac(self, data: bytes) -> bytes:
        return hmac.digest(self._hmac_key, data, hashlib.sha256)

    def _load_metadata_with_verification(self) -> Dict[str, Any]:
        if self.metadata_path.exists():
            try:
                data = self.metadata_path.read_bytes()
                stored_hmac = self.metadata_hmac_path.read_bytes()
                expected_hmac = self._calculate_metadata_hmac(data)
                if hmac.compare_digest(stored_hmac, expected_hmac):
                    metadata = json.loads(data.decode('utf-8'))
                    logger.info("Metadata loaded and verified")
                    return metadata
                else:
                    raise WORMStorageError("Primary metadata HMAC verification failed - possible tampering")
            except WORMStorageError:
                raise
            except Exception as e:
                logger.warning(f"Error loading primary metadata: {e}")

        if self.metadata_backup_path.exists() and self.metadata_hmac_backup_path.exists():
            try:
                data = self.metadata_backup_path.read_bytes()
                stored_hmac = self.metadata_hmac_backup_path.read_bytes()
                expected_hmac = self._calculate_metadata_hmac(data)
                if hmac.compare_digest(stored_hmac, expected_hmac):
                    self._atomic_write_bytes(self.metadata_path, data, self.METADATA_PERMISSIONS)
                    self._atomic_write_bytes(self.metadata_hmac_path, stored_hmac, self.METADATA_PERMISSIONS)
                    metadata = json.loads(data.decode('utf-8'))
                    logger.warning("Metadata restored from backup")
                    return metadata
                else:
                    raise WORMStorageError("Backup metadata HMAC verification failed")
            except Exception as e:
                logger.warning(f"Error loading backup metadata: {e}")

        logger.warning("Starting with empty metadata")
        return {"files": [], "created_at": datetime.now(timezone.utc).isoformat()}

    def _save_metadata(self) -> None:
        data = json.dumps(self._metadata, indent=2, sort_keys=True).encode('utf-8')
        hmac_value = self._calculate_metadata_hmac(data)

        self._atomic_write_bytes(self.metadata_path, data, self.METADATA_PERMISSIONS)
        self._atomic_write_bytes(self.metadata_hmac_path, hmac_value, self.METADATA_PERMISSIONS)

        self._atomic_write_bytes(self.metadata_backup_path, data, self.METADATA_PERMISSIONS)
        self._atomic_write_bytes(self.metadata_hmac_backup_path, hmac_value, self.METADATA_PERMISSIONS)

        self._sync_directory(self.base_path)
        logger.debug("Metadata saved successfully")

    def _refresh_metadata_from_disk(self):
        self._metadata = self._load_metadata_with_verification()

    def _handle_orphan_files(self):
        metadata_filenames = {entry.get("filename") for entry in self._metadata.get("files", []) if entry.get("filename")}
        lost_found_rel = str(self._lost_found_dir.relative_to(self.base_path))
        for file_path in self.base_path.rglob("*"):
            if file_path.is_file() and not file_path.is_symlink():
                rel_path = str(file_path.relative_to(self.base_path))
                if rel_path.startswith(".worm_") or rel_path == lost_found_rel or rel_path.startswith(lost_found_rel + os.sep):
                    continue
                if rel_path not in metadata_filenames:
                    logger.warning(f"Found orphan file: {rel_path}, moving to lost+found")
                    dest_dir = self._lost_found_dir
                    dest_dir.mkdir(exist_ok=True)
                    dest_path = dest_dir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    self._remove_immutable(file_path)
                    shutil.move(str(file_path), str(dest_path))

    # ========================================================================
    # Core WORM Operations
    # ========================================================================
    @staticmethod
    def _write_all(fd: int, data: bytes) -> None:
        total_written = 0
        while total_written < len(data):
            written = os.write(fd, data[total_written:])
            if written <= 0:
                raise OSError("Failed to write data")
            total_written += written

    @staticmethod
    def _read_all(fd: int, size: int) -> bytes:
        chunks = []
        remaining = size
        while remaining > 0:
            chunk = os.read(fd, min(4096, remaining))
            if not chunk:
                raise OSError("Unexpected end of file")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b''.join(chunks)

    def write(self, data: bytes, filename: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        self._check_access()
        full_path = self._sanitize_path(filename)
        parent = full_path.parent
        parent.mkdir(parents=True, exist_ok=True)

        self._acquire_metadata_lock()
        try:
            with self._thread_lock:
                self._refresh_metadata_from_disk()

                if full_path.exists() or any(entry.get("filename") == filename for entry in self._metadata.get("files", [])):
                    raise WORMStorageError(f"File already exists (WORM): {filename}")

                fd = self._open_file_exclusive(full_path)
                try:
                    encrypted = False
                    file_salt_hex = None
                    data_to_write = data

                    if self.encrypt and self._master_key:
                        file_salt = secrets.token_bytes(16)
                        fernet = self._get_fernet_for_file(file_salt)
                        encrypted_data = fernet.encrypt(data)
                        encrypted = True
                        file_salt_hex = file_salt.hex()
                        data_to_write = encrypted_data

                    self._write_all(fd, data_to_write)
                    os.fsync(fd)
                except Exception:
                    try:
                        os.unlink(str(full_path))
                    except Exception:
                        pass
                    raise
                finally:
                    os.close(fd)

                os.chmod(full_path, self.WORM_PERMISSIONS)
                self._make_immutable(full_path)

                file_hash = hashlib.sha256(data).hexdigest()

                file_metadata = {
                    "filename": filename,
                    "size": len(data),
                    "hash": file_hash,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "metadata": metadata or {},
                    "encrypted": encrypted,
                    "file_salt": file_salt_hex if encrypted else None,
                }

                self._metadata["files"].append(file_metadata)
                self._save_metadata()

                self._stats["total_writes"] += 1
                self._stats["last_write"] = datetime.now(timezone.utc).isoformat()
                self._stats["total_files"] = len(self._metadata.get("files", []))

                logger.info(f"WORM write: {filename} (hash: {file_hash[:16]}...)")
                return file_hash
        except Exception as e:
            if full_path.exists():
                try:
                    self._remove_immutable(full_path)
                    full_path.unlink()
                except Exception as unlink_err:
                    logger.error(f"Failed to clean up file after error: {unlink_err}")
            raise WORMStorageError(f"WORM write failed: {e}")
        finally:
            self._release_metadata_lock()

    def read(self, filename: str) -> Tuple[bytes, Dict[str, Any]]:
        self._check_access()
        full_path = self._sanitize_path(filename)

        self._acquire_metadata_lock()
        try:
            with self._thread_lock:
                self._refresh_metadata_from_disk()
                file_metadata = None
                for entry in self._metadata.get("files", []):
                    if entry.get("filename") == filename:
                        file_metadata = entry
                        break

                if not file_metadata:
                    raise WORMStorageError(f"No metadata found for: {filename}")

                if not full_path.exists():
                    raise WORMStorageError(f"File not found: {filename}")

                try:
                    fd = os.open(str(full_path), os.O_RDONLY | self.O_NOFOLLOW)
                    try:
                        file_size = os.fstat(fd).st_size
                        raw_data = self._read_all(fd, file_size)
                    finally:
                        os.close(fd)
                except OSError as e:
                    raise WORMStorageError(f"Failed to open/read file: {e}")

                data = raw_data
                if file_metadata.get("encrypted", False):
                    if not self.encrypt or not self._master_key:
                        raise WORMStorageError(f"File encrypted but encryption not available: {filename}")

                    file_salt_hex = file_metadata.get("file_salt")
                    if not file_salt_hex:
                        raise WORMStorageError(f"Missing file salt for encrypted file: {filename}")

                    file_salt = bytes.fromhex(file_salt_hex)
                    fernet = self._get_fernet_for_file(file_salt)
                    try:
                        data = fernet.decrypt(raw_data)
                    except Exception as e:
                        raise WORMStorageError(f"Decryption failed for {filename}: {e}")

                actual_hash = hashlib.sha256(data).hexdigest()
                expected_hash = file_metadata.get("hash")
                if actual_hash != expected_hash:
                    raise WORMStorageError(
                        f"Hash mismatch for {filename}: expected {expected_hash}, got {actual_hash}"
                    )

                self._stats["total_reads"] += 1
                self._stats["last_read"] = datetime.now(timezone.utc).isoformat()

                return data, file_metadata
        finally:
            self._release_metadata_lock()

    def verify_integrity(self, filename: Optional[str] = None) -> Dict[str, Any]:
        self._check_access()
        results = {
            "verified": [],
            "failed": [],
            "unexpected": [],
            "total": 0
        }

        self._acquire_metadata_lock()
        try:
            with self._thread_lock:
                self._refresh_metadata_from_disk()
                metadata_files = {}
                for entry in self._metadata.get("files", []):
                    fname = entry.get("filename")
                    if fname:
                        metadata_files[fname] = entry

                lost_found_rel = str(self._lost_found_dir.relative_to(self.base_path))

                if filename is None:
                    for file_path in self.base_path.rglob("*"):
                        if file_path.is_file() and not file_path.is_symlink():
                            rel_path = str(file_path.relative_to(self.base_path))
                            if rel_path.startswith(".worm_") or rel_path == lost_found_rel or rel_path.startswith(lost_found_rel + os.sep):
                                continue
                            if rel_path not in metadata_files:
                                results["unexpected"].append(rel_path)

                if filename:
                    if filename not in metadata_files:
                        results["failed"].append({"filename": filename, "reason": "no_metadata"})
                        results["total"] = len(metadata_files)
                        results["valid"] = False
                        return results
                    files_to_check = [filename]
                else:
                    files_to_check = list(metadata_files.keys())

                for fname in files_to_check:
                    entry = metadata_files[fname]
                    full_path = self._sanitize_path(fname)

                    if not full_path.exists():
                        results["failed"].append({"filename": fname, "reason": "missing"})
                        continue

                    try:
                        fd = os.open(str(full_path), os.O_RDONLY | self.O_NOFOLLOW)
                        try:
                            file_size = os.fstat(fd).st_size
                            raw_data = self._read_all(fd, file_size)
                        finally:
                            os.close(fd)

                        data = raw_data
                        if entry.get("encrypted", False) and self.encrypt and self._master_key:
                            file_salt_hex = entry.get("file_salt")
                            if file_salt_hex:
                                file_salt = bytes.fromhex(file_salt_hex)
                                fernet = self._get_fernet_for_file(file_salt)
                                data = fernet.decrypt(raw_data)
                            else:
                                results["failed"].append({"filename": fname, "reason": "missing_salt"})
                                continue

                        actual_hash = hashlib.sha256(data).hexdigest()
                        expected_hash = entry.get("hash")

                        if actual_hash == expected_hash:
                            results["verified"].append(fname)
                        else:
                            results["failed"].append({
                                "filename": fname,
                                "reason": "hash_mismatch",
                                "expected": expected_hash,
                                "actual": actual_hash
                            })

                    except Exception as e:
                        results["failed"].append({"filename": fname, "reason": str(e)})

                results["total"] = len(metadata_files)
                results["valid"] = len(results["failed"]) == 0 and len(results["unexpected"]) == 0
                return results
        finally:
            self._release_metadata_lock()

    def list_files(self) -> List[Dict[str, Any]]:
        self._check_access()
        self._acquire_metadata_lock()
        try:
            with self._thread_lock:
                self._refresh_metadata_from_disk()
                return list(self._metadata.get("files", []))
        finally:
            self._release_metadata_lock()

    def get_metadata(self, filename: str) -> Optional[Dict[str, Any]]:
        self._check_access()
        self._acquire_metadata_lock()
        try:
            with self._thread_lock:
                self._refresh_metadata_from_disk()
                for entry in self._metadata.get("files", []):
                    if entry.get("filename") == filename:
                        return entry
                return None
        finally:
            self._release_metadata_lock()

    def get_status(self) -> Dict[str, Any]:
        self._check_access()
        self._acquire_metadata_lock()
        try:
            with self._thread_lock:
                return {
                    "type": "single_node",
                    "path": str(self.base_path),
                    "encryption_enabled": self.encrypt,
                    "salt_present": self._salt_path.exists(),
                    "hmac_key_present": self.hmac_key_path.exists(),
                    "metadata_verified": self.metadata_path.exists() and self.metadata_hmac_path.exists(),
                    "backup_metadata_present": self.metadata_backup_path.exists() and self.metadata_hmac_backup_path.exists(),
                    "total_files": len(self._metadata.get("files", [])),
                    "total_writes": self._stats["total_writes"],
                    "total_reads": self._stats["total_reads"],
                    "last_write": self._stats["last_write"],
                    "last_read": self._stats["last_read"],
                    "storage_healthy": self._salt_path.exists() and self.hmac_key_path.exists() and self.metadata_path.exists()
                }
        finally:
            self._release_metadata_lock()


def create_worm_storage(base_path: Path, encrypt: bool = False, password: Optional[str] = None,
                        hmac_key_path: Optional[Path] = None, use_os_immutable: bool = True,
                        access_key: Optional[str] = None, hmac_key_encrypt: bool = False,
                        handle_orphans: bool = False) -> WORMStorage:
    return WORMStorage(
        base_path,
        encrypt=encrypt,
        master_password=password,
        hmac_key_path=hmac_key_path,
        use_os_immutable=use_os_immutable,
        access_key=access_key,
        hmac_key_encrypt=hmac_key_encrypt,
        handle_orphans=handle_orphans
    )


if __name__ == "__main__":
    import tempfile
    import shutil

    print("=" * 60)
    print("SIBB WORM Storage v7.3 - Self Test")
    print("=" * 60)

    test_dir = Path(tempfile.mkdtemp(prefix="sibb_test_"))
    try:
        storage = WORMStorage(test_dir, use_os_immutable=False)
        data = b"Test data for WORM storage."
        h = storage.write(data, "test.txt", {"purpose": "self-test"})
        print(f"Write OK, hash={h[:16]}...")

        read_data, meta = storage.read("test.txt")
        assert read_data == data
        print("Read OK, data matches")

        status = storage.get_status()
        print(f"Status: total_files={status['total_files']}, healthy={status['storage_healthy']}")

        try:
            storage.write(b"new", "test.txt")
            print("ERROR: Overwrite allowed!")
        except WORMStorageError:
            print("Overwrite correctly blocked")

        verify = storage.verify_integrity()
        print(f"Verify: valid={verify['valid']}, verified={len(verify['verified'])}")

        print("Self-test passed!")

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)
