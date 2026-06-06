"""Logs tab."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTabWidget, QVBoxLayout, QWidget

from minebridge_frp.app.ui.widgets.log_viewer import LogViewer


class LogsTab(QWidget):
    """Grouped logs view."""

    def __init__(self, log_dir: Path) -> None:
        super().__init__()
        self.log_dir = log_dir

        tabs = QTabWidget()
        for name in (
            "App logs",
            "SSH logs",
            "frps logs",
            "frpc logs",
            "Minecraft logs",
            "Diagnostics logs",
        ):
            tabs.addTab(LogViewer(name), name)

        buttons = QHBoxLayout()
        buttons.addWidget(QPushButton("Очистить"))
        buttons.addWidget(QPushButton("Сохранить лог в файл"))
        buttons.addWidget(QPushButton("Открыть папку логов"))
        buttons.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(buttons)
        layout.addWidget(tabs)

