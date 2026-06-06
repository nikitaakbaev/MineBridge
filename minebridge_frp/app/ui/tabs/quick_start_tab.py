"""Quick start tab."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from minebridge_frp.app.core.exceptions import ConfigurationError
from minebridge_frp.app.services.profile_service import ProfileService
from minebridge_frp.app.ui.widgets.status_badge import StatusBadge


class QuickStartTab(QWidget):
    """Primary tab for the normal one-button user workflow."""

    def __init__(self, profile_service: ProfileService) -> None:
        super().__init__()
        self.profile_service = profile_service
        self._loading_profiles = False

        self.profile_select = QComboBox()
        self.profile_select.currentIndexChanged.connect(self._activate_selected_profile)

        address = QLineEdit()
        address.setPlaceholderText("Адрес появится после запуска туннеля")
        address.setReadOnly(True)

        form = QFormLayout()
        form.addRow("Профиль", self.profile_select)
        form.addRow("VPS", StatusBadge("Не проверен", "warning"))
        form.addRow("frps", StatusBadge("Не запущен", "warning"))
        form.addRow("Minecraft-сервер", StatusBadge("Остановлен", "warning"))
        form.addRow("frpc", StatusBadge("Остановлен", "warning"))
        form.addRow("Адрес для друзей", address)

        create_profile_button = QPushButton("Создать профиль")
        export_profile_button = QPushButton("Экспорт JSON")
        import_profile_button = QPushButton("Импорт JSON")

        profile_buttons = QHBoxLayout()
        profile_buttons.addWidget(create_profile_button)
        profile_buttons.addWidget(export_profile_button)
        profile_buttons.addWidget(import_profile_button)
        profile_buttons.addStretch(1)

        start_button = QPushButton("Запустить сервер и открыть доступ")
        start_button.setMinimumHeight(44)
        stop_button = QPushButton("Остановить всё")

        buttons = QHBoxLayout()
        buttons.addWidget(start_button)
        buttons.addWidget(stop_button)

        checklist = QLabel("Чеклист ошибок появится после диагностики профиля.")
        checklist.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(profile_buttons)
        layout.addLayout(buttons)
        layout.addWidget(checklist)
        layout.addStretch(1)

        create_profile_button.clicked.connect(self._create_profile)
        export_profile_button.clicked.connect(self._export_profile)
        import_profile_button.clicked.connect(self._import_profile)
        self.reload_profiles()

    def reload_profiles(self, selected_profile_id: int | None = None) -> None:
        self._loading_profiles = True
        self.profile_select.clear()

        active_id = self.profile_service.get_active_profile().profile.id
        target_id = selected_profile_id or active_id

        for profile in self.profile_service.list_profiles():
            label = profile.name
            if profile.is_default:
                label = f"{label} *"
            self.profile_select.addItem(label, profile.id)
            if profile.id == target_id:
                self.profile_select.setCurrentIndex(self.profile_select.count() - 1)

        self._loading_profiles = False

    def _activate_selected_profile(self) -> None:
        if self._loading_profiles:
            return

        profile_id = self.profile_select.currentData()
        if profile_id is None:
            return

        try:
            self.profile_service.set_active_profile(int(profile_id))
            self.reload_profiles(selected_profile_id=int(profile_id))
        except ConfigurationError as exc:
            QMessageBox.warning(self, "Профиль", str(exc))

    def _create_profile(self) -> None:
        name, ok = QInputDialog.getText(self, "Новый профиль", "Название профиля:")
        if not ok:
            return

        try:
            bundle = self.profile_service.create_profile(name)
            self.profile_service.set_active_profile(bundle.profile.id)
            self.reload_profiles(selected_profile_id=bundle.profile.id)
        except ConfigurationError as exc:
            QMessageBox.warning(self, "Профиль", str(exc))

    def _export_profile(self) -> None:
        profile_id = self.profile_select.currentData()
        if profile_id is None:
            return

        default_name = self.profile_select.currentText().replace(" *", "").strip() or "profile"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт профиля",
            f"{default_name}.json",
            "JSON (*.json)",
        )
        if not path:
            return

        try:
            self.profile_service.export_profile(int(profile_id), Path(path))
            QMessageBox.information(self, "Профиль", "Профиль экспортирован.")
        except ConfigurationError as exc:
            QMessageBox.warning(self, "Профиль", str(exc))

    def _import_profile(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Импорт профиля", "", "JSON (*.json)")
        if not path:
            return

        try:
            bundle = self.profile_service.import_profile(Path(path), make_default=True)
            self.reload_profiles(selected_profile_id=bundle.profile.id)
            QMessageBox.information(self, "Профиль", "Профиль импортирован и выбран активным.")
        except ConfigurationError as exc:
            QMessageBox.warning(self, "Профиль", str(exc))
