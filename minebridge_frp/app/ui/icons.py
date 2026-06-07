"""Application icon helpers."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon

ICON_RELATIVE_PATH = Path("resources") / "icons" / "minebridge-frp.svg"
ICONS_RELATIVE_DIR = Path("resources") / "icons"


def app_icon_path() -> Path | None:
    """Return the bundled or source-tree application icon path."""
    return resource_icon_path("minebridge-frp.svg")


def resource_icon_path(name: str) -> Path | None:
    """Return a bundled or source-tree icon path by file name."""
    bundle_root = getattr(sys, "_MEIPASS", None)
    candidates: list[Path] = []

    if bundle_root:
        candidates.append(Path(bundle_root) / ICONS_RELATIVE_DIR / name)

    source_root = Path(__file__).resolve().parents[3]
    candidates.append(source_root / ICONS_RELATIVE_DIR / name)

    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def load_app_icon() -> QIcon:
    icon_path = app_icon_path()
    if icon_path is None:
        return QIcon()
    return QIcon(str(icon_path))
