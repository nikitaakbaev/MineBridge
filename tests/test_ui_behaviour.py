from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from minebridge_frp.app.core.app_context import AppContext  # noqa: E402
from minebridge_frp.app.services.profile_service import ProfileService  # noqa: E402
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
    finished = []

    def finish(value: object) -> None:
        results.append(value)

    def fail(message: str) -> None:
        errors.append(message)

    thread = run_in_thread(lambda: "worker-ran", finish, fail)
    thread.finished.connect(lambda: finished.append(True))
    thread.finished.connect(app.quit)
    QTimer.singleShot(3000, app.quit)
    app.exec()

    assert thread is not None
    assert finished == [True]
    assert results == ["worker-ran"]
    assert errors == []


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
    tab.install_dir.setText("/opt/minebridge-frp-test")
    tab.bind_port.setValue(7001)
    tab.dashboard_enabled.setChecked(True)
    tab.dashboard_port.setValue(7501)

    tab._save_profile_config()
    saved = profile_service.get_active_profile().vps

    assert saved.host == "193.124.67.110"
    assert saved.ssh_port == 2222
    assert saved.username == "root"
    assert saved.install_dir == "/opt/minebridge-frp-test"
    assert saved.frps_bind_port == 7001
    assert saved.dashboard_enabled is True
    assert saved.dashboard_port == 7501
