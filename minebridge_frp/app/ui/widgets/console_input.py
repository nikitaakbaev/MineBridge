"""Console command input widget."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget


class ConsoleInput(QWidget):
    """Command input used for the Minecraft server console."""

    command_submitted = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Команда Minecraft-сервера")
        self.button = QPushButton("Отправить")

        layout = QHBoxLayout(self)
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

