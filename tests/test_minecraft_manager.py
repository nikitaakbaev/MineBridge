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


def test_server_properties_round_trip_preserves_values():
    values = {
        "server-port": 25565,
        "online-mode": False,
        "difficulty": "hard",
        "max-players": 12,
        "motd": "Friends only",
    }

    reparsed = parse_server_properties(format_server_properties(values))

    assert reparsed == {
        "server-port": "25565",
        "online-mode": "false",
        "difficulty": "hard",
        "max-players": "12",
        "motd": "Friends only",
    }


def test_parse_server_properties_keeps_values_with_equals():
    text = "motd=MineBridge=FRP\nserver-port=25565\n"

    assert parse_server_properties(text)["motd"] == "MineBridge=FRP"
