"""Pydantic VPS configuration models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class VpsConfig(BaseModel):
    """SSH and remote FRP server settings."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    profile_id: int | None = None
    host: str = ""
    ssh_port: int = Field(default=22, ge=1, le=65535)
    username: str = ""
    auth_type: Literal["password", "private_key"] = "password"
    password_encrypted: str | None = None
    private_key_path: str = ""
    install_dir: str = "/opt/minebridge-frp"
    frps_bind_port: int = Field(default=7000, ge=1, le=65535)
    dashboard_enabled: bool = False
    dashboard_port: int = Field(default=7500, ge=1, le=65535)
