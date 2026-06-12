"""FastAPI application factory."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from minebridge_frp.app.api.runtime import BackendRuntime
from minebridge_frp.app.api.schemas import (
    ApiMessage,
    CommandOutput,
    CommandRequest,
    CreateProfileRequest,
    RenameProfileRequest,
    SaveMinecraftProfileRequest,
    SaveTunnelProfileRequest,
    SaveVpsProfileRequest,
    VpsActionRequest,
)
from minebridge_frp.app.core.app_context import AppContext
from minebridge_frp.app.core.exceptions import ConfigurationError, MineBridgeError
from minebridge_frp.app.models.diagnostics import DiagnosticResult
from minebridge_frp.app.models.profile import (
    MinecraftProfileBundle,
    Profile,
    ProfileBundle,
    TunnelProfileBundle,
    VpsProfileBundle,
)


def create_app(context: AppContext | None = None) -> FastAPI:
    """Create the local backend API used by the Electron frontend."""
    runtime = BackendRuntime(context or AppContext.create())
    app = FastAPI(title="MineBridge FRP Backend", version="0.1.0")
    app.state.runtime = runtime

    @app.exception_handler(MineBridgeError)
    async def minebridge_error_handler(_request, exc: MineBridgeError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.get("/api/health", response_model=ApiMessage)
    def health() -> ApiMessage:
        return ApiMessage(message="ok")

    @app.get("/api/profiles/active", response_model=ProfileBundle)
    def active_profile() -> ProfileBundle:
        return runtime.profile_service.get_active_configuration()

    @app.get("/api/profiles/vps", response_model=list[Profile])
    def list_vps_profiles() -> list[Profile]:
        return runtime.profile_service.list_vps_profiles()

    @app.get("/api/profiles/vps/active", response_model=VpsProfileBundle)
    def active_vps_profile() -> VpsProfileBundle:
        return runtime.profile_service.get_active_vps_profile()

    @app.post("/api/profiles/vps", response_model=VpsProfileBundle)
    def create_vps_profile(payload: CreateProfileRequest) -> VpsProfileBundle:
        return runtime.profile_service.create_vps_profile(payload.name)

    @app.post("/api/profiles/vps/{profile_id}/active", response_model=VpsProfileBundle)
    def set_active_vps_profile(profile_id: int) -> VpsProfileBundle:
        return runtime.profile_service.set_active_vps_profile(profile_id)

    @app.patch("/api/profiles/vps/{profile_id}", response_model=VpsProfileBundle)
    def save_vps_profile(profile_id: int, payload: SaveVpsProfileRequest) -> VpsProfileBundle:
        bundle = runtime.profile_service.get_active_vps_profile()
        if bundle.profile.id != profile_id:
            bundle = runtime.profile_service.set_active_vps_profile(profile_id)
        bundle.config = payload.config.model_copy(update={"id": bundle.config.id})
        return runtime.profile_service.save_vps_profile(bundle)

    @app.patch("/api/profiles/vps/{profile_id}/name", response_model=VpsProfileBundle)
    def rename_vps_profile(profile_id: int, payload: RenameProfileRequest) -> VpsProfileBundle:
        return runtime.profile_service.rename_vps_profile(profile_id, payload.name)

    @app.delete("/api/profiles/vps/{profile_id}", response_model=VpsProfileBundle)
    def delete_vps_profile(profile_id: int) -> VpsProfileBundle:
        return runtime.profile_service.delete_vps_profile(profile_id)

    @app.get("/api/profiles/minecraft", response_model=list[Profile])
    def list_minecraft_profiles() -> list[Profile]:
        return runtime.profile_service.list_minecraft_profiles()

    @app.get("/api/profiles/minecraft/active", response_model=MinecraftProfileBundle)
    def active_minecraft_profile() -> MinecraftProfileBundle:
        return runtime.profile_service.get_active_minecraft_profile()

    @app.post("/api/profiles/minecraft", response_model=MinecraftProfileBundle)
    def create_minecraft_profile(payload: CreateProfileRequest) -> MinecraftProfileBundle:
        return runtime.profile_service.create_minecraft_profile(payload.name)

    @app.post("/api/profiles/minecraft/{profile_id}/active", response_model=MinecraftProfileBundle)
    def set_active_minecraft_profile(profile_id: int) -> MinecraftProfileBundle:
        return runtime.profile_service.set_active_minecraft_profile(profile_id)

    @app.patch("/api/profiles/minecraft/{profile_id}", response_model=MinecraftProfileBundle)
    def save_minecraft_profile(
        profile_id: int,
        payload: SaveMinecraftProfileRequest,
    ) -> MinecraftProfileBundle:
        bundle = runtime.profile_service.get_active_minecraft_profile()
        if bundle.profile.id != profile_id:
            bundle = runtime.profile_service.set_active_minecraft_profile(profile_id)
        bundle.config = payload.config.model_copy(update={"id": bundle.config.id})
        return runtime.profile_service.save_minecraft_profile(bundle)

    @app.patch("/api/profiles/minecraft/{profile_id}/name", response_model=MinecraftProfileBundle)
    def rename_minecraft_profile(
        profile_id: int,
        payload: RenameProfileRequest,
    ) -> MinecraftProfileBundle:
        return runtime.profile_service.rename_minecraft_profile(profile_id, payload.name)

    @app.delete("/api/profiles/minecraft/{profile_id}", response_model=MinecraftProfileBundle)
    def delete_minecraft_profile(profile_id: int) -> MinecraftProfileBundle:
        return runtime.profile_service.delete_minecraft_profile(profile_id)

    @app.get("/api/profiles/tunnels", response_model=list[Profile])
    def list_tunnel_profiles() -> list[Profile]:
        return runtime.profile_service.list_tunnel_profiles()

    @app.get("/api/profiles/tunnels/active", response_model=TunnelProfileBundle)
    def active_tunnel_profile() -> TunnelProfileBundle:
        return runtime.profile_service.get_active_tunnel_profile()

    @app.post("/api/profiles/tunnels", response_model=TunnelProfileBundle)
    def create_tunnel_profile(payload: CreateProfileRequest) -> TunnelProfileBundle:
        return runtime.profile_service.create_tunnel_profile(payload.name)

    @app.post("/api/profiles/tunnels/{profile_id}/active", response_model=TunnelProfileBundle)
    def set_active_tunnel_profile(profile_id: int) -> TunnelProfileBundle:
        return runtime.profile_service.set_active_tunnel_profile(profile_id)

    @app.patch("/api/profiles/tunnels/{profile_id}", response_model=TunnelProfileBundle)
    def save_tunnel_profile(
        profile_id: int,
        payload: SaveTunnelProfileRequest,
    ) -> TunnelProfileBundle:
        bundle = runtime.profile_service.get_active_tunnel_profile()
        if bundle.profile.id != profile_id:
            bundle = runtime.profile_service.set_active_tunnel_profile(profile_id)
        bundle.config = payload.config.model_copy(update={"id": bundle.config.id})
        return runtime.profile_service.save_tunnel_profile(bundle)

    @app.patch("/api/profiles/tunnels/{profile_id}/name", response_model=TunnelProfileBundle)
    def rename_tunnel_profile(
        profile_id: int,
        payload: RenameProfileRequest,
    ) -> TunnelProfileBundle:
        return runtime.profile_service.rename_tunnel_profile(profile_id, payload.name)

    @app.delete("/api/profiles/tunnels/{profile_id}", response_model=TunnelProfileBundle)
    def delete_tunnel_profile(profile_id: int) -> TunnelProfileBundle:
        return runtime.profile_service.delete_tunnel_profile(profile_id)

    @app.post("/api/vps/check-ssh", response_model=CommandOutput)
    def check_ssh(payload: VpsActionRequest) -> CommandOutput:
        return _run_vps_command(runtime, payload, "check_ssh")

    @app.post("/api/vps/install-frps", response_model=ApiMessage)
    def install_frps(payload: VpsActionRequest) -> ApiMessage:
        token = runtime.profile_service.get_active_tunnel_profile().config.frp_token
        if not token:
            raise ConfigurationError("FRP token не задан.")
        manager = runtime.create_vps_manager(
            runtime.profile_service.get_active_vps_profile().config,
            payload.password,
        )
        try:
            runtime.events.publish("vps.action", status="started", action="install-frps")
            manager.install_frps_on_vps(token)
            runtime.events.publish("vps.action", status="finished", action="install-frps")
            return ApiMessage(message="FRP установлен на VPS.")
        finally:
            manager.close()

    @app.post("/api/vps/frps/config", response_model=ApiMessage)
    def create_frps_config(payload: VpsActionRequest) -> ApiMessage:
        token = runtime.profile_service.get_active_tunnel_profile().config.frp_token
        if not token:
            raise ConfigurationError("FRP token не задан.")
        manager = runtime.create_vps_manager(
            runtime.profile_service.get_active_vps_profile().config,
            payload.password,
        )
        try:
            manager.create_frps_config(token)
            return ApiMessage(message="frps.toml создан на VPS.")
        finally:
            manager.close()

    @app.post("/api/vps/frps/start", response_model=CommandOutput)
    def start_frps(payload: VpsActionRequest) -> CommandOutput:
        return _run_vps_command(runtime, payload, "start_frps")

    @app.post("/api/vps/frps/stop", response_model=CommandOutput)
    def stop_frps(payload: VpsActionRequest) -> CommandOutput:
        return _run_vps_command(runtime, payload, "stop_frps")

    @app.post("/api/vps/frps/restart", response_model=CommandOutput)
    def restart_frps(payload: VpsActionRequest) -> CommandOutput:
        return _run_vps_command(runtime, payload, "restart_frps")

    @app.post("/api/vps/frps/status", response_model=CommandOutput)
    def status_frps(payload: VpsActionRequest) -> CommandOutput:
        return _run_vps_command(runtime, payload, "status_frps")

    @app.post("/api/vps/firewall/open", response_model=ApiMessage)
    def open_firewall(payload: VpsActionRequest) -> ApiMessage:
        manager = runtime.create_vps_manager(
            runtime.profile_service.get_active_vps_profile().config,
            payload.password,
        )
        try:
            return ApiMessage(message=manager.open_firewall_port())
        finally:
            manager.close()

    @app.post("/api/minecraft/server-properties", response_model=ApiMessage)
    def save_server_properties() -> ApiMessage:
        config = runtime.profile_service.get_active_minecraft_profile().config
        path = runtime.minecraft_manager.save_server_properties(
            Path(config.server_dir),
            {
                "server-port": config.mc_port,
                "online-mode": config.online_mode,
                "difficulty": config.difficulty,
                "max-players": config.max_players,
                "motd": config.motd,
                "view-distance": config.view_distance,
                "simulation-distance": config.simulation_distance,
            },
        )
        return ApiMessage(message=str(path))

    @app.post("/api/minecraft/start", response_model=ApiMessage)
    def start_minecraft() -> ApiMessage:
        runtime.minecraft_manager.start_server(
            runtime.profile_service.get_active_minecraft_profile().config
        )
        return ApiMessage(message="Minecraft запускается.")

    @app.post("/api/minecraft/stop", response_model=ApiMessage)
    def stop_minecraft() -> ApiMessage:
        runtime.minecraft_manager.stop_server_gracefully()
        return ApiMessage(message="Остановка Minecraft запрошена.")

    @app.post("/api/minecraft/restart", response_model=ApiMessage)
    def restart_minecraft() -> ApiMessage:
        runtime.minecraft_manager.stop_server_gracefully()
        runtime.minecraft_manager.start_server(
            runtime.profile_service.get_active_minecraft_profile().config
        )
        return ApiMessage(message="Minecraft перезапускается.")

    @app.post("/api/minecraft/command", response_model=ApiMessage)
    def minecraft_command(payload: CommandRequest) -> ApiMessage:
        runtime.minecraft_manager.send_command(payload.command)
        return ApiMessage(message="Команда отправлена.")

    @app.post("/api/frpc/config", response_model=ApiMessage)
    def create_frpc_config() -> ApiMessage:
        bundle = runtime.profile_service.get_active_tunnel_profile()
        path = runtime.frp_manager.write_frpc_config(bundle.config, bundle.profile.name)
        return ApiMessage(message=str(path))

    @app.post("/api/frpc/download", response_model=ApiMessage)
    def download_frpc() -> ApiMessage:
        path = runtime.frp_manager.download_frpc()
        return ApiMessage(message=str(path))

    @app.post("/api/frpc/start", response_model=ApiMessage)
    def start_frpc() -> ApiMessage:
        bundle = runtime.profile_service.get_active_tunnel_profile()
        config_path = runtime.frp_manager.write_frpc_config(bundle.config, bundle.profile.name)
        runtime.frp_manager.start_frpc(config_path)
        return ApiMessage(message="frpc запускается.")

    @app.post("/api/frpc/stop", response_model=ApiMessage)
    def stop_frpc() -> ApiMessage:
        runtime.frp_manager.stop_frpc()
        return ApiMessage(message="Остановка frpc запрошена.")

    @app.post("/api/frpc/check-port", response_model=ApiMessage)
    def check_frpc_port() -> ApiMessage:
        config = runtime.profile_service.get_active_tunnel_profile().config
        host = (
            config.frp_server_addr
            or runtime.profile_service.get_active_vps_profile().config.host
        )
        if not host:
            raise ConfigurationError("FRP/VPS host не задан.")
        is_open = runtime.frp_manager.check_external_port(host, config.remote_port)
        status = "open" if is_open else "closed"
        return ApiMessage(message=f"{host}:{config.remote_port} {status}")

    @app.post("/api/diagnostics/run", response_model=list[DiagnosticResult])
    def run_diagnostics() -> list[DiagnosticResult]:
        return runtime.diagnostics_service.run_profile_checks(
            runtime.profile_service.get_active_configuration()
        )

    @app.get("/api/logs/app", response_model=ApiMessage)
    def read_app_log() -> ApiMessage:
        path = runtime.app_log_path()
        if not path.exists():
            return ApiMessage(message="")
        return ApiMessage(message=path.read_text(encoding="utf-8", errors="replace"))

    @app.websocket("/ws/events")
    async def websocket_events(websocket: WebSocket) -> None:
        await websocket.accept()
        queue = await runtime.events.subscribe()
        try:
            while True:
                event = await queue.get()
                await websocket.send_json({"type": event.type, "payload": event.payload})
        except WebSocketDisconnect:
            runtime.events.unsubscribe(queue)

    return app


def _run_vps_command(
    runtime: BackendRuntime,
    payload: VpsActionRequest,
    method_name: str,
) -> CommandOutput:
    manager = runtime.create_vps_manager(
        runtime.profile_service.get_active_vps_profile().config,
        payload.password,
    )
    try:
        result = getattr(manager, method_name)()
        return CommandOutput(
            stdout=getattr(result, "stdout", ""),
            stderr=getattr(result, "stderr", ""),
            exit_status=getattr(result, "exit_status", None),
        )
    finally:
        manager.close()
