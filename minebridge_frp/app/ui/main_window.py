"""Main application window."""

from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSystemTrayIcon,
    QTabWidget,
)

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
        self.settings = QSettings("MineBridge", "MineBridge FRP")
        self._force_quit = False

        self.setWindowTitle("MineBridge FRP")
        self.resize(1120, 760)
        self.setMinimumSize(960, 640)
        self._restore_window_state()
        self._apply_saved_theme()
        self.tray_icon = self._create_tray_icon()

        tabs = QTabWidget()
        self.quick_start_tab = QuickStartTab(context, self.profile_service)
        tabs.addTab(self.quick_start_tab, "Быстрый запуск")
        tabs.addTab(VpsTab(context, self.profile_service), "VPS")
        tabs.addTab(MinecraftTab(self.profile_service), "Minecraft")
        tabs.addTab(TunnelTab(context, self.profile_service), "Туннель")
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
            self.quick_start_tab._stop_all()

        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        super().closeEvent(event)

    def _create_tray_icon(self) -> QSystemTrayIcon | None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return None

        tray = QSystemTrayIcon(self)
        tray.setToolTip("MineBridge FRP")
        if not self.windowIcon().isNull():
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

    def _apply_saved_theme(self) -> None:
        theme = self.settings.value("theme", "system")
        app = QApplication.instance()
        if app is None:
            return
        if theme == "dark":
            app.setStyleSheet(
                "QWidget { background: #111827; color: #f9fafb; }"
                "QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox, QTableWidget {"
                " background: #1f2937; color: #f9fafb; border: 1px solid #374151; }"
                "QPushButton { background: #374151; color: #f9fafb; padding: 6px 10px; }"
            )
        elif theme == "light":
            app.setStyleSheet("")
        else:
            app.setStyleSheet("")
