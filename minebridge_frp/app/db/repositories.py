"""Database repositories."""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from minebridge_frp.app.db.database import (
    MinecraftConfigRecord,
    MinecraftProfileRecord,
    ProfileRecord,
    TunnelConfigRecord,
    TunnelProfileRecord,
    VpsConfigRecord,
    VpsProfileRecord,
)
from minebridge_frp.app.models.minecraft import MinecraftConfig
from minebridge_frp.app.models.profile import (
    MinecraftProfileBundle,
    Profile,
    ProfileBundle,
    TunnelProfileBundle,
    VpsProfileBundle,
)
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

    def list_vps_profiles(self) -> list[Profile]:
        return self._list_section_profiles(VpsProfileRecord)

    def get_default_vps_profile(self) -> VpsProfileBundle | None:
        with self.session_factory() as session:
            record = session.scalar(
                select(VpsProfileRecord).where(VpsProfileRecord.is_default.is_(True))
            )
            return self._vps_profile_from_record(record) if record else None

    def create_vps_profile(
        self,
        name: str,
        config: VpsConfig | None = None,
        is_default: bool = False,
    ) -> VpsProfileBundle:
        with self.session_factory() as session:
            if is_default:
                self._clear_section_default(session, VpsProfileRecord)
            record = VpsProfileRecord(
                name=name,
                is_default=is_default,
                **(config or VpsConfig()).model_dump(exclude={"id", "profile_id"}),
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._vps_profile_from_record(record)

    def set_default_vps_profile(self, profile_id: int) -> VpsProfileBundle | None:
        with self.session_factory() as session:
            record = session.get(VpsProfileRecord, profile_id)
            if record is None:
                return None
            self._clear_section_default(session, VpsProfileRecord)
            record.is_default = True
            session.commit()
            session.refresh(record)
            return self._vps_profile_from_record(record)

    def save_vps_profile(self, bundle: VpsProfileBundle) -> VpsProfileBundle:
        with self.session_factory() as session:
            record = session.get(VpsProfileRecord, bundle.profile.id)
            if record is None:
                return self.create_vps_profile(
                    bundle.profile.name,
                    bundle.config,
                    bundle.profile.is_default,
                )
            if bundle.profile.is_default:
                self._clear_section_default(session, VpsProfileRecord)
            record.name = bundle.profile.name
            record.is_default = bundle.profile.is_default
            self._update_record(record, bundle.config, {"id", "profile_id"})
            session.commit()
            session.refresh(record)
            return self._vps_profile_from_record(record)

    def list_minecraft_profiles(self) -> list[Profile]:
        return self._list_section_profiles(MinecraftProfileRecord)

    def get_default_minecraft_profile(self) -> MinecraftProfileBundle | None:
        with self.session_factory() as session:
            record = session.scalar(
                select(MinecraftProfileRecord).where(
                    MinecraftProfileRecord.is_default.is_(True)
                )
            )
            return self._minecraft_profile_from_record(record) if record else None

    def create_minecraft_profile(
        self,
        name: str,
        config: MinecraftConfig | None = None,
        is_default: bool = False,
    ) -> MinecraftProfileBundle:
        with self.session_factory() as session:
            if is_default:
                self._clear_section_default(session, MinecraftProfileRecord)
            record = MinecraftProfileRecord(
                name=name,
                is_default=is_default,
                **(config or MinecraftConfig()).model_dump(exclude={"id", "profile_id"}),
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._minecraft_profile_from_record(record)

    def set_default_minecraft_profile(self, profile_id: int) -> MinecraftProfileBundle | None:
        with self.session_factory() as session:
            record = session.get(MinecraftProfileRecord, profile_id)
            if record is None:
                return None
            self._clear_section_default(session, MinecraftProfileRecord)
            record.is_default = True
            session.commit()
            session.refresh(record)
            return self._minecraft_profile_from_record(record)

    def save_minecraft_profile(self, bundle: MinecraftProfileBundle) -> MinecraftProfileBundle:
        with self.session_factory() as session:
            record = session.get(MinecraftProfileRecord, bundle.profile.id)
            if record is None:
                return self.create_minecraft_profile(
                    bundle.profile.name,
                    bundle.config,
                    bundle.profile.is_default,
                )
            if bundle.profile.is_default:
                self._clear_section_default(session, MinecraftProfileRecord)
            record.name = bundle.profile.name
            record.is_default = bundle.profile.is_default
            self._update_record(record, bundle.config, {"id", "profile_id"})
            session.commit()
            session.refresh(record)
            return self._minecraft_profile_from_record(record)

    def list_tunnel_profiles(self) -> list[Profile]:
        return self._list_section_profiles(TunnelProfileRecord)

    def get_default_tunnel_profile(self) -> TunnelProfileBundle | None:
        with self.session_factory() as session:
            record = session.scalar(
                select(TunnelProfileRecord).where(TunnelProfileRecord.is_default.is_(True))
            )
            return self._tunnel_profile_from_record(record) if record else None

    def create_tunnel_profile(
        self,
        name: str,
        config: TunnelConfig | None = None,
        is_default: bool = False,
    ) -> TunnelProfileBundle:
        with self.session_factory() as session:
            if is_default:
                self._clear_section_default(session, TunnelProfileRecord)
            record = TunnelProfileRecord(
                name=name,
                is_default=is_default,
                **(config or TunnelConfig()).model_dump(exclude={"id", "profile_id"}),
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._tunnel_profile_from_record(record)

    def set_default_tunnel_profile(self, profile_id: int) -> TunnelProfileBundle | None:
        with self.session_factory() as session:
            record = session.get(TunnelProfileRecord, profile_id)
            if record is None:
                return None
            self._clear_section_default(session, TunnelProfileRecord)
            record.is_default = True
            session.commit()
            session.refresh(record)
            return self._tunnel_profile_from_record(record)

    def save_tunnel_profile(self, bundle: TunnelProfileBundle) -> TunnelProfileBundle:
        with self.session_factory() as session:
            record = session.get(TunnelProfileRecord, bundle.profile.id)
            if record is None:
                return self.create_tunnel_profile(
                    bundle.profile.name,
                    bundle.config,
                    bundle.profile.is_default,
                )
            if bundle.profile.is_default:
                self._clear_section_default(session, TunnelProfileRecord)
            record.name = bundle.profile.name
            record.is_default = bundle.profile.is_default
            self._update_record(record, bundle.config, {"id", "profile_id"})
            session.commit()
            session.refresh(record)
            return self._tunnel_profile_from_record(record)

    def _clear_default(self, session: Session) -> None:
        session.execute(update(ProfileRecord).values(is_default=False))

    def _clear_section_default(self, session: Session, record_type: type) -> None:
        session.execute(update(record_type).values(is_default=False))

    def _list_section_profiles(self, record_type: type) -> list[Profile]:
        with self.session_factory() as session:
            records = session.scalars(
                select(record_type).order_by(record_type.is_default.desc(), record_type.name)
            ).all()
            return [Profile.model_validate(record) for record in records]

    def _bundle_from_record(self, record: ProfileRecord) -> ProfileBundle:
        return ProfileBundle(
            profile=Profile.model_validate(record),
            vps=VpsConfig.model_validate(record.vps),
            minecraft=MinecraftConfig.model_validate(record.minecraft),
            tunnel=TunnelConfig.model_validate(record.tunnel),
        )

    def _vps_profile_from_record(self, record: VpsProfileRecord) -> VpsProfileBundle:
        return VpsProfileBundle(
            profile=Profile.model_validate(record),
            config=VpsConfig.model_validate(record),
        )

    def _minecraft_profile_from_record(
        self,
        record: MinecraftProfileRecord,
    ) -> MinecraftProfileBundle:
        return MinecraftProfileBundle(
            profile=Profile.model_validate(record),
            config=MinecraftConfig.model_validate(record),
        )

    def _tunnel_profile_from_record(self, record: TunnelProfileRecord) -> TunnelProfileBundle:
        return TunnelProfileBundle(
            profile=Profile.model_validate(record),
            config=TunnelConfig.model_validate(record),
        )

    def _update_record(self, record: object, model: object, exclude: set[str]) -> None:
        for key, value in model.model_dump(exclude=exclude).items():
            setattr(record, key, value)
