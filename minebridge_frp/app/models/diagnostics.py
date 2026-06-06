"""Pydantic diagnostics models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

DiagnosticStatus = Literal["OK", "WARNING", "ERROR"]


class DiagnosticResult(BaseModel):
    """Single diagnostic check result."""

    status: DiagnosticStatus
    name: str
    description: str
    fix_available: bool = False
