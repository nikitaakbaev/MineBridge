"""Request and response schemas for the local API."""

from __future__ import annotations

from pydantic import BaseModel, Field

from minebridge_frp.app.models.minecraft import MinecraftConfig
from minebridge_frp.app.models.tunnel import TunnelConfig
from minebridge_frp.app.models.vps import VpsConfig


class ApiMessage(BaseModel):
    message: str


class CommandRequest(BaseModel):
    command: str = Field(min_length=1)


class CommandOutput(BaseModel):
    stdout: str = ""
    stderr: str = ""
    exit_status: int | None = None


class CreateProfileRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class RenameProfileRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class VpsActionRequest(BaseModel):
    password: str = ""


class SaveVpsProfileRequest(BaseModel):
    config: VpsConfig


class SaveMinecraftProfileRequest(BaseModel):
    config: MinecraftConfig


class SaveTunnelProfileRequest(BaseModel):
    config: TunnelConfig
