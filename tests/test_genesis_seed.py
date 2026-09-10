#!/usr/bin/env python3
"""Unit tests for tools/genesis_seed.py.

These tests run in an isolated temporary environment and never touch
the real tools/genesis_baseline.json or protected directories.
"""

from __future__ import annotations

import hashlib
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

from tools.genesis_seed import (
    generate_genesis_hash,
    read_identity_key,
    write_genesis_baseline,
)


class TestGenesisSeed(unittest.TestCase):
    """Tests for genesis seed generation."""

    def test_generate_genesis_hash_is_stable(self):
        """Same seed and identity key must produce the same hash."""
        first = generate_genesis_hash("seed123", "identityABC")
        second = generate_genesis_hash("seed123", "identityABC")
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)
        int(first, 16)  # should not raise ValueError

    def test_different_seed_changes_hash(self):
        """Different seed must produce a different hash."""
        hash1 = generate_genesis_hash("seed123", "identityABC")
        hash2 = generate_genesis_hash("seed456", "identityABC")
        self.assertNotEqual(hash1, hash2)

    def test_different_identity_changes_hash(self):
        """Different identity key must produce a different hash."""
        hash1 = generate_genesis_hash("seed123", "identityABC")
        hash2 = generate_genesis_hash("seed123", "identityXYZ")
        self.assertNotEqual(hash1, hash2)

    def test_hash_is_time_independent(self):
        """Hash must not depend on utc_now."""
        # This is already proven by stability, but we keep it explicit.
        with patch("tools.genesis_seed.utc_now_iso") as mock_time:
            mock_time.return_value = "2026-01-01T00:00:00Z"
            first = generate_genesis_hash("seed123", "identityABC")
            mock_time.return_value = "2030-12-31T23:59:59Z"
            second = generate_genesis_hash("seed123", "identityABC")
        self.assertEqual(first, second)

    def test_write_genesis_baseline_creates_444_file(self):
        """write_genesis_baseline must create a valid JSON with chmod 444."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "genesis_baseline.json"
            test_hash = hashlib.sha256(b"test").hexdigest()
            write_genesis_baseline(test_hash, "manual_cli", "identityABC", output_path)

            self.assertTrue(output_path.exists())
            self.assertTrue(output_path.stat().st_size > 0)

            mode = output_path.stat().st_mode & 0o777
            self.assertEqual(mode, 0o444)

            data = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(data["genesis_hash"], test_hash)
            self.assertEqual(data["source"], "manual_cli")
            self.assertEqual(data["identity_key"], "identityABC")
            self.assertIn("generated_at", data)

    def test_read_identity_key_raises_if_missing(self):
        """read_identity_key must raise FileNotFoundError for missing file."""
        with self.assertRaises(FileNotFoundError):
            read_identity_key(Path("/nonexistent/hardware_identity.json"))

    def test_main_generate_refuses_overwrite_without_force(self):
        """--generate must fail if genesis_baseline.json already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            identity_path = Path(tmpdir) / "hardware_identity.json"
            identity_path.write_text(
                json.dumps({"identity_key": "identityABC"}),
                encoding="utf-8",
            )
            output_path = Path(tmpdir) / "genesis_baseline.json"
            output_path.write_text("{}", encoding="utf-8")

            with (
                patch("tools.genesis_seed.IDENTITY_PATH", identity_path),
                patch("tools.genesis_seed.OUTPUT_PATH", output_path),
                patch.object(sys, "argv", ["genesis_seed.py", "--seed", "abc"]),
            ):
                from tools.genesis_seed import main

                exit_code = main()
                self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()