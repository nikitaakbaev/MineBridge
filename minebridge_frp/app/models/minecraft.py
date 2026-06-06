"""Pydantic Minecraft server configuration models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MinecraftConfig(BaseModel):
    """Local Minecraft server settings."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    profile_id: int | None = None
    server_dir: str = ""
    jar_path: str = ""
    java_path: str = ""
    xms: str = "2G"
    xmx: str = "4G"
    mc_port: int = Field(default=25565, ge=1, le=65535)
    server_type: Literal["Vanilla", "Paper", "Fabric", "Forge", "NeoForge"] = "Vanilla"
    mc_version: str = ""
    online_mode: bool = True
    difficulty: Literal["peaceful", "easy", "normal", "hard"] = "normal"
    max_players: int = Field(default=20, ge=1, le=500)
    motd: str = "MineBridge FRP server"
    view_distance: int = Field(default=10, ge=2, le=32)
    simulation_distance: int = Field(default=10, ge=2, le=32)
