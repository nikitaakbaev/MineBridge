from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QThread, QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from minebridge_frp.app.core.app_context import AppContext  # noqa: E402
from minebridge_frp.app.services.profile_service import ProfileService  # noqa: E402
from minebridge_frp.app.ui.tabs.logs_tab import LogsTab  # noqa: E402
from minebridge_frp.app.ui.tabs.vps_tab import VpsTab  # noqa: E402
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
    saved = profile_service.get_active_profile().vps

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
