"""Status badge widget."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel


class StatusBadge(QLabel):
    """Small colored status label."""

    COLORS = {
        "ok": ("#0f766e", "#ecfdf5"),
        "warning": ("#92400e", "#fffbeb"),
        "error": ("#991b1b", "#fef2f2"),
    }

    def __init__(self, text: str, status: str = "warning") -> None:
        super().__init__()
        self.set_status(text, status)

    def set_status(self, text: str, status: str) -> None:
        color, background = self.COLORS.get(status, self.COLORS["warning"])
        self.setText(text)
        self.setStyleSheet(
            "QLabel {"
            f"color: {color};"
            f"background: {background};"
            "border: 1px solid rgba(0, 0, 0, 0.12);"
            "border-radius: 6px;"
            "padding: 4px 8px;"
            "}"
        )

