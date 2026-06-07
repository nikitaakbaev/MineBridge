"""Diagnostics tab."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHeaderView,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from minebridge_frp.app.core.app_context import AppContext
from minebridge_frp.app.models.diagnostics import DiagnosticResult
from minebridge_frp.app.services.diagnostics_service import DiagnosticsService
from minebridge_frp.app.services.profile_service import ProfileService
from minebridge_frp.app.ui.layouts import FlowLayout, prepare_action_button
from minebridge_frp.app.ui.widgets.status_badge import StatusBadge
from minebridge_frp.app.ui.workers import run_in_thread
from minebridge_frp.app.utils.secrets import generate_token


class DiagnosticsTab(QWidget):
    """Diagnostics overview for the active profile."""

    def __init__(self, context: AppContext, profile_service: ProfileService) -> None:
        super().__init__()
        self.context = context
        self.profile_service = profile_service
        self.service = DiagnosticsService(context)
        self._threads = []

        self.run_button = QPushButton("Запустить диагностику")
        self.clear_button = QPushButton("Очистить отчёт")
        prepare_action_button(self.run_button)
        prepare_action_button(self.clear_button)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Статус", "Проверка", "Описание", "Исправить"])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.setMinimumHeight(180)

        self.report = QTextEdit()
        self.report.setReadOnly(True)
        self.report.setPlaceholderText("Отчёт диагностики появится после запуска проверок.")
        self.report.setMinimumHeight(160)

        buttons = QWidget()
        buttons_layout = FlowLayout(buttons, margin=0, spacing=8)
        buttons_layout.addWidget(self.run_button)
        buttons_layout.addWidget(self.clear_button)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.table)
        splitter.addWidget(self.report)
        splitter.setChildrenCollapsible(False)
        splitter.setSizes([360, 220])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        layout.addWidget(buttons)
        layout.addWidget(splitter)

        self.run_button.clicked.connect(self.run_diagnostics)
        self.clear_button.clicked.connect(self._clear)

    def run_diagnostics(self) -> None:
        self.run_button.setEnabled(False)
        self.report.setPlainText("Диагностика выполняется...")
        bundle = self.profile_service.get_active_configuration()
        thread = run_in_thread(
            lambda: self.service.run_profile_checks(bundle),
            self._show_results,
            self._show_error,
        )
        self._threads.append(thread)

    def _show_results(self, results: object) -> None:
        self.run_button.setEnabled(True)
        typed_results = list(results) if isinstance(results, list) else []
        self.table.setRowCount(0)
        for result in typed_results:
            if isinstance(result, DiagnosticResult):
                self._add_result_row(result)
        self.report.setPlainText(self._build_report(typed_results))

    def _add_result_row(self, result: DiagnosticResult) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        status_kind = {"OK": "ok", "WARNING": "warning", "ERROR": "error"}[result.status]
        self.table.setCellWidget(row, 0, StatusBadge(result.status, status_kind))
        self.table.setItem(row, 1, QTableWidgetItem(result.name))
        self.table.setItem(row, 2, QTableWidgetItem(result.description))

        if result.fix_available and result.fix_id:
            button = QPushButton("Исправить")
            button.clicked.connect(
                lambda _checked=False, fix_id=result.fix_id: self._run_fix(fix_id)
            )
            self.table.setCellWidget(row, 3, button)
        else:
            self.table.setItem(row, 3, QTableWidgetItem(""))

    def _run_fix(self, fix_id: str) -> None:
        if fix_id == "generate_token":
            bundle = self.profile_service.get_active_tunnel_profile()
            bundle.config.frp_token = generate_token()
            self.profile_service.save_tunnel_profile(bundle)
            QMessageBox.information(self, "Диагностика", "FRP token сгенерирован и сохранён.")
            self.run_diagnostics()
            return

        if fix_id == "open_eula":
            config = self.profile_service.get_active_minecraft_profile().config
            server_dir = Path(config.server_dir)
            if not config.server_dir:
                QMessageBox.warning(self, "Диагностика", "Сначала выберите папку сервера.")
                return
            self.service.minecraft_manager.open_eula(server_dir)
            QMessageBox.information(self, "Диагностика", "Открыт eula.txt.")
            return

        if fix_id == "save_server_properties":
            config = self.profile_service.get_active_minecraft_profile().config
            if not config.server_dir:
                QMessageBox.warning(self, "Диагностика", "Сначала выберите папку сервера.")
                return
            path = self.service.minecraft_manager.save_server_properties(
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
            QMessageBox.information(self, "Диагностика", f"server.properties сохранён: {path}")
            self.run_diagnostics()
            return

        if fix_id == "find_java":
            java = self.service.minecraft_manager.find_java()
            if not java:
                QMessageBox.warning(self, "Диагностика", "Java не найдена в PATH.")
                return
            bundle = self.profile_service.get_active_minecraft_profile()
            bundle.config.java_path = java
            self.profile_service.save_minecraft_profile(bundle)
            QMessageBox.information(self, "Диагностика", f"Java сохранена: {java}")
            self.run_diagnostics()
            return

        if fix_id == "download_frpc":
            QMessageBox.information(
                self,
                "Диагностика",
                "Скачивание frpc выполняется во вкладке Туннель, чтобы показать прогресс и логи.",
            )
            return

        QMessageBox.information(
            self,
            "Диагностика",
            "Для этого исправления откройте соответствующую вкладку настроек.",
        )

    def _build_report(self, results: list[object]) -> str:
        lines = []
        counts = {"OK": 0, "WARNING": 0, "ERROR": 0}
        for result in results:
            if not isinstance(result, DiagnosticResult):
                continue
            counts[result.status] += 1
            lines.append(f"[{result.status}] {result.name}: {result.description}")
        summary = f"Итог: OK={counts['OK']}, WARNING={counts['WARNING']}, ERROR={counts['ERROR']}"
        return "\n".join([summary, "", *lines])

    def _show_error(self, message: str) -> None:
        self.run_button.setEnabled(True)
        self.report.setPlainText(message)
        QMessageBox.warning(self, "Диагностика", message)

    def _clear(self) -> None:
        self.table.setRowCount(0)
        self.report.clear()
