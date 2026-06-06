"""SQLite database setup and SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


class Base(DeclarativeBase):
    """Declarative base for MineBridge database tables."""


def utc_now() -> datetime:
    return datetime.now(UTC)


class ProfileRecord(Base):
    """Profile table."""

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    vps: Mapped[VpsConfigRecord] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        uselist=False,
    )
    minecraft: Mapped[MinecraftConfigRecord] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        uselist=False,
    )
    tunnel: Mapped[TunnelConfigRecord] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        uselist=False,
    )


class VpsConfigRecord(Base):
    """VPS config table."""

    __tablename__ = "vps_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"), unique=True, nullable=False)
    host: Mapped[str] = mapped_column(String(255), default="")
    ssh_port: Mapped[int] = mapped_column(Integer, default=22)
    username: Mapped[str] = mapped_column(String(120), default="")
    auth_type: Mapped[str] = mapped_column(String(32), default="password")
    password_encrypted: Mapped[str | None] = mapped_column(String(512), nullable=True)
    private_key_path: Mapped[str] = mapped_column(String(1024), default="")
    install_dir: Mapped[str] = mapped_column(String(1024), default="/opt/minebridge-frp")
    frps_bind_port: Mapped[int] = mapped_column(Integer, default=7000)
    dashboard_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    dashboard_port: Mapped[int] = mapped_column(Integer, default=7500)

    profile: Mapped[ProfileRecord] = relationship(back_populates="vps")


class MinecraftConfigRecord(Base):
    """Minecraft config table."""

    __tablename__ = "minecraft_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"), unique=True, nullable=False)
    server_dir: Mapped[str] = mapped_column(String(1024), default="")
    jar_path: Mapped[str] = mapped_column(String(1024), default="")
    java_path: Mapped[str] = mapped_column(String(1024), default="")
    xms: Mapped[str] = mapped_column(String(32), default="2G")
    xmx: Mapped[str] = mapped_column(String(32), default="4G")
    mc_port: Mapped[int] = mapped_column(Integer, default=25565)
    server_type: Mapped[str] = mapped_column(String(32), default="Vanilla")
    mc_version: Mapped[str] = mapped_column(String(64), default="")
    online_mode: Mapped[bool] = mapped_column(Boolean, default=True)
    difficulty: Mapped[str] = mapped_column(String(32), default="normal")
    max_players: Mapped[int] = mapped_column(Integer, default=20)
    motd: Mapped[str] = mapped_column(String(255), default="MineBridge FRP server")
    view_distance: Mapped[int] = mapped_column(Integer, default=10)
    simulation_distance: Mapped[int] = mapped_column(Integer, default=10)

    profile: Mapped[ProfileRecord] = relationship(back_populates="minecraft")


class TunnelConfigRecord(Base):
    """FRP tunnel config table."""

    __tablename__ = "tunnel_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"), unique=True, nullable=False)
    local_ip: Mapped[str] = mapped_column(String(64), default="127.0.0.1")
    local_port: Mapped[int] = mapped_column(Integer, default=25565)
    remote_port: Mapped[int] = mapped_column(Integer, default=25565)
    protocol: Mapped[str] = mapped_column(String(16), default="tcp")
    frp_server_addr: Mapped[str] = mapped_column(String(255), default="")
    frp_server_bind_port: Mapped[int] = mapped_column(Integer, default=7000)
    frp_token: Mapped[str] = mapped_column(String(255), default="")
    auto_start_frpc: Mapped[bool] = mapped_column(Boolean, default=True)

    profile: Mapped[ProfileRecord] = relationship(back_populates="tunnel")


SessionFactory = sessionmaker


def create_sqlite_engine(database_path: Path) -> Engine:
    """Create a SQLite engine for the application database."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )


def create_session_factory(engine: Engine) -> sessionmaker[Any]:
    """Create a configured SQLAlchemy session factory."""
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
