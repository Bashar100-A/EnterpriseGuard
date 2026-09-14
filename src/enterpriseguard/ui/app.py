"""Main EnterpriseGuard desktop window."""

from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import QMainWindow, QTabWidget

from .views.dashboard_view import DashboardView
from .views.integrity_view import IntegrityView
from .views.policy_view import PolicyView


DARK_STYLESHEET = """
QMainWindow, QWidget { background: #1e1e2e; color: #cdd6f4; }
QTabWidget::pane { border: 1px solid #313244; background: #181825; }
QTabBar::tab { background: #181825; color: #a6adc8; padding: 10px 18px; }
QTabBar::tab:selected { color: #1e1e2e; background: #89b4fa; }
QLabel { color: #cdd6f4; }
QPushButton { background: #89b4fa; color: #1e1e2e; padding: 7px 12px; border: 0; border-radius: 3px; }
QPushButton:hover { background: #b4befe; }
QPushButton:disabled { background: #45475a; color: #7f849c; }
QTableWidget, QTreeWidget, QTextEdit { background: #181825; color: #cdd6f4; border: 1px solid #313244; }
QHeaderView::section { background: #313244; color: #cdd6f4; padding: 6px; border: 0; }
"""


class EnterpriseGuardUI(QMainWindow):
	"""Top-level window containing the operational UI views."""

	def __init__(
		self,
		*,
		dashboard_service: Any | None = None,
		detection_service: Any | None = None,
		integrity_module: Any | None = None,
		orchestrator: Any | None = None,
	) -> None:
		super().__init__()
		self.setWindowTitle("EnterpriseGuard")
		self.resize(1200, 760)
		self.setStyleSheet(DARK_STYLESHEET)

		tabs = QTabWidget(self)
		tabs.addTab(DashboardView(dashboard_service, detection_service), "Dashboard")
		tabs.addTab(IntegrityView(integrity_module), "Integrity")
		tabs.addTab(PolicyView(orchestrator), "Policy")
		self.setCentralWidget(tabs)
