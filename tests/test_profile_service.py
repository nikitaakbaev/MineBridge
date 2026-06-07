from __future__ import annotations

from minebridge_frp.app.services.profile_service import ProfileService


def test_profile_service_creates_default_profile(tmp_path):
    service = ProfileService(tmp_path / "profiles.sqlite3")

    profiles = service.list_profiles()

    assert len(profiles) == 1
    assert profiles[0].name == "Профиль по умолчанию"
    assert profiles[0].is_default is True


def test_profile_service_switches_active_profile(tmp_path):
    service = ProfileService(tmp_path / "profiles.sqlite3")
    created = service.create_profile("LAN survival")

    active = service.set_active_profile(created.profile.id)

    assert active.profile.name == "LAN survival"
    assert service.get_active_profile().profile.id == created.profile.id


def test_profile_service_exports_and_imports_profile(tmp_path):
    service = ProfileService(tmp_path / "profiles.sqlite3")
    created = service.create_profile("Paper friends")
    export_path = tmp_path / "paper-friends.json"

    service.export_profile(created.profile.id, export_path)
    imported = service.import_profile(export_path, make_default=True)

    assert imported.profile.id != created.profile.id
    assert imported.profile.name == "Paper friends"
    assert service.get_active_profile().profile.id == imported.profile.id


def test_profile_service_keeps_section_profiles_independent(tmp_path):
    service = ProfileService(tmp_path / "profiles.sqlite3")
    vps = service.create_vps_profile("VPS Москва")
    minecraft = service.create_minecraft_profile("Paper 1.21")
    tunnel = service.create_tunnel_profile("frpc friends")

    service.set_active_vps_profile(vps.profile.id)
    service.set_active_minecraft_profile(minecraft.profile.id)
    service.set_active_tunnel_profile(tunnel.profile.id)

    active = service.get_active_configuration()

    assert service.get_active_vps_profile().profile.name == "VPS Москва"
    assert service.get_active_minecraft_profile().profile.name == "Paper 1.21"
    assert service.get_active_tunnel_profile().profile.name == "frpc friends"
    assert active.vps == service.get_active_vps_profile().config
    assert active.minecraft == service.get_active_minecraft_profile().config
    assert active.tunnel == service.get_active_tunnel_profile().config
