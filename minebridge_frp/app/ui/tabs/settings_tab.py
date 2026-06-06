"""Settings tab."""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QFormLayout, QLineEdit, QSpinBox, QVBoxLayout, QWidget

from minebridge_frp.app.core.app_context import AppContext
from minebridge_frp.app.ui.widgets.path_picker import PathPicker


class SettingsTab(QWidget):
    """Application settings placeholder."""

    def __init__(self, context: AppContext) -> None:
        super().__init__()

        theme = QComboBox()
        theme.addItems(["system", "light", "dark"])

        language = QComboBox()
        language.addItem("ru")

        close_behavior = QComboBox()
        close_behavior.addItems(
            ["спросить", "свернуть в трей", "остановить всё", "оставить сервер работать"]
        )

        timeout = QSpinBox()
        timeout.setRange(1, 300)
        timeout.setValue(30)

        auto_update = QComboBox()
        auto_update.addItems(["enabled", "disabled"])

        form = QFormLayout()
        form.addRow("Путь хранения FRP", PathPicker(file_mode=False))
        form.addRow("Путь хранения профилей", QLineEdit(str(context.config_dir)))
        form.addRow("Автообновление FRP", auto_update)
        form.addRow("Тема интерфейса", theme)
        form.addRow("Язык", language)
        form.addRow("Таймаут диагностики, сек", timeout)
        form.addRow("При закрытии приложения", close_behavior)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addStretch(1)
