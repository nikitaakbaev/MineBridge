"""Application entry point."""

from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from minebridge_frp.app.core.app_context import AppContext
from minebridge_frp.app.core.logger import setup_logging
from minebridge_frp.app.core.single_instance import SingleInstanceGuard
from minebridge_frp.app.ui.icons import load_app_icon
from minebridge_frp.app.ui.main_window import MainWindow


def main() -> int:
    """Start the MineBridge FRP desktop application."""
    context = AppContext.create()
    setup_logging(context.log_dir)
    logging.getLogger(__name__).info("Starting MineBridge FRP")

    app = QApplication(sys.argv)
    app.setApplicationName("MineBridge FRP")
    app.setOrganizationName("MineBridge")
    app.setWindowIcon(load_app_icon())

    instance_guard = SingleInstanceGuard()
    if not instance_guard.acquire():
        QMessageBox.information(None, "MineBridge FRP", "MineBridge FRP уже запущен.")
        return 0

    window = MainWindow(context)
    instance_guard.message_received.connect(lambda _message: _show_existing_window(window))
    window.show()

    return app.exec()


def _show_existing_window(window: MainWindow) -> None:
    window.showNormal()
    window.raise_()
    window.activateWindow()


if __name__ == "__main__":
    raise SystemExit(main())
