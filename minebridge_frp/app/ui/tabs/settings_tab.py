"""Settings tab."""

from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from minebridge_frp.app.core.app_context import AppContext
from minebridge_frp.app.ui.layouts import scroll_panel
from minebridge_frp.app.ui.theme import apply_theme
from minebridge_frp.app.ui.widgets.path_picker import PathPicker


class SettingsTab(QWidget):
    """Application settings."""

    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self.context = context
        self.settings = QSettings("MineBridge", "MineBridge FRP")

        self.frp_path = PathPicker(file_mode=False)
        self.frp_path.set_path(self.settings.value("frp_path", str(context.data_dir / "frp")))

        self.profile_path = QLineEdit(str(context.config_dir))
        self.profile_path.setReadOnly(True)

        self.theme = QComboBox()
        self.theme.addItems(["system", "light", "dark"])
        self.theme.setCurrentText(str(self.settings.value("theme", "system")))

        self.language = QComboBox()
        self.language.addItem("ru")

        self.close_behavior = QComboBox()
        self.close_behavior.addItems(
            ["спросить", "свернуть в трей", "остановить всё", "оставить сервер работать"]
        )
        self.close_behavior.setCurrentText(str(self.settings.value("close_behavior", "спросить")))

        self.timeout = QSpinBox()
        self.timeout.setRange(1, 300)
        self.timeout.setValue(int(self.settings.value("diagnostics_timeout", 30)))

        self.auto_update = QComboBox()
        self.auto_update.addItems(["enabled", "disabled"])
        self.auto_update.setCurrentText(str(self.settings.value("auto_update_frp", "enabled")))

        settings_group = QGroupBox("Настройки приложения")
        form = QFormLayout(settings_group)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.addRow("Путь хранения FRP", self.frp_path)
        form.addRow("Путь хранения профилей", self.profile_path)
        form.addRow("Автообновление FRP", self.auto_update)
        form.addRow("Тема интерфейса", self.theme)
        form.addRow("Язык", self.language)
        form.addRow("Таймаут диагностики, сек", self.timeout)
        form.addRow("При закрытии приложения", self.close_behavior)

        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(8, 8, 8, 8)
        panel_layout.addWidget(settings_group)
        panel_layout.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(scroll_panel(panel))

        self.theme.currentTextChanged.connect(self._save_theme)
        self.close_behavior.currentTextChanged.connect(
            lambda value: self.settings.setValue("close_behavior", value)
        )
        self.timeout.valueChanged.connect(
            lambda value: self.settings.setValue("diagnostics_timeout", value)
        )
        self.auto_update.currentTextChanged.connect(
            lambda value: self.settings.setValue("auto_update_frp", value)
        )
        self.frp_path.input.textChanged.connect(
            lambda value: self.settings.setValue("frp_path", value)
        )

    def _save_theme(self, theme: str) -> None:
        self.settings.setValue("theme", theme)
        self._apply_theme(theme)

    def _apply_theme(self, theme: str) -> None:
        app = QApplication.instance()
        if app is None:
            return
        apply_theme(app, theme)
