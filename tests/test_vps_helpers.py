from __future__ import annotations

from minebridge_frp.app.models.vps import VpsConfig
from minebridge_frp.app.services.firewall_service import (
    firewall_detection_command,
    firewall_open_port_command,
)
from minebridge_frp.app.services.systemd_service import SERVICE_NAME, create_frps_systemd_unit
from minebridge_frp.app.services.vps_manager import VpsManager


class _FakeChannel:
    def recv_exit_status(self) -> int:
        return 0


class _FakeStream:
    channel = _FakeChannel()

    def __init__(self, text: str = "") -> None:
        self.text = text

    def read(self) -> bytes:
        return self.text.encode("utf-8")


class _FakeTransport:
    def is_active(self) -> bool:
        return True


class _FakeSshClient:
    def __init__(self) -> None:
        self.commands: list[str] = []

    def get_transport(self) -> _FakeTransport:
        return _FakeTransport()

    def exec_command(self, command: str, timeout: float, get_pty: bool):
        self.commands.append(command)
        return _FakeStream(), _FakeStream("ok"), _FakeStream()


class _AutoConnectVpsManager(VpsManager):
    def __init__(self) -> None:
        super().__init__(VpsConfig(host="vps.example.com", username="root"), password="secret")
        self.connect_count = 0
        self.fake_client = _FakeSshClient()

    def connect(self, timeout: float = 15.0) -> None:
        self.connect_count += 1
        self.client = self.fake_client


def test_systemd_unit_uses_minebridge_service_name_and_paths():
    unit = create_frps_systemd_unit("/opt/minebridge-frp")

    assert SERVICE_NAME == "minebridge-frps.service"
    assert "ExecStart=/opt/minebridge-frp/frps -c /opt/minebridge-frp/frps.toml" in unit
    assert "Restart=always" in unit


def test_firewall_open_port_commands_are_specific():
    assert firewall_open_port_command("ufw", 25565) == "ufw allow 25565/tcp"
    assert (
        firewall_open_port_command("firewalld", 25565)
        == "firewall-cmd --permanent --add-port=25565/tcp && firewall-cmd --reload"
    )
    assert firewall_open_port_command("unknown", 25565) is None
    assert "ufw" in firewall_detection_command()


def test_vps_commands_auto_connect_before_exec():
    manager = _AutoConnectVpsManager()

    result = manager.restart_frps()

    assert result.stdout == "ok"
    assert manager.connect_count == 1
    assert manager.fake_client.commands == ["systemctl restart minebridge-frps"]


def test_vps_remote_download_install_uses_github_asset_on_server():
    manager = _AutoConnectVpsManager()

    manager._install_linux_frps_binary_remote_download()

    command = manager.fake_client.commands[0]
    assert "api.github.com/repos/fatedier/frp/releases/latest" in command
    assert "grep linux_amd64" in command
    assert "curl -fL" in command
    assert 'install -m 0755 "$frps_path" "$remote_dir/frps"' in command
