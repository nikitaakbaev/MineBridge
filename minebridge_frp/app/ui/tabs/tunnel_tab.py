"""FRP tunnel tab."""

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


class TunnelTab(QWidget):
    """Local frpc configuration and controls."""

    def __init__(self) -> None:
        super().__init__()

        local_port = QSpinBox()
        local_port.setRange(1, 65535)
        local_port.setValue(25565)

        remote_port = QSpinBox()
        remote_port.setRange(1, 65535)
        remote_port.setValue(25565)

        server_port = QSpinBox()
        server_port.setRange(1, 65535)
        server_port.setValue(7000)

        protocol = QComboBox()
        protocol.addItem("tcp")

        token = QLineEdit()
        token.setEchoMode(QLineEdit.Password)

        form = QFormLayout()
        form.addRow("Profile name", QLineEdit("default"))
        form.addRow("Local IP", QLineEdit("127.0.0.1"))
        form.addRow("Local port", local_port)
        form.addRow("Remote port", remote_port)
        form.addRow("Protocol", protocol)
        form.addRow("FRP server address", QLineEdit())
        form.addRow("FRP server bind port", server_port)
        form.addRow("Auth token", token)
        form.addRow("Auto-start frpc with Minecraft", QCheckBox())

        actions = QGroupBox("Действия туннеля")
        grid = QGridLayout(actions)
        labels = [
            "Сгенерировать токен",
            "Создать frpc.toml",
            "Скачать frpc",
            "Запустить frpc",
            "Остановить frpc",
            "Проверить внешний порт",
        ]
        for index, label in enumerate(labels):
            grid.addWidget(QPushButton(label), index // 3, index % 3)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(actions)
        layout.addStretch(1)
