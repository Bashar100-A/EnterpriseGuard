#!/usr/bin/env python3
"""Unit tests for tools/distributed_proof.py.

These tests run in isolated temporary environments and never touch
the real proof shards, identity, genesis, or protected directories.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Must be set before any other imports.
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.distributed_proof import (
    generate_proof_digest,
    split_digest,
    get_identity_key,
    get_genesis_hash,
    get_last_relational_node_id,
)


class TestDistributedProof(unittest.TestCase):
    """Tests for distributed proof operations."""

    def _patch_sources(
        self,
        tmpdir: str,
        identity_key: str = "id123",
        genesis_hash: str = "genesis123",
        relational_nodes: list[dict] | None = None,
    ):
        """Patch source file paths and return context managers."""
        identity_path = Path(tmpdir) / "hardware_identity.json"
        genesis_path = Path(tmpdir) / "genesis_baseline.json"
        relational_path = Path(tmpdir) / "relational_memory.json"

        identity_path.write_text(
            json.dumps({"identity_key": identity_key}), encoding="utf-8"
        )
        genesis_path.write_text(
            json.dumps({"genesis_hash": genesis_hash}), encoding="utf-8"
        )
        if relational_nodes is not None:
            relational_path.write_text(
                json.dumps({"nodes": relational_nodes}), encoding="utf-8"
            )

        return (
            patch("tools.distributed_proof.IDENTITY_PATH", identity_path),
            patch("tools.distributed_proof.GENESIS_PATH", genesis_path),
            patch("tools.distributed_proof.RELATIONAL_PATH", relational_path),
        )

    def test_generate_proof_digest_is_stable(self):
        """Same inputs must produce the same digest."""
        first = generate_proof_digest("id123", "genesis123", "node1")
        second = generate_proof_digest("id123", "genesis123", "node1")
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)

    def test_different_inputs_change_digest(self):
        """Different identity, genesis, or node must change digest."""
        digest1 = generate_proof_digest("id123", "genesis123", "node1")
        digest2 = generate_proof_digest("id456", "genesis123", "node1")
        digest3 = generate_proof_digest("id123", "genesis456", "node1")
        digest4 = generate_proof_digest("id123", "genesis123", "node2")
        self.assertNotEqual(digest1, digest2)
        self.assertNotEqual(digest1, digest3)
        self.assertNotEqual(digest1, digest4)

    def test_split_digest_reconstructs_original(self):
        """Three shards must reconstruct the original digest."""
        digest = "a" * 64
        shards = split_digest(digest)
        reconstructed = shards["local"] + shards["external"] + shards["physical"]
        self.assertEqual(reconstructed, digest)
        self.assertEqual(len(shards["local"]), 21)
        self.assertEqual(len(shards["external"]), 22)
        self.assertEqual(len(shards["physical"]), 21)

    def test_split_digest_rejects_invalid_length(self):
        """split_digest must raise ValueError for non-64-char digest."""
        with self.assertRaises(ValueError):
            split_digest("short")

    def test_get_identity_key_reads_identity_file(self):
        """get_identity_key must return the key from the identity JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with self._patch_sources(tmpdir)[0]:
                self.assertEqual(get_identity_key(), "id123")

    def test_get_identity_key_raises_if_missing_file(self):
        """get_identity_key must raise FileNotFoundError if file missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "missing.json"
            with patch("tools.distributed_proof.IDENTITY_PATH", missing):
                with self.assertRaises(FileNotFoundError):
                    get_identity_key()

    def test_get_genesis_hash_reads_genesis_file(self):
        """get_genesis_hash must return genesis hash from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with self._patch_sources(tmpdir)[1]:
                self.assertEqual(get_genesis_hash(), "genesis123")

    def test_get_last_relational_node_id_returns_last(self):
        """Must return last event ID when nodes exist."""
        nodes = [
            {"event_id": "evt1", "prev_event": "none", "next_event": "evt2", "cause": "c", "effect": "e"},
            {"event_id": "evt2", "prev_event": "evt1", "next_event": "none", "cause": "c", "effect": "e"},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            with self._patch_sources(tmpdir, relational_nodes=nodes)[2]:
                self.assertEqual(get_last_relational_node_id(), "evt2")

    def test_get_last_relational_node_id_returns_none_when_missing(self):
        """Must return 'none' when relational memory file missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with self._patch_sources(tmpdir)[2]:
                self.assertEqual(get_last_relational_node_id(), "none")


if __name__ == "__main__":
    unittest.main()