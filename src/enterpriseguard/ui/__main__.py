"""Module entry point for ``python3 -m enterpriseguard.ui``."""

import sys

from PyQt6.QtWidgets import QApplication

from .app import EnterpriseGuardUI


def main() -> int:
	"""Create and run the desktop application."""
	application = QApplication.instance() or QApplication(sys.argv)
	window = EnterpriseGuardUI()
	window.show()
	return application.exec()


if __name__ == "__main__":
	raise SystemExit(main())
