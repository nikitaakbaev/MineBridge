"""Console command input widget."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QSizePolicy, QWidget


class ConsoleInput(QWidget):
    """Command input used for the Minecraft server console."""

    command_submitted = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMaximumHeight(52)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Команда Minecraft-сервера")
        self.input.setMaximumHeight(42)
        self.button = QPushButton("Отправить")
        self.button.setMaximumHeight(42)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self.input)
        layout.addWidget(self.button)

        self.button.clicked.connect(self._submit)
        self.input.returnPressed.connect(self._submit)

    def _submit(self) -> None:
        command = self.input.text().strip()
        if not command:
            return
        self.command_submitted.emit(command)
        self.input.clear()
