from __future__ import annotations

import os
from uuid import uuid4

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QThread, QTimer  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QApplication,
    QFormLayout,
    QLineEdit,
    QScrollArea,
    QSplitter,
    QTabWidget,
)

from minebridge_frp.app.core.app_context import AppContext  # noqa: E402
from minebridge_frp.app.core.single_instance import SingleInstanceGuard  # noqa: E402
from minebridge_frp.app.services.profile_service import ProfileService  # noqa: E402
from minebridge_frp.app.ui.main_window import MainWindow  # noqa: E402
from minebridge_frp.app.ui.tabs.logs_tab import LogsTab  # noqa: E402
from minebridge_frp.app.ui.tabs.minecraft_tab import MinecraftTab  # noqa: E402
from minebridge_frp.app.ui.tabs.settings_tab import SettingsTab  # noqa: E402
from minebridge_frp.app.ui.tabs.vps_tab import VpsTab  # noqa: E402
from minebridge_frp.app.ui.theme import apply_theme  # noqa: E402
from minebridge_frp.app.ui.widgets.log_viewer import clean_log_line  # noqa: E402
from minebridge_frp.app.ui.workers import run_in_thread  # noqa: E402


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_run_in_thread_keeps_worker_alive_until_finished():
    app = _app()
    results = []
    errors = []
    callback_threads = []

    def finish(value: object) -> None:
        results.append(value)
        callback_threads.append(QThread.currentThread())
        QTimer.singleShot(50, app.quit)

    def fail(message: str) -> None:
        errors.append(message)
        callback_threads.append(QThread.currentThread())
        QTimer.singleShot(50, app.quit)

    thread = run_in_thread(lambda: "worker-ran", finish, fail)
    QTimer.singleShot(3000, app.quit)
    app.exec()

    assert thread is not None
    assert results == ["worker-ran"]
    assert errors == []
    assert callback_threads == [app.thread()]


def test_vps_tab_saves_settings_from_ui(tmp_path):
    _app()
    data_dir = tmp_path / "data"
    context = AppContext(
        config_dir=tmp_path / "config",
        data_dir=data_dir,
        log_dir=tmp_path / "logs",
        database_path=data_dir / "minebridge-frp.sqlite3",
    )
    profile_service = ProfileService.from_context(context)
    tab = VpsTab(context, profile_service)

    tab.host.setText("193.124.67.110")
    tab.ssh_port.setValue(2222)
    tab.username.setText("root")
    tab.password.setText("ssh-secret")
    tab.install_dir.setText("/opt/minebridge-frp-test")
    tab.bind_port.setValue(7001)
    tab.dashboard_enabled.setChecked(True)
    tab.dashboard_port.setValue(7501)

    tab._save_profile_config()
    saved = profile_service.get_active_vps_profile().config

    assert saved.host == "193.124.67.110"
    assert saved.ssh_port == 2222
    assert saved.username == "root"
    assert saved.password_encrypted is not None
    assert saved.password_encrypted != "ssh-secret"
    assert saved.install_dir == "/opt/minebridge-frp-test"
    assert saved.frps_bind_port == 7001
    assert saved.dashboard_enabled is True
    assert saved.dashboard_port == 7501

    reloaded_tab = VpsTab(context, profile_service)

    assert reloaded_tab.password.text() == "ssh-secret"


def test_vps_tab_shows_only_selected_auth_fields(tmp_path):
    _app()
    data_dir = tmp_path / "data"
    context = AppContext(
        config_dir=tmp_path / "config",
        data_dir=data_dir,
        log_dir=tmp_path / "logs",
        database_path=data_dir / "minebridge-frp.sqlite3",
    )
    profile_service = ProfileService.from_context(context)
    tab = VpsTab(context, profile_service)
    form = tab.private_key_path.parentWidget().layout()

    assert isinstance(form, QFormLayout)
    assert tab.auth_type.currentText() == "password"
    assert not tab.password.isHidden()
    assert tab.private_key_path.isHidden()
    assert form.labelForField(tab.private_key_path).isHidden()

    tab.auth_type.setCurrentText("private_key")

    assert tab.password.isHidden()
    assert form.labelForField(tab.password).isHidden()
    assert not tab.private_key_path.isHidden()
    assert not form.labelForField(tab.private_key_path).isHidden()


def test_vps_and_minecraft_tabs_can_switch_profiles(tmp_path):
    _app()
    data_dir = tmp_path / "data"
    context = AppContext(
        config_dir=tmp_path / "config",
        data_dir=data_dir,
        log_dir=tmp_path / "logs",
        database_path=data_dir / "minebridge-frp.sqlite3",
    )
    profile_service = ProfileService.from_context(context)
    profile_service.create_vps_profile("VPS test")
    profile_service.create_minecraft_profile("Paper test")
    vps_tab = VpsTab(context, profile_service)
    minecraft_tab = MinecraftTab(profile_service)

    assert vps_tab.profile_select.count() == 2
    assert minecraft_tab.profile_select.count() == 2

    vps_index = vps_tab.profile_select.findText("VPS test")
    minecraft_index = minecraft_tab.profile_select.findText("Paper test")
    assert vps_index >= 0
    assert minecraft_index >= 0
    vps_tab.profile_select.setCurrentIndex(vps_index)
    minecraft_tab.profile_select.setCurrentIndex(minecraft_index)

    assert profile_service.get_active_vps_profile().profile.name == "VPS test"
    assert profile_service.get_active_minecraft_profile().profile.name == "Paper test"
    assert vps_tab.profile_select.currentText() == "VPS test"
    assert minecraft_tab.profile_select.currentText() == "Paper test"


