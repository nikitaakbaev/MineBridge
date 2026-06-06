"""FRP tunnel tab."""

from __future__ import annotations

from pathlib import Path

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
from minebridge_frp.app.core.exceptions import ConfigurationError, ServiceError
from minebridge_frp.app.models.tunnel import TunnelConfig
from minebridge_frp.app.services.frp_manager import FrpManager
from minebridge_frp.app.services.profile_service import ProfileService
from minebridge_frp.app.ui.widgets.log_viewer import LogViewer
from minebridge_frp.app.ui.workers import run_in_thread


class TunnelTab(QWidget):
    """Local frpc configuration and controls."""

    def __init__(self, context: AppContext, profile_service: ProfileService) -> None:
        super().__init__()
        self.context = context
        self.profile_service = profile_service
        self.manager = FrpManager(context.data_dir / "frp")
        self.manager.log_line.connect(self._append_log)
        self.manager.status_changed.connect(self._on_status_changed)
        self.manager.error.connect(self._show_error)
        self._threads = []

        self.profile_name = QLineEdit("default")
        self.local_ip = QLineEdit("127.0.0.1")

        self.local_port = QSpinBox()
        self.local_port.setRange(1, 65535)
        self.local_port.setValue(25565)

        self.remote_port = QSpinBox()
        self.remote_port.setRange(1, 65535)
        self.remote_port.setValue(25565)

        self.server_port = QSpinBox()
        self.server_port.setRange(1, 65535)
        self.server_port.setValue(7000)

        self.protocol = QComboBox()
        self.protocol.addItem("tcp")

        self.server_addr = QLineEdit()
        self.token = QLineEdit()
        self.token.setEchoMode(QLineEdit.Password)
        self.auto_start_frpc = QCheckBox()
        self.auto_start_frpc.setChecked(True)

        form = QFormLayout()
        form.addRow("Profile name", self.profile_name)
        form.addRow("Local IP", self.local_ip)
        form.addRow("Local port", self.local_port)
        form.addRow("Remote port", self.remote_port)
        form.addRow("Protocol", self.protocol)
        form.addRow("FRP server address", self.server_addr)
        form.addRow("FRP server bind port", self.server_port)
        form.addRow("Auth token", self.token)
        form.addRow("Auto-start frpc with Minecraft", self.auto_start_frpc)

        actions = QGroupBox("Действия туннеля")
        grid = QGridLayout(actions)
        buttons = [
            ("Сгенерировать токен", self._generate_token),
            ("Создать frpc.toml", self._create_frpc_config),
            ("Скачать frpc", self._download_frpc),
            ("Запустить frpc", self._start_frpc),
            ("Остановить frpc", self._stop_frpc),
            ("Проверить внешний порт", self._check_external_port),
        ]
        for index, (label, callback) in enumerate(buttons):
            button = QPushButton(label)
            button.clicked.connect(callback)
            grid.addWidget(button, index // 3, index % 3)

        self.log_viewer = LogViewer("frpc logs")

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(actions)
        layout.addWidget(self.log_viewer)

        self._load_active_profile()

    def _load_active_profile(self) -> None:
        bundle = self.profile_service.get_active_profile()
        config = bundle.tunnel
        self.profile_name.setText(bundle.profile.name)
        self.local_ip.setText(config.local_ip)
        self.local_port.setValue(config.local_port)
        self.remote_port.setValue(config.remote_port)
        self.protocol.setCurrentText(config.protocol)
        self.server_addr.setText(config.frp_server_addr)
        self.server_port.setValue(config.frp_server_bind_port)
        self.token.setText(config.frp_token)
        self.auto_start_frpc.setChecked(config.auto_start_frpc)

    def _config_from_ui(self) -> TunnelConfig:
        return TunnelConfig(
            local_ip=self.local_ip.text().strip() or "127.0.0.1",
            local_port=self.local_port.value(),
            remote_port=self.remote_port.value(),
            protocol=self.protocol.currentText(),
            frp_server_addr=self.server_addr.text().strip(),
            frp_server_bind_port=self.server_port.value(),
            frp_token=self.token.text().strip(),
            auto_start_frpc=self.auto_start_frpc.isChecked(),
        )

    def _save_profile_config(self) -> TunnelConfig:
        bundle = self.profile_service.get_active_profile()
        config = self._config_from_ui()
        bundle.tunnel = config.model_copy(
            update={"id": bundle.tunnel.id, "profile_id": bundle.profile.id}
        )
        self.profile_service.save_profile(bundle)
        return config

    def _generate_token(self) -> None:
        token = self.manager.generate_token()
        self.token.setText(token)
        self._append_log("Новый FRP token сгенерирован.")

    def _create_frpc_config(self) -> Path | None:
        try:
            config = self._save_profile_config()
            path = self.manager.write_frpc_config(
                config,
                self.profile_name.text().strip() or "default",
            )
            self._append_log(f"frpc.toml создан: {path}")
            QMessageBox.information(self, "Туннель", f"frpc.toml создан:\n{path}")
            return path
        except (ConfigurationError, ValueError, OSError) as exc:
            QMessageBox.warning(self, "Туннель", str(exc))
            return None

    def _download_frpc(self) -> None:
        self._append_log("Скачивание FRP latest release...")
        thread = run_in_thread(
            lambda: self.manager.download_frpc(),
            self._on_download_finished,
            self._show_error,
        )
        self._threads.append(thread)

    def _on_download_finished(self, binary_path: object) -> None:
        self._append_log(f"frpc готов: {binary_path}")
        QMessageBox.information(self, "Туннель", f"frpc скачан:\n{binary_path}")

    def _start_frpc(self) -> None:
        try:
            config_path = self._create_frpc_config()
            if config_path is None:
                return
            self.manager.start_frpc(config_path)
            self._append_log("frpc запускается...")
        except (ConfigurationError, ServiceError) as exc:
            QMessageBox.warning(self, "Туннель", str(exc))

    def _stop_frpc(self) -> None:
        self.manager.stop_frpc()
        self._append_log("Остановка frpc запрошена.")

    def _check_external_port(self) -> None:
        host = self.server_addr.text().strip()
        port = self.remote_port.value()
        if not host:
            QMessageBox.warning(self, "Туннель", "Укажите FRP server address.")
            return

        self._append_log(f"Проверка внешнего порта {host}:{port}...")
        thread = run_in_thread(
            lambda: self.manager.check_external_port(host, port),
            lambda result: self._on_port_check_finished(host, port, bool(result)),
            self._show_error,
        )
        self._threads.append(thread)

    def _on_port_check_finished(self, host: str, port: int, is_open: bool) -> None:
        status = "открыт" if is_open else "не отвечает"
        self._append_log(f"Внешний порт {host}:{port} {status}.")
        QMessageBox.information(self, "Туннель", f"{host}:{port} {status}.")

    def _on_status_changed(self, status: str) -> None:
        self._append_log(f"Статус frpc: {status}")

    def _append_log(self, line: str) -> None:
        self.log_viewer.append_line(line)

    def _show_error(self, message: str) -> None:
        self._append_log(message)
        QMessageBox.warning(self, "Туннель", message)
