"""Main application window."""

from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QTabWidget

from minebridge_frp.app.core.app_context import AppContext
from minebridge_frp.app.services.profile_service import ProfileService
from minebridge_frp.app.ui.tabs.diagnostics_tab import DiagnosticsTab
from minebridge_frp.app.ui.tabs.logs_tab import LogsTab
from minebridge_frp.app.ui.tabs.minecraft_tab import MinecraftTab
from minebridge_frp.app.ui.tabs.quick_start_tab import QuickStartTab
from minebridge_frp.app.ui.tabs.settings_tab import SettingsTab
from minebridge_frp.app.ui.tabs.tunnel_tab import TunnelTab
from minebridge_frp.app.ui.tabs.vps_tab import VpsTab


class MainWindow(QMainWindow):
    """Top-level window with the main MineBridge workflow tabs."""

    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self.context = context
        self.profile_service = ProfileService.from_context(context)

        self.setWindowTitle("MineBridge FRP")
        self.resize(1120, 760)
        self.setMinimumSize(960, 640)

        tabs = QTabWidget()
        tabs.addTab(QuickStartTab(self.profile_service), "Быстрый запуск")
        tabs.addTab(VpsTab(), "VPS")
        tabs.addTab(MinecraftTab(self.profile_service), "Minecraft")
        tabs.addTab(TunnelTab(context, self.profile_service), "Туннель")
        tabs.addTab(DiagnosticsTab(), "Диагностика")
        tabs.addTab(LogsTab(context.log_dir), "Логи")
        tabs.addTab(SettingsTab(context), "Настройки")

        self.setCentralWidget(tabs)
        self.statusBar().showMessage("MineBridge FRP готов к настройке профиля")
