"""Secret generation helpers."""

from __future__ import annotations

import secrets
import string

TOKEN_ALPHABET = string.ascii_letters + string.digits


def generate_token(length: int = 48) -> str:
    """Generate a cryptographically secure FRP auth token."""
    if length < 32:
        raise ValueError("Token length must be at least 32 characters")
    return "".join(secrets.choice(TOKEN_ALPHABET) for _ in range(length))
