"""VPS management service using paramiko."""

from __future__ import annotations

import shlex
import tempfile
from dataclasses import dataclass
from pathlib import Path

import paramiko

from minebridge_frp.app.core.exceptions import ConfigurationError, ServiceError
from minebridge_frp.app.models.vps import VpsConfig
from minebridge_frp.app.services.download_service import DownloadService
from minebridge_frp.app.services.firewall_service import (
    firewall_detection_command,
    firewall_open_port_command,
)
from minebridge_frp.app.services.frp_manager import create_frps_toml
from minebridge_frp.app.services.systemd_service import SERVICE_NAME, create_frps_systemd_unit
from minebridge_frp.app.utils.archive import make_executable
from minebridge_frp.app.utils.os_detect import PlatformInfo
from minebridge_frp.app.utils.secrets import generate_token


@dataclass(frozen=True)
class CommandResult:
    """Remote command result."""

    command: str
    exit_status: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.exit_status == 0


class VpsManager:
    """Manage SSH connection and remote FRP server lifecycle."""

    def __init__(
        self,
        config: VpsConfig,
        password: str = "",
        frp_storage_dir: Path | None = None,
    ) -> None:
        self.config = config
        self.password = password
        self.client: paramiko.SSHClient | None = None
        self.frp_storage_dir = frp_storage_dir or (Path.cwd() / ".minebridge-frp" / "frp")

    def connect(self, timeout: float = 15.0) -> None:
        """Open SSH connection."""
        self._validate_connection_config()
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs = {
            "hostname": self.config.host,
            "port": self.config.ssh_port,
            "username": self.config.username,
            "timeout": timeout,
            "banner_timeout": timeout,
            "auth_timeout": timeout,
        }
        if self.config.auth_type == "private_key":
            if not self.config.private_key_path:
                raise ConfigurationError("Укажите путь к private key.")
            connect_kwargs["key_filename"] = self.config.private_key_path
        else:
            connect_kwargs["password"] = self.password
            if not self.password:
                raise ConfigurationError("Введите SSH password.")

        try:
            client.connect(**connect_kwargs)
        except Exception as exc:  # noqa: BLE001 - paramiko raises several connection exceptions.
            raise ServiceError(f"SSH подключение не удалось: {exc}") from exc

        self.client = client

    def close(self) -> None:
        if self.client:
            self.client.close()
            self.client = None

    def check_ssh(self) -> CommandResult:
        self.ensure_connected()
        return self.exec("echo minebridge-ssh-ok")

    def ensure_connected(self) -> None:
        if self.client is None:
            self.connect()

    def exec(self, command: str, sudo: bool = False, timeout: float = 60.0) -> CommandResult:
        """Run a remote shell command."""
        if self.client is None:
            raise ServiceError("SSH не подключён.")

        remote_command = command
        if sudo and self.config.username != "root":
            remote_command = f"sudo -S -p '' sh -lc {shlex.quote(command)}"

        stdin, stdout, stderr = self.client.exec_command(
            remote_command,
            timeout=timeout,
            get_pty=sudo,
        )
        if sudo and self.config.username != "root":
            stdin.write(f"{self.password}\n")
            stdin.flush()

        exit_status = stdout.channel.recv_exit_status()
        result = CommandResult(
            command=command,
            exit_status=exit_status,
            stdout=stdout.read().decode("utf-8", errors="replace"),
            stderr=stderr.read().decode("utf-8", errors="replace"),
        )
        if not result.ok:
            raise ServiceError(
                f"Команда завершилась с ошибкой ({exit_status}): {command}\n{result.stderr}"
            )
        return result

    def upload_file(self, local_path: Path, remote_path: str, sudo: bool = False) -> None:
        """Upload a local file to the remote host."""
        self.ensure_connected()
        if self.client is None:
            raise ServiceError("SSH не подключён.")

        target = remote_path
        upload_target = target
        if sudo and self.config.username != "root":
            upload_target = f"/tmp/minebridge-upload-{Path(target).name}"

        sftp = self.client.open_sftp()
        try:
            sftp.put(str(local_path), upload_target)
        finally:
            sftp.close()

        if sudo and self.config.username != "root":
            self.exec(f"mv {shlex.quote(upload_target)} {shlex.quote(target)}", sudo=True)

    def write_remote_file(self, content: str, remote_path: str, sudo: bool = False) -> None:
        """Write UTF-8 content to a remote path."""
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as file:
            file.write(content)
            temp_path = Path(file.name)
        try:
            self.upload_file(temp_path, remote_path, sudo=sudo)
        finally:
            temp_path.unlink(missing_ok=True)

    def create_frps_config(self, token: str | None = None) -> str:
        """Generate and upload frps.toml."""
        self.ensure_connected()
        token = token or generate_token()
        content = create_frps_toml(
            bind_port=self.config.frps_bind_port,
            token=token,
            dashboard_enabled=self.config.dashboard_enabled,
            dashboard_port=self.config.dashboard_port,
        )
        remote_path = f"{self.config.install_dir.rstrip('/')}/frps.toml"
        self.exec(f"mkdir -p {shlex.quote(self.config.install_dir)}", sudo=True)
        self.write_remote_file(content, remote_path, sudo=True)
        return content

    def install_systemd_service(self) -> None:
        """Upload and enable the minebridge-frps systemd service."""
        self.ensure_connected()
        unit = create_frps_systemd_unit(self.config.install_dir)
        self.write_remote_file(unit, f"/etc/systemd/system/{SERVICE_NAME}", sudo=True)
        self.exec("systemctl daemon-reload", sudo=True)
        self.exec("systemctl enable minebridge-frps", sudo=True)

    def start_frps(self) -> CommandResult:
        return self.exec("systemctl start minebridge-frps", sudo=True)

    def stop_frps(self) -> CommandResult:
        return self.exec("systemctl stop minebridge-frps", sudo=True)

    def restart_frps(self) -> CommandResult:
        return self.exec("systemctl restart minebridge-frps", sudo=True)

    def status_frps(self) -> CommandResult:
        self.ensure_connected()
        if self.client is None:
            raise ServiceError("SSH не подключён.")
        stdin, stdout, stderr = self.client.exec_command(
            "systemctl is-active minebridge-frps && systemctl status minebridge-frps --no-pager -l",
            timeout=30,
        )
        exit_status = stdout.channel.recv_exit_status()
        return CommandResult(
            command="systemctl status minebridge-frps",
            exit_status=exit_status,
            stdout=stdout.read().decode("utf-8", errors="replace"),
            stderr=stderr.read().decode("utf-8", errors="replace"),
        )

    def open_firewall_port(self, port: int | None = None) -> str:
        """Open one TCP port through ufw or firewalld."""
        self.ensure_connected()
        backend = self.exec(firewall_detection_command()).stdout.strip()
        port = port or self.config.frps_bind_port
        command = firewall_open_port_command(backend, port)
        if command is None:
            return (
                "Firewall не распознан. Выполните вручную команду, подходящую для вашей ОС: "
                f"allow TCP port {port}."
            )
        self.exec(command, sudo=True)
        return f"Firewall backend {backend}: открыт TCP порт {port}."

    def install_frps_on_vps(self, token: str) -> None:
        """Install frps binary, config, and systemd service on the VPS."""
        self.ensure_connected()
        binary = self._ensure_linux_frps_binary()
        remote_dir = self.config.install_dir.rstrip("/")
        self.exec(f"mkdir -p {shlex.quote(remote_dir)}", sudo=True)
        self.upload_file(binary, f"{remote_dir}/frps", sudo=True)
        self.exec(f"chmod +x {shlex.quote(remote_dir)}/frps", sudo=True)
        self.create_frps_config(token)
        self.install_systemd_service()
        self.restart_frps()
        status = self.status_frps()
        if not status.ok:
            raise ServiceError(status.stderr or status.stdout or "frps не запущен после установки.")

    def _ensure_linux_frps_binary(self) -> Path:
        storage = self.frp_storage_dir
        platform_info = PlatformInfo(os_name="linux", arch="amd64")
        existing = sorted(storage.rglob("frps"))
        if existing:
            make_executable(existing[-1])
            return existing[-1]

        extracted = DownloadService(storage).download_frp(platform_info=platform_info)
        matches = sorted(extracted.rglob("frps"))
        if not matches:
            raise ServiceError("В скачанном FRP архиве не найден frps.")
        make_executable(matches[-1])
        return matches[-1]

    def _validate_connection_config(self) -> None:
        if not self.config.host:
            raise ConfigurationError("Укажите VPS host.")
        if not self.config.username:
            raise ConfigurationError("Укажите SSH username.")
