#!/usr/bin/env python3
"""Unit tests for tools/hardware_identity.py.

These tests run in an isolated temporary environment and never touch
the real tools/hardware_identity.json file or protected directories.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True

# Ensure project root is importable
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.hardware_identity import (
    generate_identity_key,
    get_machine_id,
    write_identity_file,
)


class TestHardwareIdentity(unittest.TestCase):
    """Tests for hardware identity generation."""

    def test_generate_identity_key_returns_sha256_hex(self):
        """Identity key must be a 64-character sha256 hex string."""
        key = generate_identity_key()
        self.assertIsInstance(key, str)
        self.assertEqual(len(key), 64)
        int(key, 16)  # should not raise ValueError

    def test_generate_identity_key_is_stable_for_same_hardware(self):
        """Two calls without hardware changes should return the same key."""
        first = generate_identity_key()
        second = generate_identity_key()
        self.assertEqual(first, second)

    def test_get_machine_id_returns_string(self):
        """machine-id getter must return a string (possibly empty)."""
        machine_id = get_machine_id()
        self.assertIsInstance(machine_id, str)

    def test_write_identity_file_creates_0600_file(self):
        """write_identity_file must create a valid JSON with chmod 600."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "hardware_identity.json"
            # Patch IDENTITY_PATH to the temporary path
            with patch("tools.hardware_identity.IDENTITY_PATH", output_path):
                test_key = hashlib.sha256(b"test").hexdigest()
                write_identity_file(test_key, regenerated=False)

            self.assertTrue(output_path.exists())
            self.assertTrue(output_path.stat().st_size > 0)

            mode = output_path.stat().st_mode & 0o777
            self.assertEqual(mode, 0o600)

            data = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(data["identity_key"], test_key)
            self.assertEqual(data["regenerated"], False)

    def test_main_generate_refuses_overwrite_without_force(self):
        """--generate must fail if identity file already exists and no --force."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "hardware_identity.json"
            output_path.write_text("{}", encoding="utf-8")

            with patch("tools.hardware_identity.IDENTITY_PATH", output_path):
                from tools.hardware_identity import main

                with patch.object(sys, "argv", ["hardware_identity.py", "--generate"]):
                    exit_code = main()
                    self.assertEqual(exit_code, 1)

    def test_main_regenerate_requires_confirm(self):
        """--regenerate must fail without --confirm REGEN."""
        with patch.object(sys, "argv", ["hardware_identity.py", "--regenerate"]):
            from tools.hardware_identity import main

            exit_code = main()
            self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
