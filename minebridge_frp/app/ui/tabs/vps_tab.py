"""VPS configuration tab."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from minebridge_frp.app.core.app_context import AppContext
from minebridge_frp.app.core.exceptions import ConfigurationError
from minebridge_frp.app.models.vps import VpsConfig
from minebridge_frp.app.services.profile_service import ProfileService
from minebridge_frp.app.services.vps_manager import VpsManager
from minebridge_frp.app.ui.widgets.log_viewer import LogViewer
from minebridge_frp.app.ui.widgets.path_picker import PathPicker
from minebridge_frp.app.ui.workers import run_in_thread


class VpsTab(QWidget):
    """VPS SSH and remote FRP controls."""

    def __init__(self, context: AppContext, profile_service: ProfileService) -> None:
        super().__init__()
        self.context = context
        self.profile_service = profile_service
        self._threads = []

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

        form = QFormLayout()
        form.addRow("VPS IP / host", self.host)
        form.addRow("SSH port", self.ssh_port)
        form.addRow("SSH username", self.username)
        form.addRow("Auth type", self.auth_type)
        form.addRow("Password", self.password)
        form.addRow("Private key path", self.private_key_path)
        form.addRow("Remote install dir", self.install_dir)
        form.addRow("frps bind port", self.bind_port)
        form.addRow("Dashboard enabled", self.dashboard_enabled)
        form.addRow("Dashboard port", self.dashboard_port)

        actions = QGroupBox("Действия VPS")
        grid = QGridLayout(actions)
        buttons = [
            ("Проверить SSH", self._check_ssh),
            ("Установить FRP на VPS", self._install_frp),
            ("Обновить FRP на VPS", self._install_frp),
            ("Создать frps.toml", self._create_frps_toml),
            ("Установить systemd-сервис", self._install_systemd),
            ("Запустить frps", lambda: self._run_vps_action("Запуск frps", "start_frps")),
            ("Остановить frps", lambda: self._run_vps_action("Остановка frps", "stop_frps")),
            ("Перезапустить frps", lambda: self._run_vps_action("Рестарт frps", "restart_frps")),
            ("Проверить статус frps", self._status_frps),
            ("Открыть порт в firewall", self._open_firewall),
        ]
        for index, (label, callback) in enumerate(buttons):
            button = QPushButton(label)
            button.clicked.connect(callback)
            grid.addWidget(button, index // 2, index % 2)

        self.log_viewer = LogViewer("VPS logs")

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(actions)
        layout.addWidget(self.log_viewer)

        self._load_active_profile()

    def _load_active_profile(self) -> None:
        config = self.profile_service.get_active_profile().vps
        self.host.setText(config.host)
        self.ssh_port.setValue(config.ssh_port)
        self.username.setText(config.username)
        self.auth_type.setCurrentText(config.auth_type)
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
            private_key_path=self.private_key_path.text(),
            install_dir=self.install_dir.text().strip() or "/opt/minebridge-frp",
            frps_bind_port=self.bind_port.value(),
            dashboard_enabled=self.dashboard_enabled.isChecked(),
            dashboard_port=self.dashboard_port.value(),
        )

    def _save_profile_config(self) -> VpsConfig:
        bundle = self.profile_service.get_active_profile()
        config = self._config_from_ui()
        bundle.vps = config.model_copy(
            update={"id": bundle.vps.id, "profile_id": bundle.profile.id}
        )
        self.profile_service.save_profile(bundle)
        return config

    def _manager(self) -> VpsManager:
        return VpsManager(
            self._save_profile_config(),
            password=self.password.text(),
            frp_storage_dir=self.context.data_dir / "frp",
        )

    def _run_vps_action(self, title: str, method_name: str) -> None:
        self._append_log(f"{title}...")

        def action() -> str:
            manager = self._manager()
            try:
                method = getattr(manager, method_name)
                result = method()
                return getattr(result, "stdout", "") or f"{title}: OK"
            finally:
                manager.close()

        self._start_thread(action, lambda output: self._on_action_done(title, output))

    def _check_ssh(self) -> None:
        self._append_log("Проверка SSH...")

        def action() -> str:
            manager = self._manager()
            try:
                return manager.check_ssh().stdout.strip()
            finally:
                manager.close()

        self._start_thread(action, lambda output: self._on_action_done("SSH", output))

    def _install_frp(self) -> None:
        self._append_log("Установка FRP на VPS...")

        def action() -> str:
            bundle = self.profile_service.get_active_profile()
            token = bundle.tunnel.frp_token
            if not token:
                raise ConfigurationError("Сначала сгенерируйте FRP token во вкладке Туннель.")
            manager = self._manager()
            try:
                manager.install_frps_on_vps(token)
                return "FRP установлен, systemd-сервис перезапущен."
            finally:
                manager.close()

        self._start_thread(action, lambda output: self._on_action_done("Установка FRP", output))

    def _create_frps_toml(self) -> None:
        self._append_log("Создание frps.toml...")

        def action() -> str:
            bundle = self.profile_service.get_active_profile()
            token = bundle.tunnel.frp_token
            if not token:
                raise ConfigurationError("Сначала сгенерируйте FRP token во вкладке Туннель.")
            manager = self._manager()
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
        self._append_log("Открытие firewall порта...")

        def action() -> str:
            manager = self._manager()
            try:
                return manager.open_firewall_port(self.bind_port.value())
            finally:
                manager.close()

        self._start_thread(action, lambda output: self._on_action_done("Firewall", output))

    def _start_thread(self, function, on_finished) -> None:
        thread = run_in_thread(function, on_finished, self._on_action_failed)
        self._threads.append(thread)

    def _on_action_done(self, title: str, output: object) -> None:
        text = str(output).strip() or "OK"
        self._append_log(text)
        QMessageBox.information(self, "VPS", f"{title}: OK")

    def _on_action_failed(self, message: str) -> None:
        self._append_log(message)
        QMessageBox.warning(self, "VPS", message)

    def _append_log(self, line: str) -> None:
        self.log_viewer.append_line(line)
