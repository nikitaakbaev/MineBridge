"""Minecraft server management service."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, QUrl, Signal
from PySide6.QtGui import QDesktopServices

from minebridge_frp.app.core.exceptions import ConfigurationError, ServiceError
from minebridge_frp.app.models.minecraft import MinecraftConfig
from minebridge_frp.app.utils.ports import wait_until_port_open


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


class MinecraftManager(QObject):
    """Manage a local Minecraft server process."""

    log_line = Signal(str)
    status_changed = Signal(str)
    error = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.process: QProcess | None = None

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
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        return path

    def accept_eula_after_user_confirm(self, server_dir: Path) -> Path:
        server_dir.mkdir(parents=True, exist_ok=True)
        path = self.eula_path(server_dir)
        path.write_text("eula=true\n", encoding="utf-8")
        return path

    def start_server(self, config: MinecraftConfig) -> None:
        """Start Minecraft server via QProcess."""
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
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

        process = QProcess(self)
        process.setProgram(java_path)
        process.setArguments(
            [f"-Xms{config.xms}", f"-Xmx{config.xmx}", "-jar", str(jar_path), "nogui"]
        )
        process.setWorkingDirectory(str(server_dir))
        process.setProcessChannelMode(QProcess.MergedChannels)
        process.readyReadStandardOutput.connect(self._read_output)
        process.started.connect(lambda: self.status_changed.emit("running"))
        process.errorOccurred.connect(lambda error: self.error.emit(f"QProcess error: {error}"))
        process.finished.connect(lambda _code, _status: self.status_changed.emit("stopped"))

        self.process = process
        process.start()
        if not process.waitForStarted(5000):
            raise ServiceError("Не удалось запустить Minecraft-сервер.")

    def stop_server_gracefully(self) -> None:
        """Send the Minecraft stop command."""
        if not self.process or self.process.state() == QProcess.ProcessState.NotRunning:
            self.status_changed.emit("stopped")
            return
        self.send_command("stop")
        self.status_changed.emit("stopping")

    def kill_server(self) -> None:
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
            self.status_changed.emit("killed")

    def send_command(self, command: str) -> None:
        if not self.process or self.process.state() == QProcess.ProcessState.NotRunning:
            raise ServiceError("Minecraft-сервер не запущен.")
        self.process.write(f"{command.strip()}\n".encode())

    def wait_until_port_open(self, port: int, timeout_seconds: float = 30.0) -> bool:
        return wait_until_port_open("127.0.0.1", port, timeout_seconds=timeout_seconds)

    def _read_output(self) -> None:
        if not self.process:
            return
        data = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        for line in data.splitlines():
            self.log_line.emit(line)
