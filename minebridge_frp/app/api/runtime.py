"""Runtime state shared by FastAPI handlers."""

from __future__ import annotations

from pathlib import Path

from minebridge_frp.app.api.events import EventBus
from minebridge_frp.app.core.app_context import AppContext
from minebridge_frp.app.models.vps import VpsConfig
from minebridge_frp.app.services.diagnostics_service import DiagnosticsService
from minebridge_frp.app.services.frp_manager import FrpManager
from minebridge_frp.app.services.metrics_service import MetricsSampler
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

        self.minecraft_status = "idle"
        self.frpc_status = "idle"
        self.players: list[str] = []

        self.metrics = MetricsSampler(
            pid_provider=lambda: self.minecraft_manager.pid,
            players_provider=lambda: self.minecraft_manager.player_count,
            running_provider=lambda: self.minecraft_manager.is_running,
        )
        self._wire_events()

    def create_vps_manager(self, config: VpsConfig, password: str = "") -> VpsManager:
        return VpsManager(
            config,
            password=password or self.password_vault.decrypt_password(config.password_encrypted),
            frp_storage_dir=self.context.data_dir / "frp",
        )

    def app_log_path(self) -> Path:
        return self.context.log_dir / "minebridge-frp.log"

    def start(self) -> None:
        """Start background workers (called on API startup)."""
        self.metrics.start()

    def shutdown(self) -> None:
        """Stop background workers (called on API shutdown)."""
        self.metrics.stop()

    def state_snapshot(self) -> dict:
        """Return the current runtime state for freshly connected clients."""
        return {
            "minecraft_status": self.minecraft_status,
            "frpc_status": self.frpc_status,
            "players": list(self.players),
            "player_count": len(self.players),
            "uptime_seconds": round(self.minecraft_manager.uptime_seconds, 1),
            "metrics": self.metrics.last_snapshot,
        }

    def _set_minecraft_status(self, status: str) -> None:
        self.minecraft_status = status
        self.events.publish("minecraft.status", status=status)

    def _set_frpc_status(self, status: str) -> None:
        self.frpc_status = status
        self.events.publish("frpc.status", status=status)

    def _set_players(self, count: int, players: list[str]) -> None:
        self.players = list(players)
        self.events.publish("minecraft.players", count=count, players=list(players))

    def _wire_events(self) -> None:
        self.minecraft_manager.log_line.connect(
            lambda line: self.events.publish("minecraft.log", line=line)
        )
        self.minecraft_manager.status_changed.connect(self._set_minecraft_status)
        self.minecraft_manager.players_changed.connect(self._set_players)
        self.minecraft_manager.ready.connect(
            lambda: self.events.publish("minecraft.ready")
        )
        self.minecraft_manager.error.connect(
            lambda message: self.events.publish("minecraft.error", message=message)
        )
        self.frp_manager.log_line.connect(lambda line: self.events.publish("frpc.log", line=line))
        self.frp_manager.status_changed.connect(self._set_frpc_status)
        self.frp_manager.error.connect(
            lambda message: self.events.publish("frpc.error", message=message)
        )
        self.metrics.sample.connect(
            lambda snapshot: self.events.publish("metrics.sample", **snapshot)
        )
