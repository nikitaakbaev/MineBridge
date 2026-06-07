"""FRP tunnel tab."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
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
from minebridge_frp.app.core.exceptions import ConfigurationError, ServiceError
from minebridge_frp.app.models.tunnel import TunnelConfig
from minebridge_frp.app.services.download_service import DownloadService
from minebridge_frp.app.services.frp_manager import FrpManager
from minebridge_frp.app.services.profile_service import ProfileService
from minebridge_frp.app.ui.layouts import FlowLayout, prepare_action_button, scroll_panel
from minebridge_frp.app.ui.widgets.log_viewer import LogViewer
from minebridge_frp.app.ui.workers import run_in_thread


class FrpcTab(QWidget):
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
        self._profile_loading = False

        self.profile_select = QComboBox()
        self.profile_select.setMinimumWidth(260)
        self.new_profile_button = QPushButton("Новый профиль")
        self.rename_profile_button = QPushButton("Переименовать")
        self.delete_profile_button = QPushButton("Удалить")
        self.profile_name = QLineEdit("default")
        self.profile_name.setReadOnly(True)
        self.frpc_folder = QLineEdit()
        self.frpc_folder.setReadOnly(True)
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

        profile_group = QGroupBox("Профиль")
        profile_layout = QVBoxLayout(profile_group)
        profile_layout.addWidget(self.profile_select, 1)
        profile_actions = QWidget()
        profile_actions_layout = FlowLayout(profile_actions, margin=0, spacing=8)
        for button in (
            self.new_profile_button,
            self.rename_profile_button,
            self.delete_profile_button,
        ):
            profile_actions_layout.addWidget(prepare_action_button(button))
        profile_layout.addWidget(profile_actions)

        settings_group = QGroupBox("Локальный frpc")
        form = QFormLayout(settings_group)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.addRow("Профиль", self.profile_name)
        form.addRow("Рабочая папка frpc", self.frpc_folder)
        form.addRow("Локальный IP Minecraft", self.local_ip)
        form.addRow("Локальный порт Minecraft", self.local_port)
        form.addRow("Публичный порт на VPS", self.remote_port)
        form.addRow("Protocol", self.protocol)
        form.addRow("Адрес VPS / frps", self.server_addr)
        form.addRow("Порт frps на VPS", self.server_port)
        form.addRow("FRP token", self.token)
        form.addRow("Автозапуск frpc вместе с Minecraft", self.auto_start_frpc)

        actions = QGroupBox("Действия frpc")
        actions_layout = FlowLayout(actions, margin=2, spacing=8)
        buttons = [
            ("Сохранить настройки", self._save_clicked),
            ("Сгенерировать токен", self._generate_token),
            ("Создать frpc.toml", self._create_frpc_config),
            ("Скачать frpc локально", self._download_frpc),
            ("Запустить frpc локально", self._start_frpc),
            ("Остановить frpc", self._stop_frpc),
            ("Проверить внешний порт", self._check_external_port),
            ("Открыть рабочую папку", self._open_frpc_folder),
        ]
        for label, callback in buttons:
            button = prepare_action_button(QPushButton(label))
            button.clicked.connect(callback)
            actions_layout.addWidget(button)

        self.log_viewer = LogViewer("Логи локального frpc")
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
        splitter.setSizes([430, 260])

        layout = QVBoxLayout(self)
        layout.addWidget(splitter)

        self.reload_active_profile()
        self.profile_select.currentIndexChanged.connect(self._profile_selected)
        self.new_profile_button.clicked.connect(self._create_profile)
        self.rename_profile_button.clicked.connect(self._rename_profile)
        self.delete_profile_button.clicked.connect(self._delete_profile)

    def reload_active_profile(self) -> None:
        self._profile_loading = True
        try:
            self._load_profile_options()
            self._load_active_profile()
        finally:
            self._profile_loading = False

    def _load_profile_options(self) -> None:
        active_id = self.profile_service.get_active_tunnel_profile().profile.id
        self.profile_select.blockSignals(True)
        self.profile_select.clear()
        for profile in self.profile_service.list_tunnel_profiles():
            self.profile_select.addItem(profile.name, profile.id)
            if profile.id == active_id:
                self.profile_select.setCurrentIndex(self.profile_select.count() - 1)
        self.profile_select.blockSignals(False)

    def _profile_selected(self, *_args: object) -> None:
        if self._profile_loading:
            return
        profile_id = self.profile_select.currentData()
        if profile_id is None:
            return
        try:
            self._save_profile_config()
            self.profile_service.set_active_tunnel_profile(int(profile_id))
        except (ConfigurationError, ValueError) as exc:
            QMessageBox.warning(self, "frpc", str(exc))
            self.reload_active_profile()
            return
        self.reload_active_profile()

    def _create_profile(self) -> None:
        name, accepted = QInputDialog.getText(self, "Новый профиль", "Название профиля:")
        if not accepted:
            return
        try:
            bundle = self.profile_service.create_tunnel_profile(name)
            if bundle.profile.id is None:
                raise ConfigurationError("Не удалось получить id нового профиля.")
            self.profile_service.set_active_tunnel_profile(bundle.profile.id)
        except (ConfigurationError, ValueError) as exc:
            QMessageBox.warning(self, "frpc", str(exc))
            return
        self.reload_active_profile()
        self._append_log(f"Создан frpc-профиль: {bundle.profile.name}")

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
            self.profile_service.rename_tunnel_profile(int(profile_id), name)
        except ConfigurationError as exc:
            QMessageBox.warning(self, "frpc", str(exc))
            return
        self.reload_active_profile()
        self._append_log(f"frpc-профиль переименован: {name.strip()}")

    def _delete_profile(self) -> None:
        profile_id = self.profile_select.currentData()
        if profile_id is None:
            return
        answer = QMessageBox.question(
            self,
            "Удалить профиль",
            f"Удалить frpc-профиль «{self.profile_select.currentText()}»?",
        )
        if answer != QMessageBox.Yes:
            return
        try:
            self.profile_service.delete_tunnel_profile(int(profile_id))
        except ConfigurationError as exc:
            QMessageBox.warning(self, "frpc", str(exc))
            return
        self.reload_active_profile()
        self._append_log("frpc-профиль удалён.")

    def _load_active_profile(self) -> None:
        bundle = self.profile_service.get_active_tunnel_profile()
        config = bundle.config
        self.profile_name.setText(bundle.profile.name)
        self.frpc_folder.setText(str(self._profile_frpc_dir(bundle.profile.name)))
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
        bundle = self.profile_service.get_active_tunnel_profile()
        config = self._config_from_ui()
        bundle.config = config.model_copy(update={"id": bundle.config.id})
        self.profile_service.save_tunnel_profile(bundle)
        return config

    def _generate_token(self) -> None:
        token = self.manager.generate_token()
        self.token.setText(token)
        self._save_profile_config()
        self._append_log("Новый FRP token сгенерирован и сохранён.")

    def _save_clicked(self) -> None:
        try:
            self._save_profile_config()
        except (ConfigurationError, ValueError) as exc:
            QMessageBox.warning(self, "frpc", str(exc))
            return
        self._append_log("Настройки туннеля сохранены.")
        QMessageBox.information(self, "frpc", "Настройки frpc сохранены.")

    def _create_frpc_config(self) -> Path | None:
        try:
            config = self._save_profile_config()
            path = self.manager.write_frpc_config(
                config,
                self.profile_name.text().strip() or "default",
            )
            self._append_log(f"frpc.toml создан: {path}")
            self.frpc_folder.setText(str(path.parent))
            QMessageBox.information(self, "frpc", f"frpc.toml создан:\n{path}")
            return path
        except (ConfigurationError, ValueError, OSError) as exc:
            QMessageBox.warning(self, "frpc", str(exc))
            return None

    def _download_frpc(self) -> None:
        self._append_log("Скачивание FRP latest release...")
        storage_dir = self.context.data_dir / "frp"
        thread = run_in_thread(
            lambda: self._download_frpc_in_background(storage_dir),
            self._on_download_finished,
            self._show_error,
        )
        self._threads.append(thread)
        thread.finished.connect(
            lambda: self._threads.remove(thread) if thread in self._threads else None
        )

    def _download_frpc_in_background(self, storage_dir: Path) -> Path:
        extracted = DownloadService(storage_dir).download_frp()
        binary = FrpManager(storage_dir).find_frpc_binary(extracted)
        if binary is None:
            raise ServiceError("После распаковки FRP бинарник frpc не найден.")
        return binary

    def _on_download_finished(self, binary_path: object) -> None:
        self._append_log(f"frpc готов: {binary_path}")
        QMessageBox.information(self, "frpc", f"frpc скачан:\n{binary_path}")

    def _start_frpc(self) -> None:
        try:
            config_path = self._create_frpc_config()
            if config_path is None:
                return
            self.manager.start_frpc(config_path)
            self._append_log("frpc запускается...")
        except (ConfigurationError, ServiceError) as exc:
            QMessageBox.warning(self, "frpc", str(exc))

    def _stop_frpc(self) -> None:
        self.manager.stop_frpc()
        self._append_log("Остановка frpc запрошена.")

    def _check_external_port(self) -> None:
        host = self.server_addr.text().strip()
        port = self.remote_port.value()
        if not host:
            QMessageBox.warning(self, "frpc", "Укажите адрес VPS / frps.")
            return

        self._append_log(f"Проверка внешнего порта {host}:{port}...")
        thread = run_in_thread(
            lambda: self.manager.check_external_port(host, port),
            lambda result: self._on_port_check_finished(host, port, bool(result)),
            self._show_error,
        )
        self._threads.append(thread)
        thread.finished.connect(
            lambda: self._threads.remove(thread) if thread in self._threads else None
        )

    def _on_port_check_finished(self, host: str, port: int, is_open: bool) -> None:
        status = "открыт" if is_open else "не отвечает"
        self._append_log(f"Внешний порт {host}:{port} {status}.")
        QMessageBox.information(self, "frpc", f"{host}:{port} {status}.")

    def _on_status_changed(self, status: str) -> None:
        self._append_log(f"Статус frpc: {status}")

    def _append_log(self, line: str) -> None:
        self.log_viewer.append_line(line)

    def _show_error(self, message: str) -> None:
        self._append_log(message)
        QMessageBox.warning(self, "frpc", message)

    def _open_frpc_folder(self) -> None:
        path = Path(self.frpc_folder.text() or self._profile_frpc_dir(self.profile_name.text()))
        path.mkdir(parents=True, exist_ok=True)
        self.frpc_folder.setText(str(path))
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _profile_frpc_dir(self, profile_name: str) -> Path:
        return self.context.data_dir / "frp" / "profiles" / (profile_name.strip() or "default")


TunnelTab = FrpcTab
