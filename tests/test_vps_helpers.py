from __future__ import annotations

from minebridge_frp.app.services.firewall_service import (
    firewall_detection_command,
    firewall_open_port_command,
)
from minebridge_frp.app.services.systemd_service import SERVICE_NAME, create_frps_systemd_unit


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
