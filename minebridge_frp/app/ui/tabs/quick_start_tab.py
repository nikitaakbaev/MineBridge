"""Quick start tab."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer
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

from minebridge_frp.app.core.app_context import AppContext
from minebridge_frp.app.core.exceptions import ConfigurationError
from minebridge_frp.app.models.profile import ProfileBundle
from minebridge_frp.app.services.frp_manager import FrpManager
from minebridge_frp.app.services.minecraft_manager import MinecraftManager
from minebridge_frp.app.services.profile_service import ProfileService
from minebridge_frp.app.services.vps_manager import VpsManager
from minebridge_frp.app.ui.widgets.status_badge import StatusBadge
from minebridge_frp.app.ui.workers import run_in_thread
from minebridge_frp.app.utils.ports import is_local_port_listening


class QuickStartTab(QWidget):
    """Primary tab for the normal one-button user workflow."""

    def __init__(self, context: AppContext, profile_service: ProfileService) -> None:
        super().__init__()
        self.context = context
        self.profile_service = profile_service
        self._loading_profiles = False
        self._threads = []
        self._quick_password = ""
        self.minecraft_manager = MinecraftManager()
        self.frp_manager = FrpManager(context.data_dir / "frp")
        self.minecraft_manager.log_line.connect(lambda line: self._append_checklist(f"MC: {line}"))
        self.frp_manager.log_line.connect(lambda line: self._append_checklist(f"frpc: {line}"))

        self.profile_select = QComboBox()
        self.profile_select.currentIndexChanged.connect(self._activate_selected_profile)

        self.address = QLineEdit()
        self.address.setPlaceholderText("Адрес появится после запуска туннеля")
        self.address.setReadOnly(True)
        self.vps_status = StatusBadge("Не проверен", "warning")
        self.frps_status = StatusBadge("Не запущен", "warning")
        self.minecraft_status = StatusBadge("Остановлен", "warning")
        self.frpc_status = StatusBadge("Остановлен", "warning")

        form = QFormLayout()
        form.addRow("Профиль", self.profile_select)
        form.addRow("VPS", self.vps_status)
        form.addRow("frps", self.frps_status)
        form.addRow("Minecraft-сервер", self.minecraft_status)
        form.addRow("frpc", self.frpc_status)
        form.addRow("Адрес для друзей", self.address)

        create_profile_button = QPushButton("Создать профиль")
        export_profile_button = QPushButton("Экспорт JSON")
        import_profile_button = QPushButton("Импорт JSON")

        profile_buttons = QHBoxLayout()
        profile_buttons.addWidget(create_profile_button)
        profile_buttons.addWidget(export_profile_button)
        profile_buttons.addWidget(import_profile_button)
        profile_buttons.addStretch(1)

        self.start_button = QPushButton("Запустить сервер и открыть доступ")
        self.start_button.setMinimumHeight(44)
        self.stop_button = QPushButton("Остановить всё")

        buttons = QHBoxLayout()
        buttons.addWidget(self.start_button)
        buttons.addWidget(self.stop_button)

        self.checklist = QLabel("Чеклист ошибок появится после диагностики профиля.")
        self.checklist.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(profile_buttons)
        layout.addLayout(buttons)
        layout.addWidget(self.checklist)
        layout.addStretch(1)

        create_profile_button.clicked.connect(self._create_profile)
        export_profile_button.clicked.connect(self._export_profile)
        import_profile_button.clicked.connect(self._import_profile)
        self.start_button.clicked.connect(self._start_all)
        self.stop_button.clicked.connect(self._stop_all)
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

    def _start_all(self) -> None:
        try:
            bundle = self.profile_service.get_active_profile()
            self._validate_profile(bundle)
            self._reset_run_state()
            self._append_checklist("Профиль проверен.")
            self.minecraft_manager.check_java_version(bundle.minecraft.java_path or None)
            self._append_checklist("Java проверена.")
            if is_local_port_listening(bundle.minecraft.mc_port):
                raise ConfigurationError(
                    f"Локальный порт Minecraft {bundle.minecraft.mc_port} уже занят."
                )
        except ConfigurationError as exc:
            self._append_checklist(str(exc))
            QMessageBox.warning(self, "Быстрый запуск", str(exc))
            return

        self.start_button.setEnabled(False)
        self.vps_status.set_status("Проверяется", "warning")
        if bundle.vps.auth_type == "password":
            password, ok = QInputDialog.getText(
                self,
                "SSH password",
                "Пароль SSH для VPS:",
                QLineEdit.Password,
            )
            if not ok:
                self.start_button.setEnabled(True)
                return
            self._quick_password = password
        self._check_vps_then_start_local(bundle)

    def _check_vps_then_start_local(self, bundle: ProfileBundle) -> None:
        def action() -> str:
            manager = VpsManager(
                bundle.vps,
                password=self._quick_password,
                frp_storage_dir=self.context.data_dir / "frp",
            )
            try:
                manager.check_ssh()
                status = manager.status_frps()
                if status.ok and "active" in status.stdout:
                    return "frps active"
                manager.start_frps()
                return "frps started"
            finally:
                manager.close()

        thread = run_in_thread(
            action,
            lambda output: self._on_vps_ready(bundle, str(output)),
            self._on_quick_start_failed,
        )
        self._threads.append(thread)

    def _on_vps_ready(self, bundle: ProfileBundle, output: str) -> None:
        self.vps_status.set_status("OK", "ok")
        self.frps_status.set_status("Запущен", "ok")
        self._append_checklist(f"VPS/frps: {output}")
        self._start_minecraft(bundle)

    def _start_minecraft(self, bundle: ProfileBundle) -> None:
        try:
            if not self.minecraft_manager.check_eula(Path(bundle.minecraft.server_dir)):
                raise ConfigurationError(
                    "EULA Minecraft не принята. Откройте вкладку Minecraft и подтвердите EULA."
                )
            self.minecraft_manager.start_server(bundle.minecraft)
            self.minecraft_status.set_status("Запускается", "warning")
            self._append_checklist("Minecraft-сервер запускается.")
            self._poll_minecraft_port(bundle, attempts_left=120)
        except (ConfigurationError, Exception) as exc:  # noqa: BLE001
            self._on_quick_start_failed(str(exc))

    def _poll_minecraft_port(self, bundle: ProfileBundle, attempts_left: int) -> None:
        if is_local_port_listening(bundle.minecraft.mc_port):
            self.minecraft_status.set_status("Запущен", "ok")
            self._append_checklist("Локальный порт Minecraft слушает.")
            self._start_frpc(bundle)
            return
        if attempts_left <= 0:
            self._on_quick_start_failed("Minecraft не открыл локальный порт за 30 секунд.")
            return
        QTimer.singleShot(250, lambda: self._poll_minecraft_port(bundle, attempts_left - 1))

    def _start_frpc(self, bundle: ProfileBundle) -> None:
        try:
            config_path = self.frp_manager.write_frpc_config(
                bundle.tunnel,
                bundle.profile.name or "default",
            )
            self.frp_manager.start_frpc(config_path)
            self.frpc_status.set_status("Запущен", "ok")
            address = f"{bundle.vps.host}:{bundle.tunnel.remote_port}"
            self.address.setText(address)
            self._append_checklist(f"Адрес для друзей: {address}")
            self.start_button.setEnabled(True)
        except (ConfigurationError, Exception) as exc:  # noqa: BLE001
            self._on_quick_start_failed(str(exc))

    def _stop_all(self) -> None:
        self.frp_manager.stop_frpc()
        self.minecraft_manager.stop_server_gracefully()
        self.frpc_status.set_status("Остановлен", "warning")
        self.minecraft_status.set_status("Остановка", "warning")
        self._append_checklist("Локальные процессы остановлены или завершаются.")

        bundle = self.profile_service.get_active_profile()
        if bundle.vps.host:
            thread = run_in_thread(
                lambda: self._stop_remote_frps(bundle),
                lambda _output: self.frps_status.set_status("Остановлен", "warning"),
                lambda message: self._append_checklist(f"Не удалось остановить frps: {message}"),
            )
            self._threads.append(thread)

    def _stop_remote_frps(self, bundle: ProfileBundle) -> str:
        manager = VpsManager(
            bundle.vps,
            password=self._quick_password,
            frp_storage_dir=self.context.data_dir / "frp",
        )
        try:
            manager.stop_frps()
            return "frps stopped"
        finally:
            manager.close()

    def _validate_profile(self, bundle: ProfileBundle) -> None:
        if not bundle.vps.host:
            raise ConfigurationError("В профиле не указан VPS host.")
        if not bundle.vps.username:
            raise ConfigurationError("В профиле не указан SSH username.")
        if not bundle.minecraft.server_dir or not bundle.minecraft.jar_path:
            raise ConfigurationError("Выберите папку Minecraft-сервера и server.jar.")
        if not bundle.tunnel.frp_token:
            raise ConfigurationError("Сгенерируйте FRP token во вкладке Туннель.")
        if not bundle.tunnel.frp_server_addr:
            bundle.tunnel.frp_server_addr = bundle.vps.host
            self.profile_service.save_profile(bundle)

    def _reset_run_state(self) -> None:
        self.checklist.setText("")
        self.address.clear()
        self.vps_status.set_status("Не проверен", "warning")
        self.frps_status.set_status("Не запущен", "warning")
        self.minecraft_status.set_status("Остановлен", "warning")
        self.frpc_status.set_status("Остановлен", "warning")

    def _on_quick_start_failed(self, message: str) -> None:
        self.start_button.setEnabled(True)
        self._append_checklist(message)
        QMessageBox.warning(self, "Быстрый запуск", message)

    def _append_checklist(self, line: str) -> None:
        current = self.checklist.text().strip()
        self.checklist.setText(f"{current}\n{line}".strip())

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
