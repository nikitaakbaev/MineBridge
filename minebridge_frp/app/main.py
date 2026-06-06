"""Application entry point."""

from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from minebridge_frp.app.core.app_context import AppContext
from minebridge_frp.app.core.logger import setup_logging
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

    window = MainWindow(context)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
