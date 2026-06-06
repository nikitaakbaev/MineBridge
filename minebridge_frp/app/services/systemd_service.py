"""systemd unit generation helpers."""

from __future__ import annotations

SERVICE_NAME = "minebridge-frps.service"


def create_frps_systemd_unit(install_dir: str) -> str:
    """Create minebridge-frps.service unit text."""
    install_dir = install_dir.rstrip("/")
    return f"""[Unit]
Description=MineBridge FRP Server
After=network.target

[Service]
Type=simple
ExecStart={install_dir}/frps -c {install_dir}/frps.toml
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
"""
