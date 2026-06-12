"""Runtime state shared by FastAPI handlers."""

from __future__ import annotations

from pathlib import Path

from minebridge_frp.app.api.events import EventBus
from minebridge_frp.app.core.app_context import AppContext
from minebridge_frp.app.models.vps import VpsConfig
from minebridge_frp.app.services.diagnostics_service import DiagnosticsService
from minebridge_frp.app.services.frp_manager import FrpManager
from minebridge_frp.app.services.minecraft_manager import MinecraftManager
from minebridge_frp.app.services.password_vault import PasswordVault
from minebridge_frp.app.services.profile_service import ProfileService
from minebridge_frp.app.services.vps_manager import VpsManager


class BackendRuntime:
    """Own long-lived backend services for the local API server."""

    def __init__(self, context: AppContext) -> None:
        self.context = context
        self.profile_service = ProfileService.from_context(context)
        self.password_vault = PasswordVault(context.config_dir)
        self.minecraft_manager = MinecraftManager()
        self.frp_manager = FrpManager(context.data_dir / "frp")
        self.diagnostics_service = DiagnosticsService(context)
        self.events = EventBus()
        self._wire_events()

    def create_vps_manager(self, config: VpsConfig, password: str = "") -> VpsManager:
        return VpsManager(
            config,
            password=password or self.password_vault.decrypt_password(config.password_encrypted),
            frp_storage_dir=self.context.data_dir / "frp",
        )

    def app_log_path(self) -> Path:
        return self.context.log_dir / "minebridge-frp.log"

    def _wire_events(self) -> None:
        self.minecraft_manager.log_line.connect(
            lambda line: self.events.publish("minecraft.log", line=line)
        )
        self.minecraft_manager.status_changed.connect(
            lambda status: self.events.publish("minecraft.status", status=status)
        )
        self.minecraft_manager.error.connect(
            lambda message: self.events.publish("minecraft.error", message=message)
        )
        self.frp_manager.log_line.connect(lambda line: self.events.publish("frpc.log", line=line))
        self.frp_manager.status_changed.connect(
            lambda status: self.events.publish("frpc.status", status=status)
        )
        self.frp_manager.error.connect(
            lambda message: self.events.publish("frpc.error", message=message)
        )
