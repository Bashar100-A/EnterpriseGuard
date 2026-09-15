"""
EnterpriseGuard UI Application Module
====================================
Provides the central graphical user interface and control panel for EnterpriseGuard.
"""

import json
from typing import Any, Optional
from PyQt5.QtWidgets import (
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class Button:
    """Mock/Base UI Button widget for interface interaction."""

    def __init__(self, action: Optional[Any] = None) -> None:
        self.action = action
        self.clicked_count = 0

    def click(self) -> Any:
        self.clicked_count += 1
        if callable(self.action):
            return self.action()


class EnterpriseGuardUI(QMainWindow):
    """Main UI Window for EnterpriseGuard."""

    def __init__(
        self,
        dashboard_service: Optional[Any] = None,
        orchestrator: Optional[Any] = None,
    ) -> None:
        super().__init__()
        self.dashboard_service = dashboard_service
        self.orchestrator = orchestrator
        self.setWindowTitle("EnterpriseGuard")
        self._init_ui()

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)

        self.tab_widget = QTabWidget(self)

        # 1. Dashboard Tab
        self.dashboard_tab = QWidget()
        dash_layout = QVBoxLayout(self.dashboard_tab)

        self.refresh_btn = QPushButton("Refresh", self.dashboard_tab)
        self.refresh_btn.clicked.connect(self._on_refresh_dashboard)

        self.status_label = QLabel("Status: UNKNOWN", self.dashboard_tab)

        dash_layout.addWidget(self.refresh_btn)
        dash_layout.addWidget(self.status_label)
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")

        # 2. Integrity Tab
        self.integrity_tab = QWidget()
        integ_layout = QVBoxLayout(self.integrity_tab)

        self.run_check_btn = QPushButton("Run Check", self.integrity_tab)
        self.run_check_btn.clicked.connect(self._on_run_integrity_check)

        self.integrity_output = QTextEdit(self.integrity_tab)

        integ_layout.addWidget(self.run_check_btn)
        integ_layout.addWidget(self.integrity_output)
        self.tab_widget.addTab(self.integrity_tab, "Integrity")

        # 3. Policy Tab
        self.policy_tab = QWidget()
        self.tab_widget.addTab(self.policy_tab, "Policy")

        layout.addWidget(self.tab_widget)
        self.setCentralWidget(central_widget)

    def _on_refresh_dashboard(self) -> None:
        if self.dashboard_service:
            data = self.dashboard_service.refresh()
            status = data.get("health", {}).get("status", "HEALTHY")
            self.status_label.setText(f"Status: {status}")

    def _on_run_integrity_check(self) -> None:
        if self.orchestrator:
            res = self.orchestrator.run_integrity_check()
            self.integrity_output.setText(json.dumps(res))
