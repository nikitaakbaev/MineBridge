"""Log viewer widget."""

from __future__ import annotations

import re

from PySide6.QtWidgets import QLabel, QPlainTextEdit, QVBoxLayout, QWidget

ANSI_ESCAPE_PATTERN = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")
CONTROL_CHARS_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class LogViewer(QWidget):
    """Read-only text viewer for process and application logs."""

    def __init__(self, title: str = "Logs") -> None:
        super().__init__()
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.text.setPlaceholderText("Логи появятся здесь.")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(title))
        layout.addWidget(self.text)

    def append_line(self, line: str) -> None:
        self.text.appendPlainText(clean_log_line(line))

    def clear(self) -> None:
        self.text.clear()


def clean_log_line(line: str) -> str:
    """Strip ANSI/control sequences from process output before showing it in Qt."""
    without_ansi = ANSI_ESCAPE_PATTERN.sub("", line)
    without_controls = CONTROL_CHARS_PATTERN.sub("", without_ansi)
    return without_controls.rstrip("\r\n")
