#!/usr/bin/env python3
"""
SIBB (Sovereign Immutable Black Box) Distributed Storage Layer
Geographic/local replication for SIBB proof chains.

Version: 1.2
- Built on top of WORMStorage for per-node immutability
- Supports 3+ nodes with configurable quorum (default 2)
- Writes to all nodes, succeeds if quorum met
- Security errors are propagated immediately (not swallowed)
- General failures (e.g., permission denied) are tolerated as long as quorum met
- Global write lock ensures consistency within process
- Node status tracking: online, degraded, corrupted
- Access key and encryption support inherited from WORMStorage
- Per-node HMAC keys by default (no shared key)
- Cross-node hash comparison in verify()
"""

import os
import sys
import hashlib
import threading
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from tools.sibb_storage import WORMStorage, WORMStorageError, create_worm_storage

sys.dont_write_bytecode = True

logger = logging.getLogger(__name__)


class DistributedStorageError(Exception):
    """Base exception for distributed storage errors."""


class StorageNode:
    """Represents a single WORM storage node."""

    def __init__(self, name: str, path: Path, encrypt: bool = False,
                 master_password: Optional[str] = None,
                 hmac_key_path: Optional[Path] = None,
                 use_os_immutable: bool = False,
                 access_key: Optional[str] = None,
                 hmac_key_encrypt: bool = False):
        self.name = name
        self.path = Path(path)
        # If hmac_key_path not provided, generate a unique key path for this node
        if hmac_key_path is None:
            key_dir = self.path.parent / f".{self.name}_keys"
            key_dir.mkdir(parents=True, exist_ok=True)
            hmac_key_path = key_dir / "hmac_key.bin"
        self.storage = WORMStorage(
            self.path,
            encrypt=encrypt,
            master_password=master_password,
            hmac_key_path=hmac_key_path,
            use_os_immutable=use_os_immutable,
            access_key=access_key,
            hmac_key_encrypt=hmac_key_encrypt
        )
        self.status = "online"
        self.last_error = None

    def write(self, data: bytes, filename: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Write data to this node. Returns file hash."""
        try:
            h = self.storage.write(data, filename, metadata)
            self.status = "online"
            self.last_error = None
            return h
        except WORMStorageError as e:
            # Distinguish security errors from general failures
            msg = str(e)
            if "Permission denied" in msg or "Failed to acquire metadata lock" in msg:
                self.status = "degraded"
                self.last_error = msg
            else:
                self.status = "degraded"
                self.last_error = msg
            raise
        except Exception as e:
            self.status = "degraded"
            self.last_error = str(e)
            raise

    def read(self, filename: str) -> Tuple[bytes, Dict[str, Any]]:
        """Read data from this node. Raises on error."""
        try:
            data, meta = self.storage.read(filename)
            self.status = "online"
            self.last_error = None
            return data, meta
        except WORMStorageError as e:
            if "Hash mismatch" in str(e):
                self.status = "corrupted"
            else:
                self.status = "degraded"
            self.last_error = str(e)
            raise
        except Exception as e:
            self.status = "degraded"
            self.last_error = str(e)
            raise

    def verify(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """Verify integrity of this node. Returns result dict."""
        try:
            result = self.storage.verify_integrity(filename)
            if result.get("valid", False):
                self.status = "online"
                self.last_error = None
            else:
                self.status = "corrupted"
                self.last_error = "Integrity check failed"
            return result
        except Exception as e:
            self.status = "corrupted"
            self.last_error = str(e)
            return {"valid": False, "error": str(e)}

    def list_files(self) -> List[Dict[str, Any]]:
        return self.storage.list_files()

    def is_healthy(self) -> bool:
        return self.status == "online"


class DistributedStorage:
    """
    Distributed WORM storage with replication.
    """

    MIN_NODES = 3

    def __init__(self, nodes: List[StorageNode], quorum: int = 2):
        if len(nodes) < 3:
            raise DistributedStorageError("At least 3 nodes are recommended for quorum 2")
        if quorum < 1 or quorum > len(nodes):
            raise DistributedStorageError("Invalid quorum value")
        self.nodes = nodes
        self.quorum = quorum
        self._lock = threading.RLock()
        self._write_lock = threading.RLock()

    def write(self, data: bytes, filename: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Write data to all nodes. Returns results per node.
        Raises WORMStorageError if any security violation occurs.
        Raises DistributedStorageError if quorum not met.
        """
        results = {}
        success_count = 0

        with self._write_lock:
            for node in self.nodes:
                try:
                    h = node.write(data, filename, metadata)
                    results[node.name] = {"success": True, "hash": h}
                    success_count += 1
                except WORMStorageError as e:
                    msg = str(e)
                    if "Permission denied" in msg or "Failed to acquire metadata lock" in msg:
                        # General failure (e.g., node directory not writable)
                        results[node.name] = {"success": False, "error": msg}
                        node.status = "degraded"
                        node.last_error = msg
                        logger.warning(f"Write to node {node.name} failed (general): {e}")
                        continue
                    else:
                        # Security error: abort entire write
                        logger.error(f"Security error on node {node.name}: {e}")
                        node.status = "degraded"
                        node.last_error = msg
                        raise
                except Exception as e:
                    results[node.name] = {"success": False, "error": str(e)}
                    node.status = "degraded"
                    node.last_error = str(e)
                    logger.warning(f"Write to node {node.name} failed: {e}")

        if success_count < self.quorum:
            raise DistributedStorageError(
                f"Write failed: {success_count}/{len(self.nodes)} nodes succeeded (quorum={self.quorum})"
            )

        return results

    def read(self, filename: str, verify: bool = True) -> Tuple[bytes, Dict[str, Any]]:
        """
        Read data from the first healthy node that returns valid data.
        """
        last_error = None

        for node in self.nodes:
            try:
                data, meta = node.read(filename)

                if verify:
                    expected_hash = meta.get("hash")
                    if expected_hash:
                        actual_hash = hashlib.sha256(data).hexdigest()
                        if actual_hash != expected_hash:
                            logger.warning(f"Hash mismatch on node {node.name}")
                            node.status = "corrupted"
                            node.last_error = "Hash mismatch"
                            continue

                return data, meta

            except WORMStorageError as e:
                last_error = e
                if "Hash mismatch" in str(e):
                    node.status = "corrupted"
                else:
                    node.status = "degraded"
                node.last_error = str(e)
                logger.warning(f"Read from node {node.name} failed: {e}")
                continue
            except Exception as e:
                last_error = e
                node.status = "degraded"
                node.last_error = str(e)
                logger.warning(f"Read from node {node.name} failed: {e}")
                continue

        raise DistributedStorageError(f"All nodes failed to read {filename}: {last_error}")

    def verify(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify integrity across all nodes, including cross-node hash comparison.
        """
        results = {}
        all_valid = True

        # First, let each node verify itself
        node_results = {}
        for node in self.nodes:
            res = node.verify(filename)
            node_results[node.name] = res
            results[node.name] = res
            if not res.get("valid", False):
                all_valid = False
                node.status = "corrupted"
            else:
                node.status = "online"

        # Cross-node comparison: if no filename specified and all nodes internally valid,
        # compare file lists and hashes across nodes.
        if all_valid and filename is None:
            # Gather file lists from all nodes
            reference_files = None
            for node in self.nodes:
                try:
                    files = node.list_files()
                    if reference_files is None:
                        reference_files = files
                    else:
                        ref_names = {f["filename"] for f in reference_files}
                        node_names = {f["filename"] for f in files}
                        if ref_names != node_names:
                            all_valid = False
                            node.status = "corrupted"
                            results[node.name] = {"valid": False, "error": "File set mismatch"}
                except Exception as e:
                    all_valid = False
                    node.status = "degraded"
                    results[node.name] = {"valid": False, "error": str(e)}

            # Compare hashes for each common file
            if reference_files:
                for ref_file in reference_files:
                    fname = ref_file["filename"]
                    hashes = {}
                    for node in self.nodes:
                        try:
                            meta = node.storage.get_metadata(fname)
                            if meta and meta.get("hash"):
                                hashes[node.name] = meta["hash"]
                            else:
                                hashes[node.name] = None
                        except Exception:
                            hashes[node.name] = None

                    # Determine majority hash
                    hash_counts = {}
                    for h in hashes.values():
                        if h:
                            hash_counts[h] = hash_counts.get(h, 0) + 1
                    if not hash_counts:
                        continue
                    majority_hash = max(hash_counts, key=hash_counts.get)

                    # Check each node against majority
                    for node_name, h in hashes.items():
                        if h != majority_hash:
                            all_valid = False
                            node = next(n for n in self.nodes if n.name == node_name)
                            node.status = "corrupted"
                            results[node_name] = {"valid": False, "error": f"Hash mismatch for {fname}"}

        return {
            "all_valid": all_valid,
            "nodes": results
        }

    def get_status(self) -> Dict[str, Any]:
        """Return status of all nodes."""
        healthy = sum(1 for n in self.nodes if n.is_healthy())
        return {
            "nodes": [
                {
                    "name": n.name,
                    "path": str(n.path),
                    "status": n.status,
                    "last_error": n.last_error
                }
                for n in self.nodes
            ],
            "total_nodes": len(self.nodes),
            "healthy_nodes": healthy,
            "quorum": self.quorum,
            "available": healthy >= self.quorum
        }

    def list_files(self) -> List[Dict[str, Any]]:
        """Return list of files from the first healthy node."""
        for node in self.nodes:
            if node.is_healthy():
                try:
                    files = node.list_files()
                    return files
                except Exception as e:
                    node.status = "degraded"
                    node.last_error = str(e)
                    logger.warning(f"list_files failed on node {node.name}: {e}")
        return []


def create_distributed_storage(
    base_paths: List[Path],
    encrypt: bool = False,
    master_password: Optional[str] = None,
    hmac_key_path: Optional[Path] = None,
    use_os_immutable: bool = False,
    access_key: Optional[str] = None,
    hmac_key_encrypt: bool = False,
    quorum: int = 2,
    node_names: Optional[List[str]] = None
) -> DistributedStorage:
    """
    Create a distributed storage instance with multiple nodes.
    If hmac_key_path is None, each node will get its own unique HMAC key.
    """
    if len(base_paths) < 3:
        raise DistributedStorageError("At least 3 base paths required")

    if node_names is None:
        node_names = [f"node_{i+1}" for i in range(len(base_paths))]
    elif len(node_names) != len(base_paths):
        raise DistributedStorageError("node_names length must match base_paths length")

    nodes = []
    for name, path in zip(node_names, base_paths):
        node = StorageNode(
            name=name,
            path=path,
            encrypt=encrypt,
            master_password=master_password,
            hmac_key_path=hmac_key_path,
            use_os_immutable=use_os_immutable,
            access_key=access_key,
            hmac_key_encrypt=hmac_key_encrypt
        )
        nodes.append(node)

    return DistributedStorage(nodes, quorum=quorum)


# Self-test
if __name__ == "__main__":
    import tempfile
    import shutil

    print("=" * 60)
    print("SIBB Distributed Storage - Self Test")
    print("=" * 60)

    test_dir = Path(tempfile.mkdtemp(prefix="sibb_dist_"))
    try:
        node_paths = [test_dir / f"node_{i}" for i in range(3)]
        dist = create_distributed_storage(node_paths, quorum=2, use_os_immutable=False)

        data = b"Distributed SIBB test data"
        result = dist.write(data, "test.txt", {"source": "self-test"})
        print(f"Write result: {result}")

        read_data, meta = dist.read("test.txt")
        assert read_data == data
        print("Read OK")

        verify = dist.verify()
        print(f"Verify all valid: {verify['all_valid']}")

        status = dist.get_status()
        print(f"Status: {status['healthy_nodes']}/{status['total_nodes']} healthy")

        print("Self-test passed!")

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)
