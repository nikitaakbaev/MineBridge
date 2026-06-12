from __future__ import annotations

import json
from pathlib import Path


def test_electron_package_scripts_and_dependencies_exist():
    package = json.loads(Path("package.json").read_text(encoding="utf-8"))

    assert package["main"] == "electron/main.cjs"
    assert "dev" in package["scripts"]
    assert "build" in package["scripts"]
    assert package["dependencies"]["react"]
    assert package["dependencies"]["@tanstack/react-query"]
    assert package["dependencies"]["zustand"]
    assert package["dependencies"]["@xterm/xterm"]
    assert package["dependencies"]["recharts"]


def test_migrated_electron_screens_exist():
    screens = {
        "DashboardScreen.tsx",
        "ServersScreen.tsx",
        "MinecraftScreen.tsx",
        "TunnelsScreen.tsx",
        "VpsScreen.tsx",
        "DiagnosticsScreen.tsx",
        "LogsScreen.tsx",
        "SettingsScreen.tsx",
    }

    existing = {path.name for path in Path("frontend/src/screens").glob("*.tsx")}

    assert screens <= existing


def test_renderer_uses_api_client_instead_of_python_business_logic():
    renderer_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("frontend/src").rglob("*.ts*")
    )

    assert "paramiko" not in renderer_sources
    assert "QProcess" not in renderer_sources
    assert "minecraft_manager" not in renderer_sources
    assert "frp_manager" not in renderer_sources
    assert "127.0.0.1:47831" in renderer_sources
