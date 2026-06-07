"""VPS configuration tab."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QInputDialog,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from minebridge_frp.app.core.app_context import AppContext
from minebridge_frp.app.core.exceptions import ConfigurationError
from minebridge_frp.app.models.vps import VpsConfig
from minebridge_frp.app.services.password_vault import PasswordVault
from minebridge_frp.app.services.profile_service import ProfileService
from minebridge_frp.app.services.vps_manager import VpsManager
from minebridge_frp.app.ui.layouts import (
    FlowLayout,
    prepare_action_button,
    profile_selector_panel,
    scroll_panel,
)
from minebridge_frp.app.ui.widgets.log_viewer import LogViewer
from minebridge_frp.app.ui.widgets.path_picker import PathPicker
from minebridge_frp.app.ui.workers import run_in_thread


class VpsTab(QWidget):
    """VPS SSH and remote FRP controls."""

    profile_changed = Signal()

    def __init__(self, context: AppContext, profile_service: ProfileService) -> None:
        super().__init__()
        self.context = context
        self.profile_service = profile_service
        self.password_vault = PasswordVault(context.config_dir)
        self._threads = []
        self._autosave_enabled = False
        self._profile_loading = False

        self.profile_select = QComboBox()
        self.profile_select.setMinimumWidth(260)

        self.host = QLineEdit()
        self.ssh_port = QSpinBox()
        self.ssh_port.setRange(1, 65535)
        self.ssh_port.setValue(22)

        self.username = QLineEdit()
        self.auth_type = QComboBox()
        self.auth_type.addItems(["password", "private_key"])

        self.bind_port = QSpinBox()
        self.bind_port.setRange(1, 65535)
        self.bind_port.setValue(7000)

        self.dashboard_port = QSpinBox()
        self.dashboard_port.setRange(1, 65535)
        self.dashboard_port.setValue(7500)

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.private_key_path = PathPicker(file_mode=True)
        self.install_dir = QLineEdit("/opt/minebridge-frp")
        self.dashboard_enabled = QCheckBox()

        profile_group = QGroupBox("Профиль")
        profile_layout = QVBoxLayout(profile_group)
        profile_layout.addWidget(
            profile_selector_panel(
                self.profile_select,
                self._create_profile,
                self._rename_profile,
                self._delete_profile,
            )
        )

        settings_group = QGroupBox("Подключение и frps")
        form = QFormLayout(settings_group)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.addRow("VPS IP / host", self.host)
        form.addRow("SSH port", self.ssh_port)
        form.addRow("SSH username", self.username)
        form.addRow("Auth type", self.auth_type)
        form.addRow("Password", self.password)
        form.addRow("Private key path", self.private_key_path)
        form.addRow("Папка frps на VPS", self.install_dir)
        form.addRow("Порт frps на VPS", self.bind_port)
        form.addRow("Dashboard включен", self.dashboard_enabled)
        form.addRow("Dashboard port", self.dashboard_port)

        actions = QGroupBox("Действия VPS")
        actions_layout = FlowLayout(actions, margin=2, spacing=8)
        buttons = [
            ("Сохранить настройки", self._save_clicked),
            ("Проверить SSH", self._check_ssh),
            ("Скачать и установить frps на VPS", self._install_frp),
            ("Обновить frps на VPS", self._install_frp),
            ("Создать frps.toml", self._create_frps_toml),
            ("Установить systemd-сервис", self._install_systemd),
            ("Запустить frps", lambda: self._run_vps_action("Запуск frps", "start_frps")),
            ("Остановить frps", lambda: self._run_vps_action("Остановка frps", "stop_frps")),
            ("Перезапустить frps", lambda: self._run_vps_action("Рестарт frps", "restart_frps")),
            ("Проверить статус frps", self._status_frps),
            ("Открыть порт в firewall", self._open_firewall),
        ]
        for label, callback in buttons:
            button = prepare_action_button(QPushButton(label))
            button.clicked.connect(callback)
            actions_layout.addWidget(button)

        self.log_viewer = LogViewer("VPS logs")
        self.log_viewer.setMinimumHeight(160)

        controls = QWidget()
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(8, 8, 8, 8)
        controls_layout.setSpacing(10)
        controls_layout.addWidget(profile_group)
        controls_layout.addWidget(settings_group)
        controls_layout.addWidget(actions)
        controls_layout.addStretch(1)

        splitter = QSplitter()
        splitter.setOrientation(Qt.Orientation.Vertical)
        splitter.addWidget(scroll_panel(controls))
        splitter.addWidget(self.log_viewer)
        splitter.setChildrenCollapsible(False)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        splitter.setSizes([420, 260])

        layout = QVBoxLayout(self)
        layout.addWidget(splitter)

        self.reload_active_profile()
        self._update_auth_fields()
        self._connect_autosave()
        self._autosave_enabled = True

    def reload_active_profile(self) -> None:
        was_autosave_enabled = self._autosave_enabled
        self._autosave_enabled = False
        self._profile_loading = True
        try:
            self._load_profile_options()
            self._load_active_profile()
            self._update_auth_fields()
        finally:
            self._profile_loading = False
            self._autosave_enabled = was_autosave_enabled

    def _load_profile_options(self) -> None:
        active_id = self.profile_service.get_active_vps_profile().profile.id
        self.profile_select.blockSignals(True)
        self.profile_select.clear()
        for profile in self.profile_service.list_vps_profiles():
            self.profile_select.addItem(profile.name, profile.id)
            if profile.id == active_id:
                self.profile_select.setCurrentIndex(self.profile_select.count() - 1)
        self.profile_select.blockSignals(False)

    def _load_active_profile(self) -> None:
        config = self.profile_service.get_active_vps_profile().config
        self.host.setText(config.host)
        self.ssh_port.setValue(config.ssh_port)
        self.username.setText(config.username)
        self.auth_type.setCurrentText(config.auth_type)
        self._load_saved_password(config)
        self.private_key_path.set_path(config.private_key_path)
        self.install_dir.setText(config.install_dir)
        self.bind_port.setValue(config.frps_bind_port)
        self.dashboard_enabled.setChecked(config.dashboard_enabled)
        self.dashboard_port.setValue(config.dashboard_port)

    def _config_from_ui(self) -> VpsConfig:
        return VpsConfig(
            host=self.host.text().strip(),
            ssh_port=self.ssh_port.value(),
            username=self.username.text().strip(),
            auth_type=self.auth_type.currentText(),
            password_encrypted=self.password_vault.encrypt_password(self.password.text()),
            private_key_path=self.private_key_path.text(),
            install_dir=self.install_dir.text().strip() or "/opt/minebridge-frp",
            frps_bind_port=self.bind_port.value(),
            dashboard_enabled=self.dashboard_enabled.isChecked(),
            dashboard_port=self.dashboard_port.value(),
        )

    def _save_profile_config(self) -> VpsConfig:
        bundle = self.profile_service.get_active_vps_profile()
        config = self._config_from_ui()
        bundle.config = config.model_copy(update={"id": bundle.config.id})
        self.profile_service.save_vps_profile(bundle)
        return config

    def _manager(self, config: VpsConfig, password: str) -> VpsManager:
        return VpsManager(
            config,
            password=password,
            frp_storage_dir=self.context.data_dir / "frp",
        )

    def _run_vps_action(self, title: str, method_name: str) -> None:
        try:
            config = self._save_profile_config()
            password = self.password.text()
        except (ConfigurationError, ValueError) as exc:
            self._on_action_failed(str(exc))
            return

        self._append_log(f"{title}...")

        def action() -> str:
            manager = self._manager(config, password)
            try:
                method = getattr(manager, method_name)
                result = method()
                return getattr(result, "stdout", "") or f"{title}: OK"
            finally:
                manager.close()

        self._start_thread(action, lambda output: self._on_action_done(title, output))

    def _check_ssh(self) -> None:
        try:
            config = self._save_profile_config()
            password = self.password.text()
        except (ConfigurationError, ValueError) as exc:
            self._on_action_failed(str(exc))
            return

        self._append_log("Проверка SSH...")

        def action() -> str:
            manager = self._manager(config, password)
            try:
                return manager.check_ssh().stdout.strip()
            finally:
                manager.close()

        self._start_thread(action, lambda output: self._on_action_done("SSH", output))

    def _install_frp(self) -> None:
        try:
            self._save_profile_config()
            token = self.profile_service.get_active_tunnel_profile().config.frp_token
            if not token:
                raise ConfigurationError("Сначала сгенерируйте FRP token во вкладке frpc.")
            config = self.profile_service.get_active_vps_profile().config
            password = self.password.text()
        except (ConfigurationError, ValueError) as exc:
            self._on_action_failed(str(exc))
            return

        self._append_log("Установка FRP на VPS...")

        def action() -> str:
            manager = self._manager(config, password)
            try:
                manager.install_frps_on_vps(token)
                return "FRP установлен, systemd-сервис перезапущен."
            finally:
                manager.close()

        self._start_thread(action, lambda output: self._on_action_done("Установка FRP", output))

    def _create_frps_toml(self) -> None:
        try:
            self._save_profile_config()
            token = self.profile_service.get_active_tunnel_profile().config.frp_token
            if not token:
                raise ConfigurationError("Сначала сгенерируйте FRP token во вкладке frpc.")
            config = self.profile_service.get_active_vps_profile().config
            password = self.password.text()
        except (ConfigurationError, ValueError) as exc:
            self._on_action_failed(str(exc))
            return

        self._append_log("Создание frps.toml...")

        def action() -> str:
            manager = self._manager(config, password)
            try:
                return manager.create_frps_config(token)
            finally:
                manager.close()

        self._start_thread(action, lambda output: self._on_action_done("frps.toml", output))

    def _install_systemd(self) -> None:
        self._run_vps_action("Установка systemd-сервиса", "install_systemd_service")

    def _status_frps(self) -> None:
        self._run_vps_action("Статус frps", "status_frps")

    def _open_firewall(self) -> None:
        try:
            config = self._save_profile_config()
            password = self.password.text()
            port = self.bind_port.value()
        except (ConfigurationError, ValueError) as exc:
            self._on_action_failed(str(exc))
            return

        self._append_log("Открытие firewall порта...")

        def action() -> str:
            manager = self._manager(config, password)
            try:
                return manager.open_firewall_port(port)
            finally:
                manager.close()

        self._start_thread(action, lambda output: self._on_action_done("Firewall", output))

    def _save_clicked(self) -> None:
        try:
            self._save_profile_config()
        except (ConfigurationError, ValueError) as exc:
            self._on_action_failed(str(exc))
            return
        self._append_log("Настройки VPS сохранены.")
        QMessageBox.information(self, "VPS", "Настройки VPS сохранены.")

    def _connect_autosave(self) -> None:
        self.profile_select.currentIndexChanged.connect(self._profile_selected)
        self.host.editingFinished.connect(self._autosave)
        self.username.editingFinished.connect(self._autosave)
        self.auth_type.currentTextChanged.connect(self._autosave)
        self.auth_type.currentTextChanged.connect(self._update_auth_fields)
        self.password.editingFinished.connect(self._autosave)
        self.private_key_path.input.editingFinished.connect(self._autosave)
        self.install_dir.editingFinished.connect(self._autosave)
        self.ssh_port.valueChanged.connect(self._autosave)
        self.bind_port.valueChanged.connect(self._autosave)
        self.dashboard_enabled.toggled.connect(self._autosave)
        self.dashboard_port.valueChanged.connect(self._autosave)

    def _profile_selected(self, *_args: object) -> None:
        if self._profile_loading:
            return
        profile_id = self.profile_select.currentData()
        if profile_id is None:
            return
        try:
            self._save_profile_config()
            self.profile_service.set_active_vps_profile(int(profile_id))
        except (ConfigurationError, ValueError) as exc:
            self._on_action_failed(str(exc))
            self.reload_active_profile()
            return
        self.reload_active_profile()
        self._show_status(f"Профиль выбран: {self.profile_select.currentText()}")
        self.profile_changed.emit()

    def _create_profile(self) -> None:
        name, accepted = QInputDialog.getText(self, "Новый профиль", "Название профиля:")
        if not accepted:
            return
        try:
            bundle = self.profile_service.create_vps_profile(name)
            if bundle.profile.id is None:
                raise ConfigurationError("Не удалось получить id нового профиля.")
            self.profile_service.set_active_vps_profile(bundle.profile.id)
        except (ConfigurationError, ValueError) as exc:
            self._on_action_failed(str(exc))
            return
        self.reload_active_profile()
        self._show_status(f"Создан профиль: {bundle.profile.name}")
        self.profile_changed.emit()

    def _rename_profile(self) -> None:
        profile_id = self.profile_select.currentData()
        if profile_id is None:
            return
        name, accepted = QInputDialog.getText(
            self,
            "Переименовать профиль",
            "Новое название:",
            text=self.profile_select.currentText(),
        )
        if not accepted:
            return
        try:
            self.profile_service.rename_vps_profile(int(profile_id), name)
        except ConfigurationError as exc:
            self._on_action_failed(str(exc))
            return
        self.reload_active_profile()
        self.profile_changed.emit()

    def _delete_profile(self) -> None:
        profile_id = self.profile_select.currentData()
        if profile_id is None:
            return
        answer = QMessageBox.question(
            self,
            "Удалить профиль",
            f"Удалить VPS-профиль «{self.profile_select.currentText()}»?",
        )
        if answer != QMessageBox.Yes:
            return
        try:
            self.profile_service.delete_vps_profile(int(profile_id))
        except ConfigurationError as exc:
            self._on_action_failed(str(exc))
            return
        self.reload_active_profile()
        self.profile_changed.emit()

    def _autosave(self, *_args: object) -> None:
        if not self._autosave_enabled:
            return
        try:
            self._save_profile_config()
        except (ConfigurationError, ValueError) as exc:
            self._append_log(f"Не удалось сохранить настройки VPS: {exc}")

    def _update_auth_fields(self, *_args: object) -> None:
        use_private_key = self.auth_type.currentText() == "private_key"
        self._set_form_row_visible(self.password, not use_private_key)
        self._set_form_row_visible(self.private_key_path, use_private_key)

    def _set_form_row_visible(self, field: QWidget, visible: bool) -> None:
        parent = field.parentWidget()
        form = parent.layout() if parent else None
        if isinstance(form, QFormLayout):
            label = form.labelForField(field)
            if label is not None:
                label.setVisible(visible)
        field.setVisible(visible)

    def _start_thread(self, function, on_finished) -> None:
        thread = run_in_thread(function, on_finished, self._on_action_failed)
        self._threads.append(thread)
        thread.finished.connect(
            lambda: self._threads.remove(thread) if thread in self._threads else None
        )

    def _on_action_done(self, title: str, output: object) -> None:
        text = str(output).strip() or "OK"
        self._append_log(text)
        self._show_status(f"{title}: OK")

    def _on_action_failed(self, message: str) -> None:
        self._append_log(message)
        QMessageBox.warning(self, "VPS", message)

    def _append_log(self, line: str) -> None:
        self.log_viewer.append_line(line)

    def _load_saved_password(self, config: VpsConfig) -> None:
        try:
            self.password.setText(self.password_vault.decrypt_password(config.password_encrypted))
        except ConfigurationError as exc:
            self.password.clear()
            self._append_log(str(exc))

    def _show_status(self, message: str) -> None:
        window = self.window()
        if hasattr(window, "statusBar"):
            window.statusBar().showMessage(message, 5000)
