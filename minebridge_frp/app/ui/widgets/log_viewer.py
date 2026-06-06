"""Log viewer widget."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPlainTextEdit, QVBoxLayout, QWidget


class LogViewer(QWidget):
    """Read-only text viewer for process and application logs."""

    def __init__(self, title: str = "Logs") -> None:
        super().__init__()
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setPlaceholderText("Логи появятся здесь.")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(title))
        layout.addWidget(self.text)

    def append_line(self, line: str) -> None:
        self.text.appendPlainText(line.rstrip())

    def clear(self) -> None:
        self.text.clear()

