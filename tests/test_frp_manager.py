from __future__ import annotations

import tomllib

from minebridge_frp.app.models.tunnel import TunnelConfig
from minebridge_frp.app.services.frp_manager import create_frpc_toml
from minebridge_frp.app.utils.secrets import generate_token


def test_create_frpc_toml_contains_minecraft_proxy():
    token = generate_token()
    config = TunnelConfig(
        local_ip="127.0.0.1",
        local_port=25565,
        remote_port=25566,
        frp_server_addr="vps.example.com",
        frp_server_bind_port=7000,
        frp_token=token,
    )

    parsed = tomllib.loads(create_frpc_toml(config))

    assert parsed["serverAddr"] == "vps.example.com"
    assert parsed["auth"]["token"] == token
    assert parsed["proxies"][0]["name"] == "minecraft"
    assert parsed["proxies"][0]["remotePort"] == 25566


def test_generate_token_is_at_least_32_chars():
    token = generate_token()

    assert len(token) >= 32
    assert token.isalnum()
