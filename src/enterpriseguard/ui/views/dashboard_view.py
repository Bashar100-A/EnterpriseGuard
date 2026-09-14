"""Realtime telemetry and alert dashboard."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
	QGridLayout,
	QLabel,
	QPushButton,
	QTableWidget,
	QTableWidgetItem,
	QVBoxLayout,
	QWidget,
)


class DashboardView(QWidget):
	"""Display dashboard service metrics and active detection queues."""

	def __init__(
		self,
		dashboard_service: Any | None = None,
		detection_service: Any | None = None,
		parent: QWidget | None = None,
	) -> None:
		super().__init__(parent)
		self.dashboard_service = dashboard_service
		self.detection_service = detection_service

		layout = QVBoxLayout(self)
		metrics = QGridLayout()
		self.total_label = QLabel("Total events: --")
		self.alert_label = QLabel("Alerts: --")
		self.escalation_label = QLabel("Escalations: --")
		self.threat_rate_label = QLabel("Threat rate: --")
		for column, label in enumerate(
			(self.total_label, self.alert_label, self.escalation_label, self.threat_rate_label)
		):
			metrics.addWidget(label, 0, column)
		layout.addLayout(metrics)

		controls = QGridLayout()
		self.status_label = QLabel("Dashboard status: not connected")
		refresh_button = QPushButton("Refresh telemetry")
		refresh_button.clicked.connect(self.refresh)
		controls.addWidget(self.status_label, 0, 0)
		controls.addWidget(refresh_button, 0, 1)
		layout.addLayout(controls)

		self.detections_table = QTableWidget(0, 4)
		self.detections_table.setHorizontalHeaderLabels(("Queue", "Operation", "Status", "Decision"))
		self.detections_table.horizontalHeader().setStretchLastSection(True)
		layout.addWidget(self.detections_table)

		self._timer = QTimer(self)
		self._timer.timeout.connect(self.refresh)
		self._timer.start(5000)
		self.refresh()

	def refresh(self) -> None:
		"""Refresh metrics and alert queues without executing actions."""
		if self.dashboard_service is None:
			self.status_label.setText("Dashboard status: service unavailable")
			return
		try:
			snapshot = self.dashboard_service.refresh()
			metrics = snapshot.get("metrics", {})
			self.total_label.setText(f"Total events: {metrics.get('total_events', 0)}")
			self.alert_label.setText(f"Alerts: {metrics.get('alert_count', 0)}")
			self.escalation_label.setText(f"Escalations: {metrics.get('escalation_count', 0)}")
			self.threat_rate_label.setText(f"Threat rate: {metrics.get('threat_rate', 0):.2%}")
			self._populate_detections(snapshot)
			health = snapshot.get("health", {})
			self.status_label.setText(f"Dashboard status: {health.get('status', 'UNKNOWN')}")
		except Exception as exc:
			self.status_label.setText(f"Dashboard error: {exc}")

	def _populate_detections(self, snapshot: dict[str, Any]) -> None:
		queues = (
			[("Alert", item) for item in snapshot.get("alerts", [])]
			+ [("Escalation", item) for item in snapshot.get("escalations", [])]
		)
		self.detections_table.setRowCount(len(queues))
		for row, (queue_name, item) in enumerate(queues):
			values = (
				queue_name,
				str(item.get("operation_id", "--")),
				str(item.get("status", "--")),
				str(item.get("decision", "--")),
			)
			for column, value in enumerate(values):
				self.detections_table.setItem(row, column, QTableWidgetItem(value))
