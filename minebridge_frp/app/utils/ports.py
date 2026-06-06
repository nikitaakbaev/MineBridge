"""Port utilities."""

from __future__ import annotations

import socket
import time


def is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """Return True if a TCP connection can be opened."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def is_local_port_listening(port: int, host: str = "127.0.0.1") -> bool:
    """Return True if a local TCP port accepts connections."""
    return is_port_open(host, port, timeout=0.5)


def wait_until_port_open(host: str, port: int, timeout_seconds: float = 30.0) -> bool:
    """Poll until a port starts accepting TCP connections."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if is_port_open(host, port, timeout=0.5):
            return True
        time.sleep(0.25)
    return False
