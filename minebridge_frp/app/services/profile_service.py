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
from minebridge_frp.app.models.profile import Profile, ProfileBundle


class ProfileService:
    """High-level profile API used by UI and future services."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.engine = create_sqlite_engine(database_path)
        run_migrations(self.engine)
        self.session_factory = create_session_factory(self.engine)
        self.repository = ProfileRepository(self.session_factory)
        self.ensure_default_profile()

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
