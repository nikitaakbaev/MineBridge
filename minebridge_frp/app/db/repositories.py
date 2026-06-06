"""Database repositories."""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from minebridge_frp.app.db.database import (
    MinecraftConfigRecord,
    ProfileRecord,
    TunnelConfigRecord,
    VpsConfigRecord,
)
from minebridge_frp.app.models.minecraft import MinecraftConfig
from minebridge_frp.app.models.profile import Profile, ProfileBundle
from minebridge_frp.app.models.tunnel import TunnelConfig
from minebridge_frp.app.models.vps import VpsConfig

SessionFactory = Callable[[], Session]


class ProfileRepository:
    """CRUD operations for profiles and their configuration blocks."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self.session_factory = session_factory

    def list_profiles(self) -> list[Profile]:
        with self.session_factory() as session:
            records = session.scalars(
                select(ProfileRecord).order_by(ProfileRecord.is_default.desc(), ProfileRecord.name)
            ).all()
            return [Profile.model_validate(record) for record in records]

    def get_default_profile(self) -> ProfileBundle | None:
        with self.session_factory() as session:
            record = session.scalar(select(ProfileRecord).where(ProfileRecord.is_default.is_(True)))
            return self._bundle_from_record(record) if record else None

    def get_bundle(self, profile_id: int) -> ProfileBundle | None:
        with self.session_factory() as session:
            record = session.get(ProfileRecord, profile_id)
            return self._bundle_from_record(record) if record else None

    def create_profile(self, name: str, is_default: bool = False) -> ProfileBundle:
        bundle = ProfileBundle(profile=Profile(name=name, is_default=is_default))
        return self.create_bundle(bundle, make_default=is_default)

    def create_bundle(self, bundle: ProfileBundle, make_default: bool = False) -> ProfileBundle:
        clean_bundle = bundle.without_database_ids()
        with self.session_factory() as session:
            if make_default or clean_bundle.profile.is_default:
                self._clear_default(session)

            record = ProfileRecord(
                name=clean_bundle.profile.name,
                is_default=make_default or clean_bundle.profile.is_default,
            )
            record.vps = VpsConfigRecord(
                **clean_bundle.vps.model_dump(exclude={"id", "profile_id"})
            )
            record.minecraft = MinecraftConfigRecord(
                **clean_bundle.minecraft.model_dump(exclude={"id", "profile_id"})
            )
            record.tunnel = TunnelConfigRecord(
                **clean_bundle.tunnel.model_dump(exclude={"id", "profile_id"})
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._bundle_from_record(record)

    def save_bundle(self, bundle: ProfileBundle) -> ProfileBundle:
        if bundle.profile.id is None:
            return self.create_bundle(bundle, make_default=bundle.profile.is_default)

        with self.session_factory() as session:
            record = session.get(ProfileRecord, bundle.profile.id)
            if record is None:
                return self.create_bundle(bundle, make_default=bundle.profile.is_default)

            if bundle.profile.is_default:
                self._clear_default(session)

            record.name = bundle.profile.name
            record.is_default = bundle.profile.is_default
            self._update_record(record.vps, bundle.vps, {"id", "profile_id"})
            self._update_record(record.minecraft, bundle.minecraft, {"id", "profile_id"})
            self._update_record(record.tunnel, bundle.tunnel, {"id", "profile_id"})

            session.commit()
            session.refresh(record)
            return self._bundle_from_record(record)

    def set_default_profile(self, profile_id: int) -> ProfileBundle | None:
        with self.session_factory() as session:
            record = session.get(ProfileRecord, profile_id)
            if record is None:
                return None

            self._clear_default(session)
            record.is_default = True
            session.commit()
            session.refresh(record)
            return self._bundle_from_record(record)

    def count_profiles(self) -> int:
        with self.session_factory() as session:
            return len(session.scalars(select(ProfileRecord.id)).all())

    def _clear_default(self, session: Session) -> None:
        session.execute(update(ProfileRecord).values(is_default=False))

    def _bundle_from_record(self, record: ProfileRecord) -> ProfileBundle:
        return ProfileBundle(
            profile=Profile.model_validate(record),
            vps=VpsConfig.model_validate(record.vps),
            minecraft=MinecraftConfig.model_validate(record.minecraft),
            tunnel=TunnelConfig.model_validate(record.tunnel),
        )

    def _update_record(self, record: object, model: object, exclude: set[str]) -> None:
        for key, value in model.model_dump(exclude=exclude).items():
            setattr(record, key, value)
