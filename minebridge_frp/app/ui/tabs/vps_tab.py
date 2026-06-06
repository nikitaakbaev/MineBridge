"""VPS configuration tab."""

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

from minebridge_frp.app.ui.widgets.path_picker import PathPicker


class VpsTab(QWidget):
    """VPS SSH and remote FRP controls."""

    def __init__(self) -> None:
        super().__init__()

        ssh_port = QSpinBox()
        ssh_port.setRange(1, 65535)
        ssh_port.setValue(22)

        auth_type = QComboBox()
        auth_type.addItems(["password", "private key"])

        bind_port = QSpinBox()
        bind_port.setRange(1, 65535)
        bind_port.setValue(7000)

        dashboard_port = QSpinBox()
        dashboard_port.setRange(1, 65535)
        dashboard_port.setValue(7500)

        password = QLineEdit()
        password.setEchoMode(QLineEdit.Password)

        form = QFormLayout()
        form.addRow("VPS IP / host", QLineEdit())
        form.addRow("SSH port", ssh_port)
        form.addRow("SSH username", QLineEdit())
        form.addRow("Auth type", auth_type)
        form.addRow("Password", password)
        form.addRow("Private key path", PathPicker(file_mode=True))
        form.addRow("Remote install dir", QLineEdit("/opt/minebridge-frp"))
        form.addRow("frps bind port", bind_port)
        form.addRow("Dashboard enabled", QCheckBox())
        form.addRow("Dashboard port", dashboard_port)

        actions = QGroupBox("Действия VPS")
        grid = QGridLayout(actions)
        labels = [
            "Проверить SSH",
            "Установить FRP на VPS",
            "Обновить FRP на VPS",
            "Создать frps.toml",
            "Установить systemd-сервис",
            "Запустить frps",
            "Остановить frps",
            "Перезапустить frps",
            "Проверить статус frps",
            "Открыть порт в firewall",
        ]
        for index, label in enumerate(labels):
            grid.addWidget(QPushButton(label), index // 2, index % 2)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(actions)
        layout.addStretch(1)
