"""Minecraft server tab."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QProcess, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
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

from minebridge_frp.app.core.exceptions import ConfigurationError, ServiceError
from minebridge_frp.app.models.minecraft import MinecraftConfig
from minebridge_frp.app.services.minecraft_manager import MinecraftManager
from minebridge_frp.app.services.profile_service import ProfileService
from minebridge_frp.app.ui.layouts import FlowLayout, prepare_action_button, scroll_panel
from minebridge_frp.app.ui.widgets.console_input import ConsoleInput
from minebridge_frp.app.ui.widgets.log_viewer import LogViewer
from minebridge_frp.app.ui.widgets.path_picker import PathPicker


class MinecraftTab(QWidget):
    """Local Minecraft server controls."""

    profile_changed = Signal()

    def __init__(self, profile_service: ProfileService) -> None:
        super().__init__()
        self.profile_service = profile_service
        self.manager = MinecraftManager()
        self._profile_loading = False
        self.manager.log_line.connect(self._append_log)
        self.manager.status_changed.connect(self._on_status_changed)
        self.manager.error.connect(self._show_error)

        self.profile_select = QComboBox()
        self.profile_select.setMinimumWidth(260)
        self.new_profile_button = QPushButton("Новый профиль")
        self.rename_profile_button = QPushButton("Переименовать")
        self.delete_profile_button = QPushButton("Удалить")

        self.server_dir = PathPicker(file_mode=False)
        self.jar_path = PathPicker(file_mode=True)
        self.java_path = PathPicker(file_mode=True)

        self.port = QSpinBox()
        self.port.setRange(1, 65535)
        self.port.setValue(25565)

        self.max_players = QSpinBox()
        self.max_players.setRange(1, 500)
        self.max_players.setValue(20)

        self.view_distance = QSpinBox()
        self.view_distance.setRange(2, 32)
        self.view_distance.setValue(10)

        self.simulation_distance = QSpinBox()
        self.simulation_distance.setRange(2, 32)
        self.simulation_distance.setValue(10)

        self.server_type = QComboBox()
        self.server_type.addItems(["Vanilla", "Paper", "Fabric", "Forge", "NeoForge"])

        self.difficulty = QComboBox()
        self.difficulty.addItems(["peaceful", "easy", "normal", "hard"])

        self.xms = QLineEdit("2G")
        self.xmx = QLineEdit("4G")
        self.mc_version = QLineEdit()
        self.auto_open_eula = QCheckBox()
        self.accept_eula = QCheckBox()
        self.online_mode = QCheckBox()
        self.online_mode.setChecked(True)
        self.motd = QLineEdit("MineBridge FRP server")

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

        settings_group = QGroupBox("Сервер и запуск")
        form = QFormLayout(settings_group)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.addRow("Папка сервера", self.server_dir)
        form.addRow("server.jar", self.jar_path)
        form.addRow("Java path", self.java_path)
        form.addRow("Xms", self.xms)
        form.addRow("Xmx", self.xmx)
        form.addRow("Minecraft port", self.port)
        form.addRow("Server type", self.server_type)
        form.addRow("Minecraft version", self.mc_version)
        form.addRow("Автоматически открыть eula.txt", self.auto_open_eula)
        form.addRow("Я принимаю EULA Minecraft", self.accept_eula)
        form.addRow("online-mode", self.online_mode)
        form.addRow("difficulty", self.difficulty)
        form.addRow("max-players", self.max_players)
        form.addRow("motd", self.motd)
        form.addRow("view-distance", self.view_distance)
        form.addRow("simulation-distance", self.simulation_distance)

        actions = QGroupBox("Действия Minecraft")
        actions_layout = FlowLayout(actions, margin=2, spacing=8)
        buttons = [
            ("Найти Java", self._find_java),
            ("Проверить Java", self._check_java),
            ("Выбрать папку сервера", self._choose_server_dir),
            ("Найти server.jar", self._find_server_jar),
            ("Открыть eula.txt", self._open_eula),
            ("Сохранить server.properties", self._save_server_properties),
            ("Запустить Minecraft-сервер", self._start_server),
            ("Остановить Minecraft-сервер", self._stop_server),
            ("Перезапустить Minecraft-сервер", self._restart_server),
        ]
        for label, callback in buttons:
            button = prepare_action_button(QPushButton(label))
            button.clicked.connect(callback)
            actions_layout.addWidget(button)

        self.log_viewer = LogViewer("Minecraft logs")
        self.log_viewer.setMinimumHeight(160)
        self.console_input = ConsoleInput()
        self.console_input.command_submitted.connect(self._send_command)

        controls = QWidget()
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(8, 8, 8, 8)
        controls_layout.setSpacing(10)
        controls_layout.addWidget(profile_group)
        controls_layout.addWidget(settings_group)
        controls_layout.addWidget(actions)
        controls_layout.addStretch(1)

        output = QWidget()
        output_layout = QVBoxLayout(output)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.addWidget(self.log_viewer)
        output_layout.addWidget(self.console_input)

        splitter = QSplitter()
        splitter.setOrientation(Qt.Orientation.Vertical)
        splitter.addWidget(scroll_panel(controls))
        splitter.addWidget(output)
        splitter.setChildrenCollapsible(False)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        splitter.setSizes([540, 260])

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
        active_id = self.profile_service.get_active_minecraft_profile().profile.id
        self.profile_select.blockSignals(True)
        self.profile_select.clear()
        for profile in self.profile_service.list_minecraft_profiles():
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
            self.profile_service.set_active_minecraft_profile(int(profile_id))
        except (ConfigurationError, ValueError) as exc:
            QMessageBox.warning(self, "Minecraft", str(exc))
            self.reload_active_profile()
            return
        self.reload_active_profile()
        self.profile_changed.emit()

    def _create_profile(self) -> None:
        name, accepted = QInputDialog.getText(self, "Новый профиль", "Название профиля:")
        if not accepted:
            return
        try:
            bundle = self.profile_service.create_minecraft_profile(name)
            if bundle.profile.id is None:
                raise ConfigurationError("Не удалось получить id нового профиля.")
            self.profile_service.set_active_minecraft_profile(bundle.profile.id)
        except (ConfigurationError, ValueError) as exc:
            QMessageBox.warning(self, "Minecraft", str(exc))
            return
        self.reload_active_profile()
        self._append_log(f"Создан профиль: {bundle.profile.name}")
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
            self.profile_service.rename_minecraft_profile(int(profile_id), name)
        except ConfigurationError as exc:
            QMessageBox.warning(self, "Minecraft", str(exc))
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
            f"Удалить Minecraft-профиль «{self.profile_select.currentText()}»?",
        )
        if answer != QMessageBox.Yes:
            return
        try:
            self.profile_service.delete_minecraft_profile(int(profile_id))
        except ConfigurationError as exc:
            QMessageBox.warning(self, "Minecraft", str(exc))
            return
        self.reload_active_profile()
        self.profile_changed.emit()

    def _load_active_profile(self) -> None:
        config = self.profile_service.get_active_minecraft_profile().config
        self.server_dir.set_path(config.server_dir)
        self.jar_path.set_path(config.jar_path)
        self.java_path.set_path(config.java_path)
        self.xms.setText(config.xms)
        self.xmx.setText(config.xmx)
        self.port.setValue(config.mc_port)
        self.server_type.setCurrentText(config.server_type)
        self.mc_version.setText(config.mc_version)
        self.online_mode.setChecked(config.online_mode)
        self.difficulty.setCurrentText(config.difficulty)
        self.max_players.setValue(config.max_players)
        self.motd.setText(config.motd)
        self.view_distance.setValue(config.view_distance)
        self.simulation_distance.setValue(config.simulation_distance)

    def _config_from_ui(self) -> MinecraftConfig:
        return MinecraftConfig(
            server_dir=self.server_dir.text(),
            jar_path=self.jar_path.text(),
            java_path=self.java_path.text(),
            xms=self.xms.text().strip() or "2G",
            xmx=self.xmx.text().strip() or "4G",
            mc_port=self.port.value(),
            server_type=self.server_type.currentText(),
            mc_version=self.mc_version.text().strip(),
            online_mode=self.online_mode.isChecked(),
            difficulty=self.difficulty.currentText(),
            max_players=self.max_players.value(),
            motd=self.motd.text().strip() or "MineBridge FRP server",
            view_distance=self.view_distance.value(),
            simulation_distance=self.simulation_distance.value(),
        )

    def _save_profile_config(self) -> MinecraftConfig:
        bundle = self.profile_service.get_active_minecraft_profile()
        config = self._config_from_ui()
        bundle.config = config.model_copy(update={"id": bundle.config.id})
        self.profile_service.save_minecraft_profile(bundle)
        return config

    def _find_java(self) -> None:
        java = self.manager.find_java()
        if not java:
            QMessageBox.warning(self, "Java", "Java не найдена в PATH.")
            return
        self.java_path.set_path(java)
        self._append_log(f"Java найдена: {java}")

    def _check_java(self) -> None:
        try:
            output = self.manager.check_java_version(self.java_path.text() or None)
            QMessageBox.information(self, "Java", output.splitlines()[0] if output else "Java OK")
            self._append_log(output)
        except ConfigurationError as exc:
            QMessageBox.warning(self, "Java", str(exc))

    def _choose_server_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Выберите папку Minecraft-сервера")
        if path:
            self.server_dir.set_path(path)

    def _find_server_jar(self) -> None:
        start_dir = self.server_dir.text()
        path, _ = QFileDialog.getOpenFileName(self, "Выберите server.jar", start_dir, "JAR (*.jar)")
        if path:
            self.jar_path.set_path(path)

    def _open_eula(self) -> None:
        server_dir = Path(self.server_dir.text())
        if not self.server_dir.text():
            QMessageBox.warning(self, "EULA", "Сначала выберите папку сервера.")
            return
        path = self.manager.open_eula(server_dir)
        self._append_log(f"Открыт EULA файл: {path}")

    def _save_server_properties(self) -> None:
        try:
            config = self._save_profile_config()
            path = self.manager.save_server_properties(
                Path(config.server_dir),
                self._server_properties(),
            )
            self._append_log(f"server.properties сохранён: {path}")
            QMessageBox.information(self, "Minecraft", "server.properties сохранён.")
        except (ConfigurationError, OSError) as exc:
            QMessageBox.warning(self, "Minecraft", str(exc))

    def _server_properties(self) -> dict[str, object]:
        return {
            "server-port": self.port.value(),
            "online-mode": self.online_mode.isChecked(),
            "difficulty": self.difficulty.currentText(),
            "max-players": self.max_players.value(),
            "motd": self.motd.text().strip() or "MineBridge FRP server",
            "view-distance": self.view_distance.value(),
            "simulation-distance": self.simulation_distance.value(),
        }

    def _start_server(self) -> None:
        try:
            config = self._save_profile_config()
            self.manager.save_server_properties(Path(config.server_dir), self._server_properties())
            self._ensure_eula(config)
            self.manager.start_server(config)
            self._append_log("Minecraft-сервер запускается...")
        except (ConfigurationError, ServiceError, OSError) as exc:
            QMessageBox.warning(self, "Minecraft", str(exc))

    def _ensure_eula(self, config: MinecraftConfig) -> None:
        server_dir = Path(config.server_dir)
        if self.manager.check_eula(server_dir):
            return
        if self.accept_eula.isChecked():
            self.manager.accept_eula_after_user_confirm(server_dir)
            self._append_log("EULA Minecraft принята по явному подтверждению пользователя.")
            return
        if self.auto_open_eula.isChecked():
            self.manager.open_eula(server_dir)
        raise ConfigurationError(
            "EULA Minecraft не принята. Отметьте чекбокс согласия или откройте eula.txt."
        )

    def _stop_server(self) -> None:
        try:
            self.manager.stop_server_gracefully()
            QTimer.singleShot(15000, self._offer_kill_if_still_running)
        except ServiceError as exc:
            QMessageBox.warning(self, "Minecraft", str(exc))

    def _restart_server(self) -> None:
        self._stop_server()
        QTimer.singleShot(2500, self._start_server)

    def _send_command(self, command: str) -> None:
        try:
            self.manager.send_command(command)
            self._append_log(f"> {command}")
        except ServiceError as exc:
            QMessageBox.warning(self, "Minecraft", str(exc))

    def _offer_kill_if_still_running(self) -> None:
        process = self.manager.process
        if not process or process.state() == QProcess.ProcessState.NotRunning:
            return
        answer = QMessageBox.question(
            self,
            "Minecraft",
            "Сервер не остановился за 15 секунд. Завершить процесс принудительно?",
        )
        if answer == QMessageBox.Yes:
            self.manager.kill_server()

    def _on_status_changed(self, status: str) -> None:
        self._append_log(f"Статус Minecraft: {status}")

    def _append_log(self, line: str) -> None:
        self.log_viewer.append_line(line)

    def _show_error(self, message: str) -> None:
        self._append_log(message)
