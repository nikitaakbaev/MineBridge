"""Setup wizard state model."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SetupStep = Literal["vps", "tunnel", "server", "done"]


class SetupState(BaseModel):
    """First-run setup wizard state persisted under config_dir."""

    model_config = ConfigDict(from_attributes=True)

    completed: bool = False
    current_step: SetupStep = Field(default="vps")
