from __future__ import annotations

from minebridge_frp.app.services.password_vault import PasswordVault


def test_password_vault_encrypts_and_decrypts_password(tmp_path):
    vault = PasswordVault(tmp_path)

    encrypted = vault.encrypt_password("ssh-secret")

    assert encrypted is not None
    assert encrypted != "ssh-secret"
    assert vault.decrypt_password(encrypted) == "ssh-secret"
    assert (tmp_path / "secret.key").exists()


def test_password_vault_keeps_empty_password_empty(tmp_path):
    vault = PasswordVault(tmp_path)

    assert vault.encrypt_password("") is None
    assert vault.decrypt_password(None) == ""
