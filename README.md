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

The next stage adds Minecraft GUI behavior and the Minecraft manager.
