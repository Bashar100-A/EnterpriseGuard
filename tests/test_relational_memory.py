#!/usr/bin/env python3
"""Unit tests for tools/relational_memory.py.

These tests run in isolated temporary environments and never touch
the real relational_memory.json or protected directories.
"""

from __future__ import annotations

import gzip
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

from tools.relational_memory import (
    record_event,
    load_live_memory,
    event_exists,
)


class TestRelationalMemory(unittest.TestCase):
    """Tests for relational memory operations."""

    def _patch_paths(self, tmpdir: str):
        live = Path(tmpdir) / "relational_memory.json"
        archive = Path(tmpdir) / "relational_memory_archive.json.gz"
        return (
            patch("tools.relational_memory.LIVE_PATH", live),
            patch("tools.relational_memory.ARCHIVE_PATH", archive),
        )

    def test_record_event_creates_node(self):
        """record_event must append a node and save it."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with self._patch_paths(tmpdir)[0], self._patch_paths(tmpdir)[1]:
                node = record_event("evt1", "none", "evt2", "cause1", "effect1")
                self.assertEqual(node["event_id"], "evt1")
                nodes = load_live_memory()
                self.assertEqual(len(nodes), 1)
                self.assertEqual(nodes[0]["event_id"], "evt1")

    def test_record_event_rejects_duplicate_id(self):
        """record_event must reject duplicate event_id."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with self._patch_paths(tmpdir)[0], self._patch_paths(tmpdir)[1]:
                record_event("evt1", "none", "evt2", "cause1", "effect1")
                with self.assertRaises(ValueError):
                    record_event("evt1", "none", "evt3", "cause2", "effect2")

    def test_record_event_rejects_empty_fields(self):
        """record_event must reject empty fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with self._patch_paths(tmpdir)[0], self._patch_paths(tmpdir)[1]:
                with self.assertRaises(ValueError):
                    record_event("", "none", "evt2", "cause1", "effect1")
                with self.assertRaises(ValueError):
                    record_event("evt1", "none", "evt2", "", "effect1")

    def test_load_live_memory_missing_returns_empty(self):
        """load_live_memory must return [] when file missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with self._patch_paths(tmpdir)[0]:
                self.assertEqual(load_live_memory(), [])

    def test_event_exists_returns_true_after_record(self):
        """event_exists must return True after a node is recorded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with self._patch_paths(tmpdir)[0], self._patch_paths(tmpdir)[1]:
                record_event("evt1", "none", "evt2", "cause1", "effect1")
                self.assertTrue(event_exists("evt1"))
                self.assertFalse(event_exists("missing"))


if __name__ == "__main__":
    unittest.main()
