"""Launch the Electron UI as the primary MineBridge desktop app."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def main() -> int:
    """Start the Electron launcher in development mode."""
    if os.environ.get("MINEBRIDGE_USE_QT") == "1":
        from minebridge_frp.app.main import main as qt_main

        return qt_main()

    project_root = _project_root()
    missing = _missing_frontend_files(project_root)
    if missing:
        print(
            "MineBridge Electron UI files are missing:\n"
            + "\n".join(f"- {path}" for path in missing),
            flush=True,
        )
        print("Run from the project checkout or install the Electron build artifact.", flush=True)
        return 1

    npm = shutil.which("npm")
    if npm is None:
        print("MineBridge now uses the Electron UI as the primary interface.", flush=True)
        print("Node.js and npm are required to start it in the development checkout.", flush=True)
        print("Install Node.js, run `npm install`, then run `minebridge-frp` again.", flush=True)
        print("Temporary Qt fallback: MINEBRIDGE_USE_QT=1 minebridge-frp", flush=True)
        return 1

    return subprocess.call([npm, "run", "dev"], cwd=project_root, env=_electron_env())


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _missing_frontend_files(project_root: Path) -> list[Path]:
    required = [
        project_root / "package.json",
        project_root / "electron" / "main.cjs",
        project_root / "frontend" / "index.html",
        project_root / "frontend" / "src" / "App.tsx",
    ]
    return [path for path in required if not path.exists()]


def _electron_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("ELECTRON_RUN_AS_NODE", None)
    env.pop("ELECTRON_NO_ATTACH_CONSOLE", None)
    return env


if __name__ == "__main__":
    raise SystemExit(main())
