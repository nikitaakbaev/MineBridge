"""Local FRP client manager."""

from __future__ import annotations

from pathlib import Path

import tomlkit

from minebridge_frp.app.core.exceptions import ConfigurationError, ServiceError
from minebridge_frp.app.models.tunnel import TunnelConfig
from minebridge_frp.app.services.download_service import DownloadService
from minebridge_frp.app.services.events import CallbackSignal
from minebridge_frp.app.services.process_runner import ProcessRunner
from minebridge_frp.app.utils.bundled_assets import bundled_frp_root
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


class FrpManager:
    """Manage local frpc configuration, download, and process lifecycle."""

    def __init__(self, storage_dir: Path) -> None:
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.download_service = DownloadService(storage_dir)
        self.log_line = CallbackSignal[[str]]()
        self.status_changed = CallbackSignal[[str]]()
        self.error = CallbackSignal[[str]]()
        self.process = ProcessRunner()
        self.process.output.connect(self.log_line.emit)
        self.process.started.connect(lambda: self.status_changed.emit("running"))
        self.process.finished.connect(lambda _code: self.status_changed.emit("stopped"))
        self.process.error.connect(self.error.emit)

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
        bundled = self._bundled_frpc_binary()
        if bundled is not None:
            return bundled
        extract_dir = self.download_service.download_frp(version=version)
        binary = self.find_frpc_binary(extract_dir)
        if binary is None:
            raise ServiceError("После распаковки FRP бинарник frpc не найден.")
        return binary

    def find_frpc_binary(self, search_dir: Path | None = None) -> Path | None:
        platform_info = detect_platform()
        base = search_dir or self.storage_dir
        candidates = sorted(base.rglob(platform_info.frpc_binary_name))
        if candidates:
            return candidates[-1]
        return self._bundled_frpc_binary()

    def _bundled_frpc_binary(self) -> Path | None:
        platform_info = detect_platform()
        candidate = (
            bundled_frp_root() / platform_info.frp_asset_suffix / platform_info.frpc_binary_name
        )
        if candidate.exists():
            return candidate
        return None

    def start_frpc(self, config_path: Path, binary_path: Path | None = None) -> None:
        if self.process.is_running:
            raise ServiceError("frpc уже запущен.")

        binary = binary_path or self.find_frpc_binary()
        if binary is None or not binary.exists():
            raise ConfigurationError("frpc не найден. Скачайте frpc или укажите бинарник.")
        if not config_path.exists():
            raise ConfigurationError("frpc.toml не найден. Сначала создайте конфиг.")

        self.process.start(binary, ["-c", str(config_path)], working_directory=config_path.parent)

    def stop_frpc(self) -> None:
        if not self.process.is_running:
            self.status_changed.emit("stopped")
            return
        self.process.terminate(timeout_seconds=3.0)
        self.status_changed.emit("stopped")

    def check_external_port(self, host: str, port: int) -> bool:
        return is_port_open(host, port, timeout=3.0)

    def _validate_config_for_file(self, config: TunnelConfig) -> None:
        if not config.frp_server_addr:
            raise ConfigurationError("Укажите адрес FRP/VPS сервера.")
        if not config.frp_token:
            raise ConfigurationError("Сгенерируйте или укажите FRP token.")
