"""Remote firewall command helpers."""

from __future__ import annotations


def firewall_detection_command() -> str:
    """Return shell code that prints the supported firewall backend."""
    return (
        "if command -v ufw >/dev/null 2>&1; then echo ufw; "
        "elif command -v firewall-cmd >/dev/null 2>&1; then echo firewalld; "
        "else echo unknown; fi"
    )


def firewall_open_port_command(backend: str, port: int, protocol: str = "tcp") -> str | None:
    """Return a safe command to open a single port for a known firewall backend."""
    if backend == "ufw":
        return f"ufw allow {port}/{protocol}"
    if backend == "firewalld":
        return f"firewall-cmd --permanent --add-port={port}/{protocol} && firewall-cmd --reload"
    return None