def test_runtime_tabs_expose_profile_edit_buttons(tmp_path):
    _app()
    data_dir = tmp_path / "data"
    context = AppContext(
        config_dir=tmp_path / "config",
        data_dir=data_dir,
        log_dir=tmp_path / "logs",
        database_path=data_dir / "minebridge-frp.sqlite3",
    )
    window = MainWindow(context)

    for tab in (window.vps_tab, window.minecraft_tab, window.frpc_tab):
        assert tab.new_profile_button.text() == "Новый профиль"
        assert tab.rename_profile_button.text() == "Переименовать"
        assert tab.delete_profile_button.text() == "Удалить"


def test_logs_tab_loads_and_filters_app_log(tmp_path):
    _app()
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "minebridge-frp.log").write_text(
        "\n".join(
            [
                "2026-06-06 [INFO] minebridge_frp.app.main: Starting MineBridge FRP",
                "2026-06-06 [INFO] paramiko.transport: Authentication successful",
                "2026-06-06 [INFO] frpc: login succeeded",
            ]
        ),
        encoding="utf-8",
    )

    tab = LogsTab(log_dir)

    assert "Starting MineBridge" in tab.viewers["App logs"].text.toPlainText()
    assert "paramiko.transport" in tab.viewers["SSH/VPS"].text.toPlainText()
    assert "frpc: login succeeded" in tab.viewers["frpc"].text.toPlainText()


def test_main_window_uses_direct_manual_workflow_tabs(tmp_path):
    _app()
    data_dir = tmp_path / "data"
    context = AppContext(
        config_dir=tmp_path / "config",
        data_dir=data_dir,
        log_dir=tmp_path / "logs",
        database_path=data_dir / "minebridge-frp.sqlite3",
    )

    window = MainWindow(context)
    tabs = window.centralWidget()

    assert isinstance(tabs, QTabWidget)
    labels = [tabs.tabText(index) for index in range(tabs.count())]
    assert labels == ["VPS", "Minecraft", "frpc", "Диагностика", "Логи", "Настройки"]
    assert "Быстрый запуск" not in labels
    assert not any(isinstance(tabs.widget(index), QScrollArea) for index in range(tabs.count()))


def test_runtime_tabs_have_resizable_log_splitters(tmp_path):
    _app()
    data_dir = tmp_path / "data"
    context = AppContext(
        config_dir=tmp_path / "config",
        data_dir=data_dir,
        log_dir=tmp_path / "logs",
        database_path=data_dir / "minebridge-frp.sqlite3",
    )
    window = MainWindow(context)
    tabs = window.centralWidget()

    for index in (0, 1, 2):
        tab_widget = tabs.widget(index)
        splitter = tab_widget.findChild(QSplitter)
        assert splitter is not None
        assert splitter.count() == 2
        assert isinstance(splitter.widget(0), QScrollArea)


def test_minecraft_form_fields_do_not_collapse_or_overstretch(tmp_path):
    app = _app()
    data_dir = tmp_path / "data"
    context = AppContext(
        config_dir=tmp_path / "config",
        data_dir=data_dir,
        log_dir=tmp_path / "logs",
        database_path=data_dir / "minebridge-frp.sqlite3",
    )
    window = MainWindow(context)
    window.resize(1038, 712)
    window.show()
    app.processEvents()

    tabs = window.centralWidget()
    minecraft_tab = tabs.widget(1)
    line_heights = [field.height() for field in minecraft_tab.findChildren(QLineEdit)]

    assert min(line_heights) >= 28
    assert max(line_heights[:3]) <= 42


def test_log_viewer_cleans_ansi_control_output():
    dirty = "\x1b[1;34m2026-06-06 login success\x1b[0m\r"

    assert clean_log_line(dirty) == "2026-06-06 login success"


def test_settings_tab_does_not_expose_theme_switching(tmp_path):
    _app()
    data_dir = tmp_path / "data"
    context = AppContext(
        config_dir=tmp_path / "config",
        data_dir=data_dir,
        log_dir=tmp_path / "logs",
        database_path=data_dir / "minebridge-frp.sqlite3",
    )
    tab = SettingsTab(context)

    assert not hasattr(tab, "theme")


def test_dark_theme_uses_visible_control_arrows():
    app = _app()
    apply_theme(app)

    style = app.styleSheet()

    assert "control-arrow-up.svg" in style
    assert "control-arrow-down.svg" in style
    assert "QSpinBox::up-arrow" in style
    assert "QComboBox::down-arrow" in style


def test_single_instance_guard_rejects_second_instance():
    app = _app()
    key = f"minebridge-frp-test-{uuid4()}"
    first = SingleInstanceGuard(key)
    second = SingleInstanceGuard(key)

    assert first.acquire() is True
    app.processEvents()
    assert second.acquire() is False
