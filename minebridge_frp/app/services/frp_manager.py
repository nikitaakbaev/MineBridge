"""Local FRP client manager."""

from __future__ import annotations

from pathlib import Path

import tomlkit
from PySide6.QtCore import QObject, QProcess, Signal

from minebridge_frp.app.core.exceptions import ConfigurationError, ServiceError
from minebridge_frp.app.models.tunnel import TunnelConfig
from minebridge_frp.app.services.download_service import DownloadService
from minebridge_frp.app.utils.os_detect import detect_platform
from minebridge_frp.app.utils.ports import is_port_open
from minebridge_frp.app.utils.secrets import generate_token


def create_frps_toml(
    bind_port: int,
    token: str,
    dashboard_enabled: bool = False,
    dashboard_port: int = 7500,
    dashboard_user: str = "admin",
    dashboard_password: str = "",
) -> str:
    """Create frps.toml text for the remote VPS side."""
    document = tomlkit.document()
    document.add("bindPort", bind_port)

    auth = tomlkit.table()
    auth.add("method", "token")
    auth.add("token", token)
    document.add("auth", auth)

    if dashboard_enabled:
        web_server = tomlkit.table()
        web_server.add("addr", "127.0.0.1")
        web_server.add("port", dashboard_port)
        web_server.add("user", dashboard_user)
        web_server.add("password", dashboard_password or generate_token(32))
        document.add("webServer", web_server)

    return tomlkit.dumps(document)


def create_frpc_toml(config: TunnelConfig) -> str:
    """Create frpc.toml text for a Minecraft TCP tunnel."""
    document = tomlkit.document()
    document.add("serverAddr", config.frp_server_addr)
    document.add("serverPort", config.frp_server_bind_port)

    auth = tomlkit.table()
    auth.add("method", "token")
    auth.add("token", config.frp_token)
    document.add("auth", auth)

    proxy = tomlkit.table()
    proxy.add("name", "minecraft")
    proxy.add("type", config.protocol)
    proxy.add("localIP", config.local_ip)
    proxy.add("localPort", config.local_port)
    proxy.add("remotePort", config.remote_port)

    proxies = tomlkit.aot()
    proxies.append(proxy)
    document.add("proxies", proxies)
    return tomlkit.dumps(document)


class FrpManager(QObject):
    """Manage local frpc configuration, download, and process lifecycle."""

    log_line = Signal(str)
    status_changed = Signal(str)
    error = Signal(str)

    def __init__(self, storage_dir: Path) -> None:
        super().__init__()
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.download_service = DownloadService(storage_dir)
        self.process: QProcess | None = None

    def generate_token(self) -> str:
        return generate_token()

    def write_frpc_config(self, config: TunnelConfig, profile_name: str = "default") -> Path:
        self._validate_config_for_file(config)
        profile_dir = self.storage_dir / "profiles" / profile_name
        profile_dir.mkdir(parents=True, exist_ok=True)
        path = profile_dir / "frpc.toml"
        path.write_text(create_frpc_toml(config), encoding="utf-8")
        return path

    def download_frpc(self, version: str | None = None) -> Path:
        extract_dir = self.download_service.download_frp(version=version)
        binary = self.find_frpc_binary(extract_dir)
        if binary is None:
            raise ServiceError("После распаковки FRP бинарник frpc не найден.")
        return binary

    def find_frpc_binary(self, search_dir: Path | None = None) -> Path | None:
        platform_info = detect_platform()
        base = search_dir or self.storage_dir
        candidates = sorted(base.rglob(platform_info.frpc_binary_name))
        return candidates[-1] if candidates else None

    def start_frpc(self, config_path: Path, binary_path: Path | None = None) -> None:
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            raise ServiceError("frpc уже запущен.")

        binary = binary_path or self.find_frpc_binary()
        if binary is None or not binary.exists():
            raise ConfigurationError("frpc не найден. Скачайте frpc или укажите бинарник.")
        if not config_path.exists():
            raise ConfigurationError("frpc.toml не найден. Сначала создайте конфиг.")

        process = QProcess(self)
        process.setProgram(str(binary))
        process.setArguments(["-c", str(config_path)])
        process.setWorkingDirectory(str(config_path.parent))
        process.setProcessChannelMode(QProcess.MergedChannels)
        process.readyReadStandardOutput.connect(self._read_output)
        process.started.connect(lambda: self.status_changed.emit("running"))
        process.errorOccurred.connect(lambda error: self.error.emit(f"QProcess error: {error}"))
        process.finished.connect(lambda _code, _status: self.status_changed.emit("stopped"))

        self.process = process
        process.start()
        if not process.waitForStarted(5000):
            raise ServiceError("Не удалось запустить frpc.")

    def stop_frpc(self) -> None:
        if not self.process or self.process.state() == QProcess.ProcessState.NotRunning:
            self.status_changed.emit("stopped")
            return
        self.process.terminate()
        if not self.process.waitForFinished(3000):
            self.process.kill()
        self.status_changed.emit("stopped")

    def check_external_port(self, host: str, port: int) -> bool:
        return is_port_open(host, port, timeout=3.0)

    def _validate_config_for_file(self, config: TunnelConfig) -> None:
        if not config.frp_server_addr:
            raise ConfigurationError("Укажите адрес FRP/VPS сервера.")
        if not config.frp_token:
            raise ConfigurationError("Сгенерируйте или укажите FRP token.")

    def _read_output(self) -> None:
        if not self.process:
            return
        data = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        for line in data.splitlines():
            self.log_line.emit(line)
