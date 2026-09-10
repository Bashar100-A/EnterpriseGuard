#!/usr/bin/env python3
"""
Unit tests for Innocence Chain component (final corrected version).

Uses unittest only (no pytest).
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import innocence_chain
from innocence_chain import (
    compute_ring_hash,
    generate_ring,
    verify_chain,
    CHAIN_PATH,
    IDENTITY_PATH,
    RELATIONAL_PATH,
    GENESIS_PREV_HASH,
)


class TestInnocenceChain(unittest.TestCase):

    def setUp(self):
        """Create isolated temporary files for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)

        # Redirect module-level file paths to temp dir
        self.old_chain_path = innocence_chain.CHAIN_PATH
        self.old_identity_path = innocence_chain.IDENTITY_PATH
        self.old_relational_path = innocence_chain.RELATIONAL_PATH
        innocence_chain.CHAIN_PATH = self.root / "innocence_chain.json"
        innocence_chain.IDENTITY_PATH = self.root / "hardware_identity.json"
        innocence_chain.RELATIONAL_PATH = self.root / "relational_memory.json"

        # Create a dummy hardware identity file with a known key
        self.identity_key = "test_identity_key_123"
        hw_data = {"identity_key": self.identity_key}
        self._write_json(innocence_chain.IDENTITY_PATH, hw_data)

        # Create an empty relational memory file (using "nodes" key)
        rel_data = {"nodes": []}
        self._write_json(innocence_chain.RELATIONAL_PATH, rel_data)

    def tearDown(self):
        """Restore original file paths."""
        innocence_chain.CHAIN_PATH = self.old_chain_path
        innocence_chain.IDENTITY_PATH = self.old_identity_path
        innocence_chain.RELATIONAL_PATH = self.old_relational_path

    def _write_json(self, path: Path, data: dict):
        """Write JSON to path, temporarily adjusting permissions if file exists and is read-only."""
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            try:
                os.chmod(path, 0o600)
            except OSError:
                pass
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.chmod(path, 0o444)

    def _read_json(self, path: Path) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @patch("innocence_chain._get_integrity_status")
    def test_generate_first_ring_uses_genesis_and_correct_hash(self, mock_integrity):
        """First ring uses 'genesis' and correct hash with all current components."""
        mock_integrity.return_value = "PASS"
        ring = generate_ring()

        self.assertEqual(ring["integrity_status"], "PASS")
        self.assertEqual(ring["relational_memory_snapshot"], "none")
        self.assertEqual(ring["prev_ring_hash"], GENESIS_PREV_HASH)

        expected_hash = compute_ring_hash(
            GENESIS_PREV_HASH,
            self.identity_key,
            "PASS",
            "none",
            ring.get("realtime_events_hash", "none"),
            ring.get("chain_id", ""),
            ring.get("agent_events_hash", "none"),
        )
        self.assertEqual(ring["ring_hash"], expected_hash)

        chain_data = self._read_json(innocence_chain.CHAIN_PATH)
        self.assertEqual(len(chain_data["rings"]), 1)

    @patch("innocence_chain._get_integrity_status")
    def test_generate_second_ring_links_to_first(self, mock_integrity):
        """Second ring uses first ring's hash as previous."""
        mock_integrity.return_value = "PASS"

        first_ring = generate_ring()
        second_ring = generate_ring()

        expected_second_hash = compute_ring_hash(
            first_ring["ring_hash"],
            self.identity_key,
            "PASS",
            "none",
            second_ring.get("realtime_events_hash", "none"),
            first_ring.get("chain_id", ""),
            second_ring.get("agent_events_hash", "none"),
        )
        self.assertEqual(second_ring["ring_hash"], expected_second_hash)
        self.assertEqual(second_ring["prev_ring_hash"], first_ring["ring_hash"])

        chain_data = self._read_json(innocence_chain.CHAIN_PATH)
        self.assertEqual(len(chain_data["rings"]), 2)

    @patch("innocence_chain._get_integrity_status")
    def test_verify_valid_chain(self, mock_integrity):
        """Verification passes on correct chain."""
        mock_integrity.return_value = "PASS"
        generate_ring()
        generate_ring()
        self.assertTrue(verify_chain())

    @patch("innocence_chain._get_integrity_status")
    def test_tampering_old_ring_hash_breaks_chain(self, mock_integrity):
        """Modifying any old ring_hash invalidates the whole chain."""
        mock_integrity.return_value = "PASS"
        generate_ring()
        generate_ring()

        chain_data = self._read_json(innocence_chain.CHAIN_PATH)
        chain_data["rings"][0]["ring_hash"] = "tampered"
        self._write_json(innocence_chain.CHAIN_PATH, chain_data)

        self.assertFalse(verify_chain())

    @patch("innocence_chain._get_integrity_status")
    def test_tampering_snapshot_breaks_chain(self, mock_integrity):
        """Changing relational_memory_snapshot in an old ring breaks the chain."""
        mock_integrity.return_value = "PASS"
        generate_ring()
        generate_ring()

        chain_data = self._read_json(innocence_chain.CHAIN_PATH)
        chain_data["rings"][0]["relational_memory_snapshot"] = "evt-tampered"
        self._write_json(innocence_chain.CHAIN_PATH, chain_data)

        self.assertFalse(verify_chain())

    @patch("innocence_chain._get_integrity_status")
    def test_generate_refuses_if_existing_chain_corrupted(self, mock_integrity):
        """generate_ring must not add a new ring if existing chain is corrupted."""
        mock_integrity.return_value = "PASS"
        generate_ring()
        chain_data = self._read_json(innocence_chain.CHAIN_PATH)
        chain_data["rings"][0]["ring_hash"] = "tampered"
        self._write_json(innocence_chain.CHAIN_PATH, chain_data)

        with self.assertRaises(RuntimeError):
            generate_ring()

    @patch("innocence_chain._get_integrity_status")
    def test_corrupt_chain_file_raises_on_load(self, mock_integrity):
        """If chain file exists but is invalid JSON, load_chain raises RuntimeError."""
        mock_integrity.return_value = "PASS"
        innocence_chain.CHAIN_PATH.write_text("{ invalid json", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            generate_ring()

    @patch("innocence_chain._get_integrity_status")
    def test_missing_identity_key_file_raises(self, mock_integrity):
        """If hardware_identity.json missing, generate_ring raises FileNotFoundError."""
        mock_integrity.return_value = "PASS"
        os.remove(innocence_chain.IDENTITY_PATH)
        with self.assertRaises(FileNotFoundError):
            generate_ring()

    @patch("innocence_chain._get_integrity_status")
    def test_invalid_integrity_status_rejected(self, mock_integrity):
        """generate_ring must reject integrity_status not PASS/FAIL."""
        mock_integrity.return_value = "UNKNOWN"
        with self.assertRaises(ValueError):
            generate_ring()

    @patch("innocence_chain._get_integrity_status")
    def test_relational_snapshot_from_last_event(self, mock_integrity):
        """The snapshot should be the last event_id from relational memory (nodes key)."""
        rel_data = {
            "nodes": [
                {"event_id": "evt-001", "prev_event": None, "next_event": "evt-002",
                 "cause": "c", "effect": "e", "timestamp": "..."},
                {"event_id": "evt-002", "prev_event": "evt-001", "next_event": None,
                 "cause": "c2", "effect": "e2", "timestamp": "..."}
            ]
        }
        self._write_json(innocence_chain.RELATIONAL_PATH, rel_data)

        mock_integrity.return_value = "PASS"
        ring = generate_ring()
        self.assertEqual(ring["relational_memory_snapshot"], "evt-002")

        expected = compute_ring_hash(
            GENESIS_PREV_HASH,
            self.identity_key,
            "PASS",
            "evt-002",
            ring.get("realtime_events_hash", "none"),
            ring.get("chain_id", ""),
            ring.get("agent_events_hash", "none"),
        )
        self.assertEqual(ring["ring_hash"], expected)

    def test_compute_ring_hash_is_stable(self):
        """compute_ring_hash returns same value for same inputs."""
        h1 = compute_ring_hash("genesis", "key", "PASS", "none")
        h2 = compute_ring_hash("genesis", "key", "PASS", "none")
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)

    def test_verify_missing_chain_raises(self):
        """verify_chain raises RuntimeError if chain file missing."""
        if innocence_chain.CHAIN_PATH.exists():
            os.remove(innocence_chain.CHAIN_PATH)
        with self.assertRaises(RuntimeError):
            verify_chain()

    def test_verify_empty_chain_raises(self):
        """verify_chain raises RuntimeError if chain is empty."""
        innocence_chain.CHAIN_PATH.write_text('{"rings": []}', encoding="utf-8")
        with self.assertRaises(RuntimeError):
            verify_chain()


if __name__ == "__main__":
    unittest.main()
