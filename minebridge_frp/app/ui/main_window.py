"""Main application window."""

from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QMessageBox,
    QStyle,
    QSystemTrayIcon,
    QTabWidget,
)

from minebridge_frp.app.core.app_context import AppContext
from minebridge_frp.app.services.profile_service import ProfileService
from minebridge_frp.app.ui.icons import load_app_icon
from minebridge_frp.app.ui.tabs.diagnostics_tab import DiagnosticsTab
from minebridge_frp.app.ui.tabs.logs_tab import LogsTab
from minebridge_frp.app.ui.tabs.minecraft_tab import MinecraftTab
from minebridge_frp.app.ui.tabs.settings_tab import SettingsTab
from minebridge_frp.app.ui.tabs.tunnel_tab import FrpcTab
from minebridge_frp.app.ui.tabs.vps_tab import VpsTab
from minebridge_frp.app.ui.theme import apply_theme


class MainWindow(QMainWindow):
    """Top-level window with the main MineBridge workflow tabs."""

    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self.context = context
        self.profile_service = ProfileService.from_context(context)
        self.settings = QSettings("MineBridge", "MineBridge FRP")
        self._force_quit = False

        self.setWindowTitle("MineBridge FRP")
        self.resize(1180, 800)
        self.setMinimumSize(760, 520)
        icon = load_app_icon()
        if icon.isNull():
            icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.setWindowIcon(icon)
        self._restore_window_state()
        self._apply_theme()
        self.tray_icon = self._create_tray_icon()

        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.setMovable(False)
        tabs.setUsesScrollButtons(True)
        self.minecraft_tab = MinecraftTab(self.profile_service)
        self.frpc_tab = FrpcTab(context, self.profile_service)
        tabs.addTab(VpsTab(context, self.profile_service), "VPS")
        tabs.addTab(self.minecraft_tab, "Minecraft")
        tabs.addTab(self.frpc_tab, "frpc")
        tabs.addTab(DiagnosticsTab(context, self.profile_service), "Диагностика")
        tabs.addTab(LogsTab(context.log_dir), "Логи")
        tabs.addTab(SettingsTab(context), "Настройки")

        self.setCentralWidget(tabs)
        self.statusBar().showMessage("MineBridge FRP готов к настройке профиля")

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt override name.
        behavior = self.settings.value("close_behavior", "спросить")
        if (
            behavior == "свернуть в трей"
            and not self._force_quit
            and self.tray_icon
            and QSystemTrayIcon.isSystemTrayAvailable()
        ):
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "MineBridge FRP",
                "Приложение свернуто в трей.",
                QSystemTrayIcon.MessageIcon.Information,
                2500,
            )
            return

        if behavior == "спросить":
            answer = QMessageBox.question(
                self,
                "MineBridge FRP",
                "Закрыть приложение? Запущенные процессы могут продолжить работу.",
            )
            if answer != QMessageBox.Yes:
                event.ignore()
                return
        elif behavior == "остановить всё":
            self.frpc_tab._stop_frpc()
            self.minecraft_tab.manager.stop_server_gracefully()

        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        super().closeEvent(event)

    def _create_tray_icon(self) -> QSystemTrayIcon | None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return None

        tray = QSystemTrayIcon(self)
        tray.setToolTip("MineBridge FRP")
        tray.setIcon(self.windowIcon())

        menu = QMenu(self)
        show_action = QAction("Показать", self)
        quit_action = QAction("Выйти", self)
        show_action.triggered.connect(self.showNormal)
        quit_action.triggered.connect(self._quit_from_tray)
        menu.addAction(show_action)
        menu.addAction(quit_action)
        tray.setContextMenu(menu)
        tray.activated.connect(lambda _reason: self.showNormal())
        tray.show()
        return tray

    def _quit_from_tray(self) -> None:
        self._force_quit = True
        QApplication.quit()

    def _restore_window_state(self) -> None:
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        window_state = self.settings.value("windowState")
        if window_state:
            self.restoreState(window_state)

    def _apply_theme(self) -> None:
        app = QApplication.instance()
        if app is None:
            return
        apply_theme(app)
