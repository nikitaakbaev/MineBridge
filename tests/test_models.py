from __future__ import annotations

import pytest
from pydantic import ValidationError

from minebridge_frp.app.models.minecraft import MinecraftConfig
from minebridge_frp.app.models.profile import Profile, ProfileBundle
from minebridge_frp.app.models.tunnel import TunnelConfig
from minebridge_frp.app.models.vps import VpsConfig
from minebridge_frp.app.utils.secrets import generate_token


def test_tunnel_config_rejects_short_token():
    with pytest.raises(ValidationError):
        TunnelConfig(frp_token="too-short")


def test_tunnel_config_rejects_invalid_ports():
    token = generate_token()

    with pytest.raises(ValidationError):
        TunnelConfig(local_port=0, frp_token=token)

    with pytest.raises(ValidationError):
        TunnelConfig(remote_port=65536, frp_token=token)


def test_vps_config_validates_ports_and_auth_type():
    with pytest.raises(ValidationError):
        VpsConfig(ssh_port=0)

    with pytest.raises(ValidationError):
        VpsConfig(frps_bind_port=65536)

    with pytest.raises(ValidationError):
        VpsConfig(auth_type="ssh-agent")


def test_minecraft_config_defaults_match_server_profile():
    config = MinecraftConfig()

    assert config.mc_port == 25565
    assert config.online_mode is True
    assert config.difficulty == "normal"
    assert config.max_players == 20
    assert config.server_type == "Vanilla"


def test_profile_bundle_without_database_ids_clears_nested_ids():
    bundle = ProfileBundle(
        profile=Profile(id=1, name="Survival"),
        vps=VpsConfig(id=2, profile_id=1),
        minecraft=MinecraftConfig(id=3, profile_id=1),
        tunnel=TunnelConfig(id=4, profile_id=1, frp_token=generate_token()),
    )

    exported = bundle.without_database_ids()

    assert exported.profile.id is None
    assert exported.vps.id is None
    assert exported.vps.profile_id is None
    assert exported.minecraft.id is None
    assert exported.minecraft.profile_id is None
    assert exported.tunnel.id is None
    assert exported.tunnel.profile_id is None
