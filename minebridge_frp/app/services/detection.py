"""Detect Minecraft server launch files and Java installations."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

_LAUNCHER_NAMES_EXACT = {
    "server.jar",
    "minecraft_server.jar",
    "paper.jar",
    "purpur.jar",
    "spigot.jar",
    "craftbukkit.jar",
    "fabric-server-launch.jar",
    "fabric-server-launcher.jar",
    "quilt-server-launch.jar",
    "forge-server.jar",
    "neoforge-server.jar",
}

_SCRIPT_SUFFIXES = (".sh", ".bash", ".bat", ".cmd", ".ps1")
_LAUNCHER_SCRIPT_BASES = {
    "run",
    "start",
    "launch",
    "server",
    "start-server",
    "run-server",
}

_JAR_KEYWORDS = (
    "server",
    "paper",
    "purpur",
    "spigot",
    "fabric",
    "quilt",
    "forge",
    "neoforge",
)

_VERSION_PATTERN = re.compile(r'version\s+"([^"]+)"', re.IGNORECASE)


@dataclass(frozen=True)
class LauncherCandidate:
    """A candidate file that can launch a Minecraft server."""

    path: str
    kind: str
    score: int


@dataclass(frozen=True)
class JavaInstallation:
    """A discovered Java installation."""

    path: str
    version: str
    vendor: str = ""


def _iter_directory(directory: Path) -> Iterator[Path]:
    try:
        for entry in directory.iterdir():
            if entry.is_file():
                yield entry
    except OSError:
        return


def _score_jar(name: str) -> int:
    lower = name.lower()
    if lower in _LAUNCHER_NAMES_EXACT:
        return 100
    if any(keyword in lower for keyword in _JAR_KEYWORDS):
        return 60
    return 20


def _script_kind(suffix: str) -> str:
    if suffix in (".sh", ".bash"):
        return "shell"
    if suffix in (".bat", ".cmd"):
        return "batch"
    if suffix == ".ps1":
        return "powershell"
    return "script"


def _script_runs_on_current_os(suffix: str) -> bool:
    if suffix in (".sh", ".bash"):
        return os.name != "nt" or shutil.which("bash") is not None
    if suffix in (".bat", ".cmd"):
        return os.name == "nt"
    if suffix == ".ps1":
        return shutil.which("pwsh") is not None or shutil.which("powershell") is not None
    return True


def detect_server_launchers(server_dir: Path) -> list[LauncherCandidate]:
    """Find launch scripts and jars under a server directory.

    The result is sorted by score descending. Scripts named like ``run.sh`` or
    ``start.bat`` always win over auxiliary jars; well-known launcher jars beat
    arbitrary jars. Pure shaded libraries (``log4j-*.jar`` etc.) get the lowest
    score so they only appear if nothing else matches.
    """
    if not server_dir.exists() or not server_dir.is_dir():
        return []

    candidates: list[LauncherCandidate] = []
    seen: set[str] = set()

    for entry in _iter_directory(server_dir):
        suffix = entry.suffix.lower()
        if suffix in _SCRIPT_SUFFIXES:
            base = entry.stem.lower()
            if base.startswith("user_jvm") or base.startswith("install"):
                continue
            score = 200 if base in _LAUNCHER_SCRIPT_BASES else 150
            if not _script_runs_on_current_os(suffix):
                # The script can't be launched on this OS — keep it as a
                # last-resort candidate but never let it beat anything else.
                score = 5
            candidates.append(
                LauncherCandidate(path=str(entry), kind=_script_kind(suffix), score=score)
            )
            seen.add(str(entry))

    for entry in _iter_directory(server_dir):
        if entry.suffix.lower() != ".jar":
            continue
        if str(entry) in seen:
            continue
        candidates.append(
            LauncherCandidate(path=str(entry), kind="jar", score=_score_jar(entry.name))
        )

    candidates.sort(key=lambda c: (-c.score, c.path.lower()))
    return candidates


def _java_version(path: Path) -> str | None:
    try:
        result = subprocess.run(
            [str(path), "-version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    output = result.stderr or result.stdout or ""
    match = _VERSION_PATTERN.search(output)
    if match:
        return match.group(1)
    first = next((line.strip() for line in output.splitlines() if line.strip()), "")
    return first or None


def _java_vendor(version_output: str) -> str:
    lower = version_output.lower()
    for vendor in ("temurin", "openjdk", "graalvm", "zulu", "corretto", "liberica", "oracle"):
        if vendor in lower:
            return vendor
    return ""


def _candidate_java_paths() -> Iterator[Path]:
    if java_home := os.environ.get("JAVA_HOME"):
        yield Path(java_home) / "bin" / _java_executable_name()

    paths_env = os.environ.get("PATH", "")
    for raw in paths_env.split(os.pathsep):
        if not raw:
            continue
        candidate = Path(raw) / _java_executable_name()
        yield candidate

    yield from _windows_well_known_java_paths()
    yield from _unix_well_known_java_paths()


def _java_executable_name() -> str:
    return "java.exe" if os.name == "nt" else "java"


def _windows_well_known_java_paths() -> Iterator[Path]:
    if os.name != "nt":
        return
    program_files = [
        os.environ.get("ProgramFiles"),
        os.environ.get("ProgramFiles(x86)"),
        os.environ.get("ProgramW6432"),
    ]
    vendors = (
        "Java",
        "Eclipse Adoptium",
        "Eclipse Foundation",
        "Microsoft",
        "Amazon Corretto",
        "BellSoft",
        "Zulu",
        "Semeru",
    )
    for base in program_files:
        if not base:
            continue
        for vendor in vendors:
            vendor_dir = Path(base) / vendor
            if not vendor_dir.exists():
                continue
            try:
                for entry in vendor_dir.iterdir():
                    candidate = entry / "bin" / "java.exe"
                    if candidate.exists():
                        yield candidate
            except OSError:
                continue


def _unix_well_known_java_paths() -> Iterator[Path]:
    if os.name == "nt":
        return
    roots = [
        Path("/usr/lib/jvm"),
        Path("/usr/java"),
        Path("/opt/java"),
        Path.home() / ".sdkman" / "candidates" / "java",
        Path("/Library/Java/JavaVirtualMachines"),
    ]
    for root in roots:
        if not root.exists():
            continue
        try:
            for entry in root.iterdir():
                for relative in ("bin/java", "Contents/Home/bin/java"):
                    candidate = entry / relative
                    if candidate.exists():
                        yield candidate
        except OSError:
            continue


def detect_java_installations(extra_paths: Iterable[str] = ()) -> list[JavaInstallation]:
    """Find every Java executable accessible from the current environment.

    Walks ``JAVA_HOME``, ``PATH``, well-known vendor install roots on Windows
    (Program Files\\<Vendor>\\<dist>\\bin\\java.exe) and Linux/macOS
    (/usr/lib/jvm, /Library/Java/...), plus any ``extra_paths`` provided by the
    caller. Each binary is invoked once with ``-version`` to read the actual
    version string. Results are deduplicated by resolved path.
    """
    seen: set[str] = set()
    found: list[JavaInstallation] = []

    candidates = list(_candidate_java_paths())
    for raw in extra_paths:
        if raw:
            candidates.append(Path(raw))
    if which := shutil.which("java"):
        candidates.append(Path(which))

    for candidate in candidates:
        if not candidate.exists() or not candidate.is_file():
            continue
        try:
            resolved = str(candidate.resolve())
        except OSError:
            resolved = str(candidate)
        if resolved in seen:
            continue
        version = _java_version(candidate)
        if not version:
            continue
        seen.add(resolved)
        found.append(
            JavaInstallation(
                path=resolved,
                version=version,
                vendor=_java_vendor(version),
            )
        )

    found.sort(key=lambda item: _version_sort_key(item.version), reverse=True)
    return found


def _version_sort_key(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for chunk in re.findall(r"\d+", version):
        try:
            parts.append(int(chunk))
        except ValueError:
            continue
        if len(parts) >= 4:
            break
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts)
