"""Diagnostics tab."""

from __future__ import annotations

from PySide6.QtWidgets import QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class DiagnosticsTab(QWidget):
    """Diagnostics overview with placeholder checks for stage 1."""

    def __init__(self) -> None:
        super().__init__()

        table = QTableWidget(0, 3)
        table.setHorizontalHeaderLabels(["Статус", "Проверка", "Описание"])
        table.horizontalHeader().setStretchLastSection(True)

        checks = [
            ("WARNING", "Java", "Проверка будет реализована на этапе диагностики."),
            ("WARNING", "Minecraft port", "Проверка будет реализована на этапе диагностики."),
            ("WARNING", "VPS SSH", "Проверка будет реализована на этапе VPS Manager."),
            ("WARNING", "frpc/frps", "Проверка будет реализована на этапах FRP."),
        ]
        for status, check, description in checks:
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(status))
            table.setItem(row, 1, QTableWidgetItem(check))
            table.setItem(row, 2, QTableWidgetItem(description))

        layout = QVBoxLayout(self)
        layout.addWidget(QPushButton("Запустить диагностику"))
        layout.addWidget(table)

