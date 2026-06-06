"""Process utilities."""

from __future__ import annotations

import psutil


def is_process_running(name_part: str) -> bool:
    """Return True when a running process name or cmdline contains text."""
    needle = name_part.lower()
    for process in psutil.process_iter(["name", "cmdline"]):
        try:
            name = (process.info.get("name") or "").lower()
            cmdline = " ".join(process.info.get("cmdline") or []).lower()
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
        if needle in name or needle in cmdline:
            return True
    return False
