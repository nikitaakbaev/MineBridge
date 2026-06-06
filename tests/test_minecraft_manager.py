from __future__ import annotations

from minebridge_frp.app.services.minecraft_manager import (
    format_server_properties,
    parse_server_properties,
)


def test_parse_server_properties_ignores_comments():
    text = """
    # comment
    server-port=25565
    online-mode=true
    motd=MineBridge FRP server
    """

    assert parse_server_properties(text) == {
        "server-port": "25565",
        "online-mode": "true",
        "motd": "MineBridge FRP server",
    }


def test_format_server_properties_formats_booleans_lowercase():
    text = format_server_properties({"online-mode": True, "server-port": 25565})

    assert "online-mode=true" in text
    assert "server-port=25565" in text
