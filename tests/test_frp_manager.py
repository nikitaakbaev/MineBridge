from __future__ import annotations

import tomllib

from minebridge_frp.app.models.tunnel import TunnelConfig
from minebridge_frp.app.services.download_service import DEFAULT_FRP_VERSION, DownloadService
from minebridge_frp.app.services.frp_manager import create_frpc_toml, create_frps_toml
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


def test_create_frps_toml_keeps_dashboard_localhost():
    token = generate_token()
    parsed = tomllib.loads(
        create_frps_toml(
            bind_port=7000,
            token=token,
            dashboard_enabled=True,
            dashboard_port=7500,
            dashboard_password="dashboard-secret",
        )
    )

    assert parsed["bindPort"] == 7000
    assert parsed["auth"]["token"] == token
    assert parsed["webServer"]["addr"] == "127.0.0.1"
    assert parsed["webServer"]["password"] == "dashboard-secret"


def test_create_frps_toml_omits_dashboard_when_disabled():
    token = generate_token()
    parsed = tomllib.loads(create_frps_toml(bind_port=7001, token=token))

    assert parsed == {
        "bindPort": 7001,
        "auth": {
            "method": "token",
            "token": token,
        },
    }


def test_create_frpc_toml_uses_configured_ports_and_token():
    token = generate_token()
    config = TunnelConfig(
        local_ip="192.168.0.10",
        local_port=25570,
        remote_port=25580,
        frp_server_addr="193.0.2.10",
        frp_server_bind_port=7100,
        frp_token=token,
    )

    parsed = tomllib.loads(create_frpc_toml(config))

    assert parsed["serverAddr"] == "193.0.2.10"
    assert parsed["serverPort"] == 7100
    assert parsed["auth"] == {"method": "token", "token": token}
    assert parsed["proxies"] == [
        {
            "name": "minecraft",
            "type": "tcp",
            "localIP": "192.168.0.10",
            "localPort": 25570,
            "remotePort": 25580,
        }
    ]


def test_download_service_uses_pinned_frp_release_by_default(tmp_path, monkeypatch):
    seen: list[str] = []

    class Response:
        status_code = 200

        def json(self) -> dict:
            return {"tag_name": DEFAULT_FRP_VERSION, "assets": []}

    def fake_get(url: str, timeout: int):
        seen.append(url)
        return Response()

    monkeypatch.setattr("minebridge_frp.app.services.download_service.requests.get", fake_get)

    DownloadService(tmp_path)._fetch_release(DEFAULT_FRP_VERSION)

    assert seen == [
        f"https://api.github.com/repos/fatedier/frp/releases/tags/{DEFAULT_FRP_VERSION}"
    ]
