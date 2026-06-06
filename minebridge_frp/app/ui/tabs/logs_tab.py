"""Logs tab."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices, QTextCursor
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from minebridge_frp.app.ui.widgets.log_viewer import LogViewer


class LogsTab(QWidget):
    """Grouped application log viewer."""

    FILTERS = {
        "App logs": (),
        "SSH/VPS": ("paramiko", "SSH", "VPS", "frps", "systemctl"),
        "frpc": ("frpc",),
        "Minecraft": ("Minecraft", "MC:", "java", "server.jar"),
        "Diagnostics": ("diagnostic", "Диагностика", "Diagnostic"),
    }

    def __init__(self, log_dir: Path) -> None:
        super().__init__()
        self.log_dir = log_dir
        self.log_file = log_dir / "minebridge-frp.log"
        self.viewers: dict[str, LogViewer] = {}

        self.tabs = QTabWidget()
        for name in self.FILTERS:
            viewer = LogViewer(name)
            self.viewers[name] = viewer
            self.tabs.addTab(viewer, name)

        refresh_button = QPushButton("Обновить")
        clear_button = QPushButton("Очистить окно")
        save_button = QPushButton("Сохранить лог в файл")
        open_folder_button = QPushButton("Открыть папку логов")

        buttons = QHBoxLayout()
        buttons.addWidget(refresh_button)
        buttons.addWidget(clear_button)
        buttons.addWidget(save_button)
        buttons.addWidget(open_folder_button)
        buttons.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(buttons)
        layout.addWidget(self.tabs)

        refresh_button.clicked.connect(self.refresh)
        clear_button.clicked.connect(self._clear_current)
        save_button.clicked.connect(self._save_current)
        open_folder_button.clicked.connect(self._open_log_folder)

        self.refresh()

    def refresh(self) -> None:
        """Reload the current application log file into all filtered tabs."""
        lines = self._read_log_lines()
        for name, needles in self.FILTERS.items():
            viewer = self.viewers[name]
            viewer.clear()
            filtered = self._filter_lines(lines, needles)
            if filtered:
                viewer.text.setPlainText("\n".join(filtered[-3000:]))
            else:
                viewer.text.setPlainText(self._empty_text(name))
            viewer.text.moveCursor(QTextCursor.MoveOperation.End)

    def _read_log_lines(self) -> list[str]:
        if not self.log_file.exists():
            return []
        try:
            return self.log_file.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:
            return [f"Не удалось прочитать лог: {exc}"]

    def _filter_lines(self, lines: list[str], needles: tuple[str, ...]) -> list[str]:
        if not needles:
            return lines
        lowered_needles = tuple(needle.lower() for needle in needles)
        return [
            line
            for line in lines
            if any(needle in line.lower() for needle in lowered_needles)
        ]

    def _empty_text(self, name: str) -> str:
        if not self.log_file.exists():
            return f"Файл логов ещё не создан: {self.log_file}"
        return f"В текущем логе нет записей для раздела «{name}»."

    def _current_viewer(self) -> LogViewer:
        return self.tabs.currentWidget()

    def _clear_current(self) -> None:
        self._current_viewer().clear()

    def _save_current(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить лог",
            "minebridge-log.txt",
            "Text (*.txt)",
        )
        if not path:
            return
        try:
            Path(path).write_text(self._current_viewer().text.toPlainText(), encoding="utf-8")
        except OSError as exc:
            QMessageBox.warning(self, "Логи", f"Не удалось сохранить лог: {exc}")

    def _open_log_folder(self) -> None:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.log_dir)))
