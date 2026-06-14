"""Minecraft server management service."""

from __future__ import annotations

import re
import shutil
import subprocess
import time
from pathlib import Path

from minebridge_frp.app.core.exceptions import ConfigurationError, ServiceError
from minebridge_frp.app.models.minecraft import MinecraftConfig
from minebridge_frp.app.services.events import CallbackSignal
from minebridge_frp.app.services.process_runner import ProcessRunner
from minebridge_frp.app.utils.ports import wait_until_port_open

_JOIN_PATTERN = re.compile(r"(?:\]:?\s*)([A-Za-z0-9_]{1,16}) joined the game\b")
_LEFT_PATTERN = re.compile(
    r"(?:\]:?\s*)([A-Za-z0-9_]{1,16}) (?:left the game|lost connection)\b"
)
_DONE_PATTERN = re.compile(r'Done \([0-9.]+s\)!')


def parse_server_properties(text: str) -> dict[str, str]:
    """Parse Minecraft server.properties content."""
    properties: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        properties[key.strip()] = value.strip()
    return properties


def format_server_properties(properties: dict[str, object]) -> str:
    """Format server.properties content."""
    lines = ["#MineBridge FRP generated server.properties"]
    for key in sorted(properties):
        value = properties[key]
        if isinstance(value, bool):
            value = str(value).lower()
        lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n"


class MinecraftManager:
    """Manage a local Minecraft server process."""

    def __init__(self) -> None:
        self.log_line = CallbackSignal[[str]]()
        self.status_changed = CallbackSignal[[str]]()
        self.error = CallbackSignal[[str]]()
        self.players_changed = CallbackSignal[[int, list]]()
        self.ready = CallbackSignal[[]]()
        self.process = ProcessRunner()
        self._players: list[str] = []
        self._started_at: float | None = None
        self.process.output.connect(self._handle_output)
        self.process.started.connect(self._handle_started)
        self.process.finished.connect(self._handle_finished)
        self.process.error.connect(self.error.emit)

    @property
    def pid(self) -> int | None:
        return self.process.pid

    @property
    def is_running(self) -> bool:
        return self.process.is_running

    @property
    def players(self) -> list[str]:
        return list(self._players)

    @property
    def player_count(self) -> int:
        return len(self._players)

    @property
    def uptime_seconds(self) -> float:
        if self._started_at is None or not self.process.is_running:
            return 0.0
        return max(0.0, time.time() - self._started_at)

    def _handle_started(self) -> None:
        self._started_at = time.time()
        self._players = []
        self.players_changed.emit(0, [])
        self.status_changed.emit("running")

    def _handle_finished(self, _code: int) -> None:
        self._started_at = None
        if self._players:
            self._players = []
            self.players_changed.emit(0, [])
        self.status_changed.emit("stopped")

    def _handle_output(self, line: str) -> None:
        self.log_line.emit(line)
        self._scan_for_players(line)
        if _DONE_PATTERN.search(line):
            self.ready.emit()

    def _scan_for_players(self, line: str) -> None:
        changed = False
        join = _JOIN_PATTERN.search(line)
        if join:
            name = join.group(1)
            if name not in self._players:
                self._players.append(name)
                changed = True
        left = _LEFT_PATTERN.search(line)
        if left:
            name = left.group(1)
            if name in self._players:
                self._players.remove(name)
                changed = True
        if changed:
            self.players_changed.emit(len(self._players), list(self._players))

    def find_java(self) -> str | None:
        """Find java executable in PATH."""
        return shutil.which("java")

    def check_java_version(self, java_path: str | None = None) -> str:
        """Return Java version output or raise a configuration error."""
        executable = java_path or self.find_java()
        if not executable:
            raise ConfigurationError("Java не найдена в PATH. Укажите путь к java вручную.")

        try:
            result = subprocess.run(
                [executable, "-version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ConfigurationError(f"Не удалось запустить Java: {exc}") from exc

        output = "\n".join(part for part in (result.stderr, result.stdout) if part).strip()
        if result.returncode != 0:
            raise ConfigurationError(output or "Java вернула ошибку.")
        return output

    def load_server_properties(self, server_dir: Path) -> dict[str, str]:
        path = server_dir / "server.properties"
        if not path.exists():
            return {}
        return parse_server_properties(path.read_text(encoding="utf-8"))

    def save_server_properties(self, server_dir: Path, properties: dict[str, object]) -> Path:
        server_dir.mkdir(parents=True, exist_ok=True)
        path = server_dir / "server.properties"
        path.write_text(format_server_properties(properties), encoding="utf-8")
        return path

    def eula_path(self, server_dir: Path) -> Path:
        return server_dir / "eula.txt"

    def check_eula(self, server_dir: Path) -> bool:
        path = self.eula_path(server_dir)
        if not path.exists():
            return False
        properties = parse_server_properties(path.read_text(encoding="utf-8"))
        return properties.get("eula", "").lower() == "true"

    def open_eula(self, server_dir: Path) -> Path:
        server_dir.mkdir(parents=True, exist_ok=True)
        path = self.eula_path(server_dir)
        if not path.exists():
            path.write_text("eula=false\n", encoding="utf-8")
        return path

    def accept_eula_after_user_confirm(self, server_dir: Path) -> Path:
        server_dir.mkdir(parents=True, exist_ok=True)
        path = self.eula_path(server_dir)
        path.write_text("eula=true\n", encoding="utf-8")
        return path

    def start_server(self, config: MinecraftConfig) -> None:
        """Start Minecraft server."""
        if self.process.is_running:
            raise ServiceError("Minecraft-сервер уже запущен.")

        server_dir = Path(config.server_dir)
        jar_path = Path(config.jar_path)
        java_path = config.java_path or self.find_java()

        if not server_dir.exists():
            raise ConfigurationError("Папка сервера не существует.")
        if not jar_path.exists():
            raise ConfigurationError("server.jar не найден.")
        if not java_path:
            raise ConfigurationError("Java не найдена.")
        if not self.check_eula(server_dir):
            raise ConfigurationError(
                "EULA Minecraft не принята. Откройте eula.txt и подтвердите EULA."
            )

        self.process.start(
            java_path,
            [f"-Xms{config.xms}", f"-Xmx{config.xmx}", "-jar", str(jar_path), "nogui"],
            working_directory=server_dir,
        )

    def stop_server_gracefully(self) -> None:
        """Send the Minecraft stop command."""
        if not self.process.is_running:
            self.status_changed.emit("stopped")
            return
        self.send_command("stop")
        self.status_changed.emit("stopping")

    def kill_server(self) -> None:
        if self.process.is_running:
            self.process.kill()
            self.status_changed.emit("killed")

    def send_command(self, command: str) -> None:
        if not self.process.is_running:
            raise ServiceError("Minecraft-сервер не запущен.")
        self.process.send_line(command.strip())

    def wait_until_port_open(self, port: int, timeout_seconds: float = 30.0) -> bool:
        return wait_until_port_open("127.0.0.1", port, timeout_seconds=timeout_seconds)
