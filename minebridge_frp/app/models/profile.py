"""Pydantic profile models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from minebridge_frp.app.models.minecraft import MinecraftConfig
from minebridge_frp.app.models.tunnel import TunnelConfig
from minebridge_frp.app.models.vps import VpsConfig


class Profile(BaseModel):
    """User profile metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    name: str = Field(default="Профиль по умолчанию", min_length=1, max_length=120)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_default: bool = False


class ProfileBundle(BaseModel):
    """Complete exportable profile with all config blocks."""

    model_config = ConfigDict(from_attributes=True)

    profile: Profile
    vps: VpsConfig = Field(default_factory=VpsConfig)
    minecraft: MinecraftConfig = Field(default_factory=MinecraftConfig)
    tunnel: TunnelConfig = Field(default_factory=TunnelConfig)

    def without_database_ids(self) -> ProfileBundle:
        """Return a copy safe for JSON import into another database."""
        return self.model_copy(
            deep=True,
            update={
                "profile": self.profile.model_copy(update={"id": None}),
                "vps": self.vps.model_copy(update={"id": None, "profile_id": None}),
                "minecraft": self.minecraft.model_copy(update={"id": None, "profile_id": None}),
                "tunnel": self.tunnel.model_copy(update={"id": None, "profile_id": None}),
            },
        )
