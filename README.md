# MineBridge FRP

MineBridge FRP is a desktop GUI app for running a Minecraft server on the user's PC and exposing it to friends through an FRP tunnel on a cheap VPS.

## Current Stage

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
- remote command execution with sudo support;
- SFTP upload helpers;
- remote frps.toml generation;
- minebridge-frps systemd unit generation and installation;
- frps start/stop/restart/status controls;
- ufw/firewalld port opening without disabling the firewall;
- full remote frps installation flow for Linux amd64 VPS hosts.

Stage 6 is implemented:

- Quick Start profile validation;
- Java and local Minecraft port checks;
- VPS SSH/frps readiness check;
- local Minecraft launch;
- local port polling before tunnel startup;
- frpc.toml generation and local frpc launch;
- friend address display as VPS_IP:REMOTE_PORT;
- stop-all action for local Minecraft/frpc and remote frps when available.

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

## Roadmap

The next stage adds a fuller diagnostics tab with per-check statuses and safe fix actions.
