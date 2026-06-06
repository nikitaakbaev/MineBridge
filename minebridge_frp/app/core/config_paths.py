"""Platform-aware application paths."""

from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "MineBridge FRP"
APP_AUTHOR = "MineBridge"
ENV_HOME = "MINEBRIDGE_HOME"


def _env_home_path(kind: str) -> Path | None:
    home = os.environ.get(ENV_HOME)
    if not home:
        return None

    base = Path(home)
    if kind == "config":
        return base / "config"
    if kind == "data":
        return base / "data"
    if kind == "logs":
        return base / "logs"
    raise ValueError(f"Unknown path kind: {kind}")


def _platform_path(kind: str) -> Path:
    env_path = _env_home_path(kind)
    if env_path is not None:
        return env_path

    try:
        from platformdirs import user_config_dir, user_data_dir, user_log_dir
    except ImportError:
        base = Path.home() / ".minebridge-frp"
        return base / kind

    if kind == "config":
        return Path(user_config_dir(APP_NAME, APP_AUTHOR))
    if kind == "data":
        return Path(user_data_dir(APP_NAME, APP_AUTHOR))
    if kind == "logs":
        return Path(user_log_dir(APP_NAME, APP_AUTHOR))

    raise ValueError(f"Unknown path kind: {kind}")


def get_config_dir() -> Path:
    return _platform_path("config")


def get_data_dir() -> Path:
    return _platform_path("data")


def get_log_dir() -> Path:
    return _platform_path("logs")


def ensure_writable_path(path: Path) -> Path:
    """Return path if writable, otherwise use a local development fallback."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return path
    except OSError:
        fallback = Path.cwd() / ".minebridge-frp" / path.name
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback
