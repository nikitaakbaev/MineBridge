from __future__ import annotations

import tomllib
from pathlib import Path

from minebridge_frp.app import electron_launcher


def test_project_script_uses_electron_launcher_as_default():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    scripts = pyproject["project"]["scripts"]
    dependencies = pyproject["project"]["dependencies"]

    assert scripts["minebridge-frp"] == "minebridge_frp.app.electron_launcher:main"
    assert scripts["minebridge-frp-api"] == "minebridge_frp.app.api.main:main"
    assert "minebridge-frp-qt" not in scripts
    assert not any(dependency.startswith("PySide6") for dependency in dependencies)


def test_electron_launcher_checks_required_frontend_files():
    missing = electron_launcher._missing_frontend_files(Path.cwd())

    assert missing == []


def test_desktop_runner_points_to_electron_launcher():
    runner = Path("scripts/run_minebridge_frp.sh").read_text(encoding="utf-8")

    assert "minebridge_frp.app.electron_launcher" in runner
    assert "MINEBRIDGE_USE_QT" not in runner
    assert "minebridge_frp.app.main" not in runner


def test_electron_launcher_cleans_electron_node_environment(monkeypatch):
    monkeypatch.setenv("ELECTRON_RUN_AS_NODE", "1")
    monkeypatch.setenv("ELECTRON_NO_ATTACH_CONSOLE", "1")

    env = electron_launcher._electron_env()

    assert "ELECTRON_RUN_AS_NODE" not in env
    assert "ELECTRON_NO_ATTACH_CONSOLE" not in env


def test_qt_ui_files_are_removed():
    removed_paths = [
        Path("minebridge_frp/app/main.py"),
        Path("minebridge_frp/app/core/single_instance.py"),
        Path("packaging/minebridge-frp.spec"),
        Path("scripts/build_linux.sh"),
        Path("scripts/build_windows.ps1"),
    ]

    assert all(not path.exists() for path in removed_paths)
    assert not list(Path("minebridge_frp/app/ui").glob("**/*.py"))
