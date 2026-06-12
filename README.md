# MineBridge FRP

MineBridge FRP is a desktop GUI app for running a Minecraft server on the user's PC and exposing it to friends through an FRP tunnel on a cheap VPS.

## Current Stage

Electron migration stage 1 is documented in
[`docs/electron-migration-stage-1.md`](docs/electron-migration-stage-1.md). It maps the
current PySide6 UI, services, models, dependencies, and the planned FastAPI + WebSocket
bridge for the future Electron frontend.

Stage 1 is implemented:

- project skeleton;
- Python packaging config;
- PySide6 application entry point;
- main window with the required tabs;
- basic application logger;
- placeholder widgets and tabs for later stages.

Stage 2 is implemented:

- Pydantic models for profiles, VPS, Minecraft, tunnel, and diagnostics;
- SQLite database with SQLAlchemy tables;
- automatic default profile creation;
- profile listing and active profile selection;
- independent VPS, Minecraft, and frpc profile lists for mixing saved configurations;
- profile presets can be created, renamed, deleted, and selected per workflow tab;
- profile JSON import/export from the Quick Start tab.

Stage 3 is implemented:

- Minecraft tab is connected to the active profile;
- Java discovery and version checks;
- server folder and server.jar selection;
- server.properties read/write helpers;
- explicit EULA handling without silent acceptance;
- local Minecraft server start/stop/restart through QProcess;
- realtime Minecraft log output and stdin command console.

Stage 4 is implemented:

- secure FRP token generation;
- frpc.toml generation with tomlkit;
- current OS/architecture detection for FRP assets;
- FRP download and archive extraction helpers;
- local frpc start/stop through QProcess;
- realtime frpc logs and external port checks.

Stage 5 is implemented:

- SSH connections to VPS through paramiko;
- saved VPS passwords are encrypted locally with an app key in the config directory;
- remote command execution with sudo support;
- SFTP upload helpers;
- remote frps.toml generation;
- minebridge-frps systemd unit generation and installation;
- frps start/stop/restart/status controls;
- ufw/firewalld port opening without disabling the firewall;
- full remote frps installation flow for Linux amd64 VPS hosts.

Stage 6 is implemented as separate manual workflow tabs:

- VPS tab manages SSH, remote frps install/config/systemd/firewall;
- Minecraft tab manages the local server folder, server.properties, EULA, and Java process;
- frpc tab manages the local frpc working folder, frpc.toml, binary download, launch, logs, and external port checks;
- VPS, Minecraft, and frpc tabs have separate profile selectors;
- the old all-in-one Quick Start tab has been removed to keep each action explicit.

Stage 7 is implemented:

- Diagnostics tab runs active-profile checks in a background thread;
- checks cover Java, server folder, server.jar, EULA, server.properties, ports, frpc, token, and VPS basics;
- each result has OK / WARNING / ERROR status and a readable description;
- safe fix actions are available for token generation, Java discovery, EULA opening, and server.properties generation;
- diagnostics report summarizes all checks.

Stage 8 is implemented:

- status badges are used in runtime and diagnostics views;
- window geometry/state are saved and restored;
- the interface uses a permanent dark theme;
- close behavior is persisted through QSettings;
- close behavior supports ask, tray minimize, stop-all, and leave-running modes;
- tray icon is enabled when the platform provides a system tray.

Stage 9 is implemented:

- unit tests cover frpc.toml generation;
- unit tests cover frps.toml generation with and without dashboard settings;
- server.properties parsing and formatting are covered by round-trip tests;
- local port probing is covered with a socket listener test;
- token generation and token validation are covered;
- Pydantic profile, VPS, Minecraft, and tunnel model validation is covered;
- profile import/export safety is covered by database-id cleanup tests.

Stage 10 is implemented:

- PyInstaller spec is provided in `packaging/minebridge-frp.spec`;
- Linux portable one-folder build script is provided in `scripts/build_linux.sh`;
- Windows build script is provided in `scripts/build_windows.ps1`;
- builds include application code only and do not bundle profile databases, FRP runtime downloads, `.env` files, or secrets.

## Requirements

- Python 3.11+
- Windows 10/11 or Linux x86_64

## Install For Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Run

```bash
python -m minebridge_frp.app.main
```

or, after installation:

```bash
minebridge-frp
```

## Desktop Launcher

On Linux, install the app menu launcher:

```bash
scripts/install_desktop_launcher.sh
```

It creates `MineBridge FRP` in the application menu and uses the project `.venv` through `scripts/run_minebridge_frp.sh`, so the app can be opened without typing a run command.

## Test

```bash
python -m compileall minebridge_frp tests
ruff check .
pytest
```

## Build With PyInstaller

Install packaging dependencies:

```bash
pip install -e ".[packaging]"
```

Linux portable folder:

```bash
scripts/build_linux.sh
```

The output folder is:

```text
dist/MineBridge FRP
```

Windows executable folder from PowerShell:

```powershell
.\scripts\build_windows.ps1
```

The output executable is:

```text
dist\MineBridge FRP\MineBridge FRP.exe
```

Do not copy local runtime data into release builds. In particular, keep `.minebridge-frp/`, profile exports, SQLite databases, `.env` files, downloaded FRP archives/binaries, SSH keys, and passwords outside distributable artifacts.

## Roadmap

Future stages can add signed installers, automatic FRP update checks, richer remote diagnostics, and guided first-run setup.
