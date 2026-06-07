"""Profile persistence and import/export service."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from minebridge_frp.app.core.app_context import AppContext
from minebridge_frp.app.core.exceptions import ConfigurationError
from minebridge_frp.app.db.database import create_session_factory, create_sqlite_engine
from minebridge_frp.app.db.migrations import run_migrations
from minebridge_frp.app.db.repositories import ProfileRepository
from minebridge_frp.app.models.profile import (
    MinecraftProfileBundle,
    Profile,
    ProfileBundle,
    TunnelProfileBundle,
    VpsProfileBundle,
)


class ProfileService:
    """High-level profile API used by UI and future services."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.engine = create_sqlite_engine(database_path)
        run_migrations(self.engine)
        self.session_factory = create_session_factory(self.engine)
        self.repository = ProfileRepository(self.session_factory)
        self.ensure_default_profile()
        self.ensure_default_section_profiles()

    @classmethod
    def from_context(cls, context: AppContext) -> ProfileService:
        return cls(context.database_path)

    def ensure_default_profile(self) -> ProfileBundle:
        default = self.repository.get_default_profile()
        if default is not None:
            return default

        if self.repository.count_profiles() == 0:
            return self.repository.create_profile("Профиль по умолчанию", is_default=True)

        profiles = self.repository.list_profiles()
        updated = self.repository.set_default_profile(profiles[0].id)
        if updated is None:
            raise ConfigurationError("Не удалось выбрать профиль по умолчанию")
        return updated

    def ensure_default_section_profiles(self) -> None:
        legacy = self.get_active_profile()
        if self.repository.get_default_vps_profile() is None:
            self.repository.create_vps_profile(
                legacy.profile.name,
                legacy.vps,
                is_default=True,
            )
        if self.repository.get_default_minecraft_profile() is None:
            self.repository.create_minecraft_profile(
                legacy.profile.name,
                legacy.minecraft,
                is_default=True,
            )
        if self.repository.get_default_tunnel_profile() is None:
            self.repository.create_tunnel_profile(
                legacy.profile.name,
                legacy.tunnel,
                is_default=True,
            )

    def list_profiles(self) -> list[Profile]:
        return self.repository.list_profiles()

    def get_active_profile(self) -> ProfileBundle:
        bundle = self.repository.get_default_profile()
        if bundle is None:
            return self.ensure_default_profile()
        return bundle

    def get_profile(self, profile_id: int) -> ProfileBundle:
        bundle = self.repository.get_bundle(profile_id)
        if bundle is None:
            raise ConfigurationError(f"Профиль с id={profile_id} не найден")
        return bundle

    def create_profile(self, name: str) -> ProfileBundle:
        if not name.strip():
            raise ConfigurationError("Название профиля не может быть пустым")
        return self.repository.create_profile(name.strip(), is_default=False)

    def set_active_profile(self, profile_id: int) -> ProfileBundle:
        bundle = self.repository.set_default_profile(profile_id)
        if bundle is None:
            raise ConfigurationError(f"Профиль с id={profile_id} не найден")
        return bundle

    def save_profile(self, bundle: ProfileBundle) -> ProfileBundle:
        return self.repository.save_bundle(bundle)

    def get_active_configuration(self) -> ProfileBundle:
        legacy = self.get_active_profile()
        return ProfileBundle(
            profile=legacy.profile,
            vps=self.get_active_vps_profile().config,
            minecraft=self.get_active_minecraft_profile().config,
            tunnel=self.get_active_tunnel_profile().config,
        )

    def list_vps_profiles(self) -> list[Profile]:
        return self.repository.list_vps_profiles()

    def get_active_vps_profile(self) -> VpsProfileBundle:
        bundle = self.repository.get_default_vps_profile()
        if bundle is None:
            legacy = self.get_active_profile()
            return self.repository.create_vps_profile(
                legacy.profile.name,
                legacy.vps,
                is_default=True,
            )
        return bundle

    def create_vps_profile(self, name: str) -> VpsProfileBundle:
        if not name.strip():
            raise ConfigurationError("Название VPS-профиля не может быть пустым")
        return self.repository.create_vps_profile(name.strip())

    def set_active_vps_profile(self, profile_id: int) -> VpsProfileBundle:
        bundle = self.repository.set_default_vps_profile(profile_id)
        if bundle is None:
            raise ConfigurationError(f"VPS-профиль с id={profile_id} не найден")
        return bundle

    def save_vps_profile(self, bundle: VpsProfileBundle) -> VpsProfileBundle:
        return self.repository.save_vps_profile(bundle)

    def list_minecraft_profiles(self) -> list[Profile]:
        return self.repository.list_minecraft_profiles()

    def get_active_minecraft_profile(self) -> MinecraftProfileBundle:
        bundle = self.repository.get_default_minecraft_profile()
        if bundle is None:
            legacy = self.get_active_profile()
            return self.repository.create_minecraft_profile(
                legacy.profile.name,
                legacy.minecraft,
                is_default=True,
            )
        return bundle

    def create_minecraft_profile(self, name: str) -> MinecraftProfileBundle:
        if not name.strip():
            raise ConfigurationError("Название Minecraft-профиля не может быть пустым")
        return self.repository.create_minecraft_profile(name.strip())

    def set_active_minecraft_profile(self, profile_id: int) -> MinecraftProfileBundle:
        bundle = self.repository.set_default_minecraft_profile(profile_id)
        if bundle is None:
            raise ConfigurationError(f"Minecraft-профиль с id={profile_id} не найден")
        return bundle

    def save_minecraft_profile(
        self,
        bundle: MinecraftProfileBundle,
    ) -> MinecraftProfileBundle:
        return self.repository.save_minecraft_profile(bundle)

    def list_tunnel_profiles(self) -> list[Profile]:
        return self.repository.list_tunnel_profiles()

    def get_active_tunnel_profile(self) -> TunnelProfileBundle:
        bundle = self.repository.get_default_tunnel_profile()
        if bundle is None:
            legacy = self.get_active_profile()
            return self.repository.create_tunnel_profile(
                legacy.profile.name,
                legacy.tunnel,
                is_default=True,
            )
        return bundle

    def create_tunnel_profile(self, name: str) -> TunnelProfileBundle:
        if not name.strip():
            raise ConfigurationError("Название frpc-профиля не может быть пустым")
        return self.repository.create_tunnel_profile(name.strip())

    def set_active_tunnel_profile(self, profile_id: int) -> TunnelProfileBundle:
        bundle = self.repository.set_default_tunnel_profile(profile_id)
        if bundle is None:
            raise ConfigurationError(f"frpc-профиль с id={profile_id} не найден")
        return bundle

    def save_tunnel_profile(self, bundle: TunnelProfileBundle) -> TunnelProfileBundle:
        return self.repository.save_tunnel_profile(bundle)

    def export_profile(self, profile_id: int, path: Path) -> Path:
        bundle = self.get_profile(profile_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            bundle.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return path

    def import_profile(self, path: Path, make_default: bool = True) -> ProfileBundle:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            bundle = ProfileBundle.model_validate(payload).without_database_ids()
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            raise ConfigurationError(f"Не удалось импортировать профиль: {exc}") from exc

        if make_default:
            bundle.profile.is_default = True
        return self.repository.create_bundle(bundle, make_default=make_default)
