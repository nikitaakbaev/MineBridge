from __future__ import annotations

import tomllib
from pathlib import Path

from minebridge_frp.app import electron_launcher


def test_project_script_uses_electron_launcher_as_default():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    scripts = pyproject["project"]["scripts"]

    assert scripts["minebridge-frp"] == "minebridge_frp.app.electron_launcher:main"
    assert scripts["minebridge-frp-qt"] == "minebridge_frp.app.main:main"
    assert scripts["minebridge-frp-api"] == "minebridge_frp.app.api.main:main"


def test_electron_launcher_checks_required_frontend_files():
    missing = electron_launcher._missing_frontend_files(Path.cwd())

    assert missing == []


def test_desktop_runner_points_to_electron_launcher():
    runner = Path("scripts/run_minebridge_frp.sh").read_text(encoding="utf-8")

    assert "minebridge_frp.app.electron_launcher" in runner
    assert "MINEBRIDGE_USE_QT" in runner
    assert "minebridge_frp.app.main" in runner


def test_electron_launcher_cleans_electron_node_environment(monkeypatch):
    monkeypatch.setenv("ELECTRON_RUN_AS_NODE", "1")
    monkeypatch.setenv("ELECTRON_NO_ATTACH_CONSOLE", "1")

    env = electron_launcher._electron_env()

    assert "ELECTRON_RUN_AS_NODE" not in env
    assert "ELECTRON_NO_ATTACH_CONSOLE" not in env
