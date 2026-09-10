import os
import sys
import json
import hashlib
import tempfile
import shutil
import threading
import pytest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.sibb_storage import WORMStorageError
from tools.sibb_distributed import (
    DistributedStorage,
    StorageNode,
    create_distributed_storage,
    DistributedStorageError
)

# ==================== Fixtures ====================

@pytest.fixture
def node_paths(tmp_path):
    """Create three temporary node directories."""
    return [tmp_path / "node1", tmp_path / "node2", tmp_path / "node3"]

@pytest.fixture
def dist_storage(node_paths):
    """Create a distributed storage with 3 nodes, quorum 2, no OS immutability."""
    return create_distributed_storage(node_paths, quorum=2, use_os_immutable=False)

# ==================== Basic Distributed Write/Read ====================

def test_write_success_all_nodes(dist_storage):
    data = b"Distributed test data"
    result = dist_storage.write(data, "file.txt", {"purpose": "test"})
    success_count = sum(1 for r in result.values() if r["success"])
    assert success_count == 3
    for node in dist_storage.nodes:
        assert (node.path / "file.txt").exists()

def test_write_one_node_fails_but_quorum_met(tmp_path):
    node_paths = [tmp_path / "n1", tmp_path / "n2", tmp_path / "n3"]
    nodes = [
        StorageNode("node1", node_paths[0], use_os_immutable=False),
        StorageNode("node2", node_paths[1], use_os_immutable=False),
        StorageNode("node3", node_paths[2], use_os_immutable=False)
    ]
    dist = DistributedStorage(nodes, quorum=2)
    node3_path = node_paths[2]
    node3_path.mkdir(parents=True, exist_ok=True)
    os.chmod(node3_path, 0o444)  # make read-only to simulate failure
    try:
        data = b"data"
        result = dist.write(data, "test.txt")
        success_count = sum(1 for r in result.values() if r["success"])
        assert success_count == 2
        assert nodes[2].status != "online"
    finally:
        os.chmod(node3_path, 0o755)

def test_read_success(dist_storage):
    data = b"Distributed read test"
    dist_storage.write(data, "read.txt")
    read_data, meta = dist_storage.read("read.txt")
    assert read_data == data

def test_read_with_one_node_missing_file(dist_storage):
    data = b"data"
    dist_storage.write(data, "file.txt")
    node3 = dist_storage.nodes[2]
    os.unlink(node3.path / "file.txt")
    read_data, meta = dist_storage.read("file.txt")
    assert read_data == data

# ==================== Quorum Enforcement ====================

def test_quorum_not_met_raises(tmp_path):
    node_paths = [tmp_path / "n1", tmp_path / "n2", tmp_path / "n3"]
    nodes = [
        StorageNode("node1", node_paths[0], use_os_immutable=False),
        StorageNode("node2", node_paths[1], use_os_immutable=False),
        StorageNode("node3", node_paths[2], use_os_immutable=False)
    ]
    os.chmod(node_paths[1], 0o444)
    os.chmod(node_paths[2], 0o444)
    dist = DistributedStorage(nodes, quorum=2)
    try:
        with pytest.raises(DistributedStorageError):
            dist.write(b"data", "test.txt")
    finally:
        os.chmod(node_paths[1], 0o755)
        os.chmod(node_paths[2], 0o755)

def test_quorum_3_success(tmp_path):
    node_paths = [tmp_path / "n1", tmp_path / "n2", tmp_path / "n3"]
    nodes = [StorageNode(f"node{i+1}", p, use_os_immutable=False) for i, p in enumerate(node_paths)]
    dist = DistributedStorage(nodes, quorum=3)
    result = dist.write(b"data", "test.txt")
    success_count = sum(1 for r in result.values() if r["success"])
    assert success_count == 3

# ==================== Integrity Verification ====================

def test_verify_all_valid(dist_storage):
    dist_storage.write(b"data", "file.txt")
    verify = dist_storage.verify()
    assert verify["all_valid"] is True

def test_verify_detects_tampered_file(dist_storage):
    dist_storage.write(b"original", "file.txt")
    node2 = dist_storage.nodes[1]
    file_path = node2.path / "file.txt"
    os.chmod(file_path, 0o600)
    with open(file_path, "wb") as f:
        f.write(b"tampered")
    os.chmod(file_path, 0o444)
    verify = dist_storage.verify()
    assert verify["all_valid"] is False
    # Node should be marked as corrupted after verification
    assert node2.status == "corrupted"

def test_verify_detects_missing_file(dist_storage):
    dist_storage.write(b"data", "file.txt")
    node3 = dist_storage.nodes[2]
    os.unlink(node3.path / "file.txt")
    verify = dist_storage.verify()
    assert verify["all_valid"] is False

def test_verify_detects_unexpected_file(dist_storage):
    dist_storage.write(b"data", "file.txt")
    node1 = dist_storage.nodes[0]
    (node1.path / "unexpected.txt").write_bytes(b"extra")
    verify = dist_storage.verify()
    assert verify["all_valid"] is False

def test_verify_detects_metadata_tampering(dist_storage):
    dist_storage.write(b"data", "file.txt")
    node1 = dist_storage.nodes[0]
    # Modify metadata file directly
    meta_path = node1.storage.metadata_path
    with open(meta_path, "r") as f:
        meta = json.load(f)
    meta["files"][0]["hash"] = "deadbeef"
    with open(meta_path, "w") as f:
        json.dump(meta, f)
    verify = dist_storage.verify()
    assert verify["all_valid"] is False
    assert node1.status == "corrupted"

# ==================== Read with Hash Mismatch ====================

