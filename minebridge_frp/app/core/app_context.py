"""Shared application context."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from minebridge_frp.app.core.config_paths import (
    ensure_writable_path,
    get_config_dir,
    get_data_dir,
    get_log_dir,
)


@dataclass(frozen=True)
class AppContext:
    """Runtime paths and shared application state."""

    config_dir: Path
    data_dir: Path
    log_dir: Path
    database_path: Path

    @classmethod
    def create(cls) -> AppContext:
        config_dir = ensure_writable_path(get_config_dir())
        data_dir = ensure_writable_path(get_data_dir())
        log_dir = ensure_writable_path(get_log_dir())

        database_path = data_dir / "minebridge-frp.sqlite3"

        return cls(
            config_dir=config_dir,
            data_dir=data_dir,
            log_dir=log_dir,
            database_path=database_path,
        )
