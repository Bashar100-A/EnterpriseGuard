"""ADIE governance and orchestration status view."""

from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import QFormLayout, QLabel, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget


class PolicyView(QWidget):
	"""Show orchestration safety, provider, and approval-chain state."""

	def __init__(
		self,
		orchestrator: Any | None = None,
		parent: QWidget | None = None,
	) -> None:
		super().__init__(parent)
		self.orchestrator = orchestrator
		layout = QVBoxLayout(self)
		self.status_label = QLabel("Policy status: not connected")
		layout.addWidget(self.status_label)

		form = QFormLayout()
		self.execution_label = QLabel("--")
		self.contracts_label = QLabel("--")
		self.approval_label = QLabel("--")
		form.addRow("Execution mode", self.execution_label)
		form.addRow("Contracts", self.contracts_label)
		form.addRow("Approval chain", self.approval_label)
		layout.addLayout(form)

		self.providers = QTreeWidget()
		self.providers.setHeaderLabels(("Provider", "Implementation"))
		self.providers.header().setStretchLastSection(True)
		layout.addWidget(self.providers)
		self.refresh()

	def refresh(self) -> None:
		"""Read orchestration status without invoking the control plane."""
		if self.orchestrator is None:
			self.status_label.setText("Policy status: orchestrator unavailable")
			return
		try:
			status = self.orchestrator.status()
			self.status_label.setText(
				f"Policy status: {'healthy' if status.get('planning_only') else 'review required'}"
			)
			self.execution_label.setText(
				"Planning only; no security actions"
				if status.get("planning_only") and not status.get("executes_security_actions")
				else "Execution policy requires review"
			)
			providers = status.get("providers", {})
			self.contracts_label.setText(f"{len(providers)} provider contracts available")
			self.approval_label.setText(
				f"Completed: {status.get('successful_runs', 0)} | "
				f"Blocked: {status.get('blocked_runs', 0)} | "
				f"Failed: {status.get('failed_runs', 0)}"
			)
			self.providers.clear()
			for name, implementation in sorted(providers.items()):
				QTreeWidgetItem(self.providers, (str(name), str(implementation)))
		except Exception as exc:
			self.status_label.setText(f"Policy error: {exc}")
