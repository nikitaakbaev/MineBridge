"""Diagnostics checks for profiles and runtime state."""

from __future__ import annotations

from pathlib import Path

from minebridge_frp.app.core.app_context import AppContext
from minebridge_frp.app.models.diagnostics import DiagnosticResult
from minebridge_frp.app.models.profile import ProfileBundle
from minebridge_frp.app.services.frp_manager import FrpManager
from minebridge_frp.app.services.minecraft_manager import MinecraftManager
from minebridge_frp.app.utils.ports import is_local_port_listening, is_port_open
from minebridge_frp.app.utils.process import is_process_running


class DiagnosticsService:
    """Run user-facing diagnostics for the active profile."""

    def __init__(self, context: AppContext) -> None:
        self.context = context
        self.minecraft_manager = MinecraftManager()
        self.frp_manager = FrpManager(context.data_dir / "frp")

    def run_profile_checks(self, bundle: ProfileBundle) -> list[DiagnosticResult]:
        """Run checks that do not require destructive remote changes."""
        results: list[DiagnosticResult] = []
        results.extend(self._minecraft_checks(bundle))
        results.extend(self._tunnel_checks(bundle))
        results.extend(self._vps_checks(bundle))
        return results

    def _minecraft_checks(self, bundle: ProfileBundle) -> list[DiagnosticResult]:
        config = bundle.minecraft
        results: list[DiagnosticResult] = []

        try:
            version = self.minecraft_manager.check_java_version(config.java_path or None)
            first_line = version.splitlines()[0] if version else "Java доступна"
            results.append(DiagnosticResult(status="OK", name="Java", description=first_line))
        except Exception as exc:  # noqa: BLE001 - diagnostics should report any failure as a result.
            results.append(
                DiagnosticResult(
                    status="ERROR",
                    name="Java",
                    description=str(exc),
                    fix_available=True,
                    fix_id="find_java",
                )
            )

        server_dir = Path(config.server_dir) if config.server_dir else None
        if server_dir and server_dir.exists():
            results.append(
                DiagnosticResult(status="OK", name="Server folder", description=str(server_dir))
            )
        else:
            results.append(
                DiagnosticResult(
                    status="ERROR",
                    name="Server folder",
                    description="Папка Minecraft-сервера не выбрана или не существует.",
                    fix_available=True,
                    fix_id="select_server_dir",
                )
            )

        jar_path = Path(config.jar_path) if config.jar_path else None
        if jar_path and jar_path.exists():
            results.append(
                DiagnosticResult(status="OK", name="server.jar", description=str(jar_path))
            )
        else:
            results.append(
                DiagnosticResult(
                    status="ERROR",
                    name="server.jar",
                    description="server.jar не выбран или не существует.",
                    fix_available=True,
                    fix_id="select_server_jar",
                )
            )

        if server_dir and self.minecraft_manager.check_eula(server_dir):
            results.append(DiagnosticResult(status="OK", name="EULA", description="eula=true"))
        else:
            results.append(
                DiagnosticResult(
                    status="ERROR",
                    name="EULA",
                    description="EULA Minecraft не принята.",
                    fix_available=True,
                    fix_id="open_eula",
                )
            )

        properties_path = server_dir / "server.properties" if server_dir else None
        if properties_path and properties_path.exists():
            properties = self.minecraft_manager.load_server_properties(server_dir)
            configured_port = properties.get("server-port")
            if configured_port and configured_port != str(config.mc_port):
                results.append(
                    DiagnosticResult(
                        status="WARNING",
                        name="server.properties",
                        description=(
                            f"server-port={configured_port}, а в профиле указан {config.mc_port}."
                        ),
                    )
                )
            else:
                results.append(
                    DiagnosticResult(
                        status="OK",
                        name="server.properties",
                        description="Файл найден и порт совпадает с профилем.",
                    )
                )
        else:
            results.append(
                DiagnosticResult(
                    status="WARNING",
                    name="server.properties",
                    description="server.properties ещё не создан.",
                    fix_available=True,
                    fix_id="save_server_properties",
                )
            )

        if is_local_port_listening(config.mc_port):
            results.append(
                DiagnosticResult(
                    status="WARNING",
                    name="Local Minecraft port",
                    description=f"Порт {config.mc_port} уже слушает. Возможно, сервер уже запущен.",
                )
            )
        else:
            results.append(
                DiagnosticResult(
                    status="OK",
                    name="Local Minecraft port",
                    description=f"Порт {config.mc_port} свободен.",
                )
            )

        if is_process_running("java"):
            results.append(
                DiagnosticResult(
                    status="WARNING",
                    name="Java process",
                    description="Найден запущенный Java-процесс. Это может быть Minecraft-сервер.",
                )
            )
        else:
            results.append(
                DiagnosticResult(
                    status="OK",
                    name="Java process",
                    description="Запущенные Java-процессы не обнаружены.",
                )
            )

        return results

    def _tunnel_checks(self, bundle: ProfileBundle) -> list[DiagnosticResult]:
        config = bundle.tunnel
        results: list[DiagnosticResult] = []

        if config.frp_token:
            results.append(
                DiagnosticResult(status="OK", name="FRP token", description="Token задан.")
            )
        else:
            results.append(
                DiagnosticResult(
                    status="ERROR",
                    name="FRP token",
                    description="FRP token не задан.",
                    fix_available=True,
                    fix_id="generate_token",
                )
            )

        server_addr = config.frp_server_addr or bundle.vps.host
        if server_addr:
            results.append(
                DiagnosticResult(status="OK", name="FRP server address", description=server_addr)
            )
        else:
            results.append(
                DiagnosticResult(
                    status="ERROR",
                    name="FRP server address",
                    description="FRP server address/VPS host не задан.",
                )
            )

        frpc = self.frp_manager.find_frpc_binary()
        if frpc:
            results.append(DiagnosticResult(status="OK", name="frpc binary", description=str(frpc)))
        else:
            results.append(
                DiagnosticResult(
                    status="WARNING",
                    name="frpc binary",
                    description="frpc пока не скачан.",
                    fix_available=True,
                    fix_id="download_frpc",
                )
            )

        if is_process_running("frpc"):
            results.append(
                DiagnosticResult(status="OK", name="frpc process", description="frpc запущен.")
            )
        else:
            results.append(
                DiagnosticResult(
                    status="WARNING",
                    name="frpc process",
                    description="frpc сейчас не запущен.",
                )
            )

        if server_addr:
            is_open = is_port_open(server_addr, config.remote_port, timeout=1.5)
            results.append(
                DiagnosticResult(
                    status="OK" if is_open else "WARNING",
                    name="External port",
                    description=(
                        f"{server_addr}:{config.remote_port} отвечает."
                        if is_open
                        else f"{server_addr}:{config.remote_port} не отвечает или закрыт."
                    ),
                )
            )

        return results

    def _vps_checks(self, bundle: ProfileBundle) -> list[DiagnosticResult]:
        config = bundle.vps
        results: list[DiagnosticResult] = []

        if config.host:
            results.append(DiagnosticResult(status="OK", name="VPS host", description=config.host))
        else:
            results.append(
                DiagnosticResult(status="ERROR", name="VPS host", description="VPS host не задан.")
            )

        if config.username:
            results.append(
                DiagnosticResult(status="OK", name="SSH username", description=config.username)
            )
        else:
            results.append(
                DiagnosticResult(
                    status="ERROR",
                    name="SSH username",
                    description="SSH username не задан.",
                )
            )

        if config.auth_type == "private_key" and config.private_key_path:
            key_path = Path(config.private_key_path)
            status = "OK" if key_path.exists() else "ERROR"
            description = str(key_path) if key_path.exists() else "Private key path не существует."
            results.append(
                DiagnosticResult(status=status, name="SSH private key", description=description)
            )
        elif config.auth_type == "password":
            results.append(
                DiagnosticResult(
                    status="WARNING",
                    name="SSH password",
                    description="Пароль не хранится. Проверка SSH выполняется во вкладке VPS.",
                )
            )

        results.append(
            DiagnosticResult(
                status="WARNING",
                name="Remote frps",
                description=(
                    "Удалённый frps проверяется через SSH во вкладке VPS или Быстрый запуск."
                ),
            )
        )
        return results
