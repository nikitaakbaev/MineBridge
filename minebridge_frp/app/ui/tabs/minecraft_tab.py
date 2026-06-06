"""Minecraft server tab."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from minebridge_frp.app.ui.widgets.console_input import ConsoleInput
from minebridge_frp.app.ui.widgets.log_viewer import LogViewer
from minebridge_frp.app.ui.widgets.path_picker import PathPicker


class MinecraftTab(QWidget):
    """Local Minecraft server controls."""

    def __init__(self) -> None:
        super().__init__()

        port = QSpinBox()
        port.setRange(1, 65535)
        port.setValue(25565)

        max_players = QSpinBox()
        max_players.setRange(1, 500)
        max_players.setValue(20)

        view_distance = QSpinBox()
        view_distance.setRange(2, 32)
        view_distance.setValue(10)

        simulation_distance = QSpinBox()
        simulation_distance.setRange(2, 32)
        simulation_distance.setValue(10)

        server_type = QComboBox()
        server_type.addItems(["Vanilla", "Paper", "Fabric", "Forge", "NeoForge"])

        difficulty = QComboBox()
        difficulty.addItems(["peaceful", "easy", "normal", "hard"])

        form = QFormLayout()
        form.addRow("Папка сервера", PathPicker(file_mode=False))
        form.addRow("server.jar", PathPicker(file_mode=True))
        form.addRow("Java path", PathPicker(file_mode=True))
        form.addRow("Xms", QLineEdit("2G"))
        form.addRow("Xmx", QLineEdit("4G"))
        form.addRow("Minecraft port", port)
        form.addRow("Server type", server_type)
        form.addRow("Minecraft version", QLineEdit())
        form.addRow("Автоматически открыть eula.txt", QCheckBox())
        form.addRow("Я принимаю EULA Minecraft", QCheckBox())
        form.addRow("online-mode", QCheckBox())
        form.addRow("difficulty", difficulty)
        form.addRow("max-players", max_players)
        form.addRow("motd", QLineEdit("MineBridge FRP server"))
        form.addRow("view-distance", view_distance)
        form.addRow("simulation-distance", simulation_distance)

        actions = QGroupBox("Действия Minecraft")
        grid = QGridLayout(actions)
        labels = [
            "Найти Java",
            "Проверить Java",
            "Выбрать папку сервера",
            "Найти server.jar",
            "Открыть eula.txt",
            "Сохранить server.properties",
            "Запустить Minecraft-сервер",
            "Остановить Minecraft-сервер",
            "Перезапустить Minecraft-сервер",
        ]
        for index, label in enumerate(labels):
            grid.addWidget(QPushButton(label), index // 3, index % 3)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(actions)
        layout.addWidget(LogViewer("Minecraft logs"))
        layout.addWidget(ConsoleInput())