def test_read_detects_corrupted_data(dist_storage):
    dist_storage.write(b"correct", "file.txt")
    # Corrupt the first node so read will try it, fail, and mark it corrupted
    node1 = dist_storage.nodes[0]
    file_path = node1.path / "file.txt"
    os.chmod(file_path, 0o600)
    with open(file_path, "wb") as f:
        f.write(b"corrupted")
    os.chmod(file_path, 0o444)
    # Read should skip corrupted node1 and return data from healthy node2
    data, _ = dist_storage.read("file.txt")
    assert data == b"correct"
    assert node1.status == "corrupted"
    # Ensure node2 is still healthy
    assert dist_storage.nodes[1].status == "online"

# ==================== Node Failure Handling ====================

def test_single_node_failure_does_not_break_system(dist_storage):
    dist_storage.write(b"data", "file.txt")
    node3 = dist_storage.nodes[2]
    shutil.rmtree(node3.path)
    data, _ = dist_storage.read("file.txt")
    assert data == b"data"
    result = dist_storage.write(b"newdata", "file2.txt")
    assert sum(1 for r in result.values() if r["success"]) >= 2

def test_read_fails_when_all_nodes_down(dist_storage):
    dist_storage.write(b"data", "file.txt")
    for node in dist_storage.nodes:
        shutil.rmtree(node.path)
    with pytest.raises(DistributedStorageError):
        dist_storage.read("file.txt")

# ==================== Concurrency ====================

def test_concurrent_writes_different_files(dist_storage):
    def write_file(i):
        dist_storage.write(f"data{i}".encode(), f"file{i}.txt")
    threads = [threading.Thread(target=write_file, args=(i,)) for i in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()
    for i in range(5):
        for node in dist_storage.nodes:
            assert (node.path / f"file{i}.txt").exists()

def test_concurrent_writes_same_filename_consistent(dist_storage):
    """Ensure that only one write succeeds and all nodes have identical content."""
    successes = []
    failures = []
    barrier = threading.Barrier(5)

    def write_attempt():
        barrier.wait()
        try:
            dist_storage.write(b"data", "same.txt")
            successes.append(1)
        except Exception as e:
            failures.append(e)

    threads = [threading.Thread(target=write_attempt) for _ in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()

    # Only one write should succeed globally
    assert len(successes) == 1
    # All nodes must have the same content
    contents = set()
    for node in dist_storage.nodes:
        file_path = node.path / "same.txt"
        if file_path.exists():
            contents.add(file_path.read_bytes())
    assert len(contents) == 1

def test_concurrent_reads(dist_storage):
    dist_storage.write(b"data", "file.txt")
    def read_attempt():
        data, _ = dist_storage.read("file.txt")
        assert data == b"data"
    threads = [threading.Thread(target=read_attempt) for _ in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()

# ==================== Security ====================

def test_access_key_enforced_distributed(tmp_path, monkeypatch):
    monkeypatch.setenv("SIBB_ACCESS_KEY", "secret")
    node_paths = [tmp_path / "n1", tmp_path / "n2", tmp_path / "n3"]
    try:
        nodes = [
            StorageNode("node1", node_paths[0], use_os_immutable=False, access_key="secret"),
            StorageNode("node2", node_paths[1], use_os_immutable=False, access_key="secret"),
            StorageNode("node3", node_paths[2], use_os_immutable=False, access_key="secret")
        ]
        dist = DistributedStorage(nodes, quorum=2)
        dist.write(b"data", "file.txt")
        # Remove env var to simulate wrong key
        monkeypatch.delenv("SIBB_ACCESS_KEY")
        with pytest.raises(WORMStorageError):
            dist.write(b"new", "file2.txt")
    finally:
        pass  # cleanup handled by monkeypatch and tmp_path

def test_hmac_key_permissions_distributed(dist_storage):
    for node in dist_storage.nodes:
        if node.storage.hmac_key_path.exists():
            perms = node.storage.hmac_key_path.stat().st_mode & 0o777
            assert perms == 0o600

def test_path_traversal_rejected_distributed(dist_storage):
    with pytest.raises(WORMStorageError):
        dist_storage.write(b"data", "../evil.txt")

def test_symlink_attack_rejected_distributed(dist_storage):
    # Create symlink in one node pointing outside
    node1 = dist_storage.nodes[0]
    outside_file = node1.path.parent / "outside.txt"
    outside_file.write_bytes(b"secret")
    symlink_path = node1.path / "subdir" / "link.txt"
    symlink_path.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(outside_file, symlink_path)
    with pytest.raises(WORMStorageError):
        dist_storage.write(b"new", "subdir/link.txt")
    # Ensure no data was written to the symlink target
    assert outside_file.read_bytes() == b"secret"

# ==================== Encryption ====================

def test_encryption_distributed(tmp_path):
    node_paths = [tmp_path / "n1", tmp_path / "n2", tmp_path / "n3"]
    dist = create_distributed_storage(
        node_paths,
        encrypt=True,
        master_password="StrongPass123!",
        use_os_immutable=False,
        quorum=2
    )
    data = b"Sensitive distributed data"
    dist.write(data, "encrypted.bin")
    raw = (node_paths[0] / "encrypted.bin").read_bytes()
    assert raw != data
    read_data, _ = dist.read("encrypted.bin")
    assert read_data == data

def test_encryption_wrong_password_on_read(tmp_path):
    node_paths = [tmp_path / "n1", tmp_path / "n2", tmp_path / "n3"]
    dist = create_distributed_storage(
        node_paths,
        encrypt=True,
        master_password="StrongPass123!",
        use_os_immutable=False,
        quorum=2
    )
    dist.write(b"data", "file.txt")
    # Attempt to create a new storage with wrong password on same node paths should raise
    with pytest.raises(Exception):
        create_distributed_storage(
            node_paths,
            encrypt=True,
            master_password="WrongPass",
            use_os_immutable=False,
            quorum=2
        )

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
