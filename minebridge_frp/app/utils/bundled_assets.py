"""Helpers for packaged runtime assets shipped with the app."""

from __future__ import annotations

import sys
from pathlib import Path


def bundled_frp_root() -> Path:
    """Return the directory containing bundled FRP binaries.

    In development this points at the source tree resources folder.
    In a packaged backend it points next to the frozen executable under
    `<resources>/frp-bundled`.
    """
    candidates: list[Path] = []

    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parents[1] / "frp-bundled")

    candidates.extend(
        [
            Path(__file__).resolve().parents[3] / "resources" / "frp-bundled",
            Path(__file__).resolve().parents[4] / "resources" / "frp-bundled",
        ]
    )

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]
