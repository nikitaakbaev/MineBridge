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


def test_vite_splits_recharts_chunk():
    source = Path("vite.config.ts").read_text(encoding="utf-8")

    assert "manualChunks" in source
    assert 'charts: ["recharts"]' in source


def test_electron_backend_uses_sibling_python_exe_for_pythonw():
    source = Path("electron/backend.cjs").read_text(encoding="utf-8")

    assert "siblingPythonExe(result.spawnfile)" in source
    assert 'spawnSync("python", ["--version"]' not in source
    assert "path.dirname(spawnfile)" in source


def test_packaged_app_uses_bundled_backend_and_api_token():
    package = json.loads(Path("package.json").read_text(encoding="utf-8"))
    main_source = Path("electron/main.cjs").read_text(encoding="utf-8")
    backend_source = Path("electron/backend.cjs").read_text(encoding="utf-8")
    preload_source = Path("electron/preload.cjs").read_text(encoding="utf-8")

    assert "npm run build:backend" in package["scripts"]["dist:win"]
    assert "backend-bin" in json.dumps(package["build"]["extraResources"])
    assert "bundledBackendExecutable(process.resourcesPath)" in main_source
    assert "spawnBundledBackend" in backend_source
    assert "MINEBRIDGE_API_TOKEN" in main_source
    assert "apiToken" in preload_source


def test_migrated_electron_screens_exist():
    screens = {
        "HomeScreen.tsx",
        "SetupScreen.tsx",
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
