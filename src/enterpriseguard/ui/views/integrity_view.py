"""Cryptographic integrity and baseline verification view."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QTextEdit, QVBoxLayout, QWidget


class IntegrityView(QWidget):
	"""Run and render the repository integrity monitor result."""

	def __init__(
		self,
		integrity_module: Any | None = None,
		parent: QWidget | None = None,
	) -> None:
		super().__init__(parent)
		self.integrity_module = integrity_module or self._load_integrity_module()

		layout = QVBoxLayout(self)
		controls = QHBoxLayout()
		check_button = QPushButton("Run integrity check")
		check_button.clicked.connect(self.run_check)
		controls.addWidget(check_button)
		controls.addStretch()
		layout.addLayout(controls)

		self.report = QTextEdit(self)
		self.report.setReadOnly(True)
		self.report.setPlaceholderText("Integrity report will appear here.")
		layout.addWidget(self.report)

	def run_check(self) -> None:
		"""Execute only the monitor's read-only check operation."""
		try:
			if self.integrity_module is None:
				raise RuntimeError("integrity_monitor is unavailable")
			root = Path(__file__).resolve().parents[4]
			baseline = root / "tools" / "integrity_baseline.json"
			result = self.integrity_module.check_integrity(root, baseline)
			self.report.setPlainText(json.dumps(result, indent=2, sort_keys=True))
		except Exception as exc:
			self.report.setPlainText(json.dumps({"status": "ERROR", "error": str(exc)}, indent=2))

	@staticmethod
	def _load_integrity_module() -> Any | None:
		try:
			import importlib.util

			path = Path(__file__).resolve().parents[4] / "tools" / "integrity_monitor.py"
			spec = importlib.util.spec_from_file_location("enterpriseguard_integrity_monitor", path)
			if spec is None or spec.loader is None:
				return None
			module = importlib.util.module_from_spec(spec)
			spec.loader.exec_module(module)
			return module
		except Exception:
			return None
