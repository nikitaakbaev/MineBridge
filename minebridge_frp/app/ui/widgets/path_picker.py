"""Path picker widget."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QWidget,
)


class PathPicker(QWidget):
    """Line edit plus browse button for files and directories."""

    def __init__(self, file_mode: bool) -> None:
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMaximumHeight(42)
        self.file_mode = file_mode
        self.input = QLineEdit()
        self.input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.input.setMinimumHeight(34)
        self.input.setMaximumHeight(42)
        self.button = QPushButton("...")
        self.button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.button.setFixedWidth(36)
        self.button.setMinimumHeight(34)
        self.button.setMaximumHeight(42)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.input)
        layout.addWidget(self.button)

        self.button.clicked.connect(self._choose_path)

    def path(self) -> Path | None:
        value = self.input.text().strip()
        return Path(value) if value else None

    def text(self) -> str:
        return self.input.text().strip()

    def set_path(self, path: str | Path) -> None:
        self.input.setText(str(path))

    def _choose_path(self) -> None:
        if self.file_mode:
            path, _ = QFileDialog.getOpenFileName(self, "Выберите файл")
        else:
            path = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if path:
            self.input.setText(path)
