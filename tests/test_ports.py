from __future__ import annotations

import socket

import pytest

from minebridge_frp.app.utils.ports import is_port_open


def test_is_port_open_detects_local_listener():
    try:
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except PermissionError:
        pytest.skip("Socket creation is not permitted in this sandbox")

    with listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]

        assert is_port_open("127.0.0.1", port)
