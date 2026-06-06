"""Local password encryption for saved VPS credentials."""

from __future__ import annotations

import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from minebridge_frp.app.core.exceptions import ConfigurationError


class PasswordVault:
    """Encrypt and decrypt saved passwords with a local app key."""

    def __init__(self, config_dir: Path) -> None:
        self.key_path = config_dir / "secret.key"

    def encrypt_password(self, password: str) -> str | None:
        """Return encrypted password text suitable for database storage."""
        if not password:
            return None
        return self._fernet().encrypt(password.encode("utf-8")).decode("ascii")

    def decrypt_password(self, encrypted_password: str | None) -> str:
        """Return plaintext password for use in the current UI session."""
        if not encrypted_password:
            return ""
        try:
            return self._fernet().decrypt(encrypted_password.encode("ascii")).decode("utf-8")
        except (InvalidToken, UnicodeDecodeError, ValueError) as exc:
            raise ConfigurationError("Не удалось расшифровать сохранённый VPS password.") from exc

    def _fernet(self) -> Fernet:
        return Fernet(self._load_or_create_key())

    def _load_or_create_key(self) -> bytes:
        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        if self.key_path.exists():
            return self.key_path.read_bytes().strip()

        key = Fernet.generate_key()
        self.key_path.write_bytes(key)
        try:
            os.chmod(self.key_path, 0o600)
        except OSError:
            pass
        return key
