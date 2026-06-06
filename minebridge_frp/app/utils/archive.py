"""Archive extraction helpers."""

from __future__ import annotations

import os
import tarfile
import zipfile
from pathlib import Path


def extract_archive(archive_path: Path, destination: Path) -> Path:
    """Extract a .zip or .tar.gz archive and return the destination path."""
    destination.mkdir(parents=True, exist_ok=True)

    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(destination)
    elif archive_path.name.endswith((".tar.gz", ".tgz")):
        with tarfile.open(archive_path) as archive:
            archive.extractall(destination)
    else:
        raise ValueError(f"Unsupported archive format: {archive_path}")

    return destination


def make_executable(path: Path) -> None:
    """Add executable bits for the current user/group/others on POSIX."""
    if os.name == "nt":
        return
    mode = path.stat().st_mode
    path.chmod(mode | 0o111)
