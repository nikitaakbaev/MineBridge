"""Pydantic FRP tunnel configuration models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TunnelConfig(BaseModel):
    """Local frpc tunnel settings."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    profile_id: int | None = None
    local_ip: str = "127.0.0.1"
    local_port: int = Field(default=25565, ge=1, le=65535)
    remote_port: int = Field(default=25565, ge=1, le=65535)
    protocol: Literal["tcp"] = "tcp"
    frp_server_addr: str = ""
    frp_server_bind_port: int = Field(default=7000, ge=1, le=65535)
    frp_token: str = ""
    auto_start_frpc: bool = True

    @field_validator("frp_token")
    @classmethod
    def validate_token_length(cls, value: str) -> str:
        if value and len(value) < 32:
            raise ValueError("FRP token must be at least 32 characters when set")
        return value
