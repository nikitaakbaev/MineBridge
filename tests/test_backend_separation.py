from __future__ import annotations

from pathlib import Path

from minebridge_frp.app.services.frp_manager import FrpManager
from minebridge_frp.app.services.minecraft_manager import MinecraftManager


def test_runtime_managers_do_not_import_qt():
    for path in (
        Path("minebridge_frp/app/services/minecraft_manager.py"),
        Path("minebridge_frp/app/services/frp_manager.py"),
    ):
        source = path.read_text(encoding="utf-8")
        assert "PySide6" not in source
        assert "QProcess" not in source
        assert "QObject" not in source
        assert "from PySide6.QtCore import Signal" not in source


def test_minecraft_open_eula_only_returns_path(tmp_path):
    path = MinecraftManager().open_eula(tmp_path)

    assert path == tmp_path / "eula.txt"
    assert path.read_text(encoding="utf-8") == "eula=false\n"


def test_frp_manager_exposes_callback_events(tmp_path):
    manager = FrpManager(tmp_path)
    statuses: list[str] = []

    manager.status_changed.connect(statuses.append)
    manager.status_changed.emit("running")

    assert statuses == ["running"]
