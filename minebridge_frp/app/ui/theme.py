"""Application stylesheet helpers."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication


def apply_theme(app: QApplication, theme: str) -> None:
    """Apply a compact readable theme."""
    if theme == "light":
        app.setStyleSheet(LIGHT_STYLESHEET)
        return
    if theme == "dark":
        app.setStyleSheet(DARK_STYLESHEET)
        return
    app.setStyleSheet(LIGHT_STYLESHEET)


COMMON_STYLESHEET = """
QWidget {
    font-size: 13px;
}
QScrollArea {
    border: none;
}
QScrollArea > QWidget > QWidget {
    padding: 10px;
}
QTabWidget::pane {
    border: 1px solid palette(mid);
    top: -1px;
}
QTabBar::tab {
    min-width: 92px;
    padding: 9px 14px;
    margin-right: 2px;
}
QGroupBox {
    font-weight: 600;
    border: 1px solid palette(mid);
    border-radius: 6px;
    margin-top: 14px;
    padding: 12px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox, QTableWidget {
    border: 1px solid palette(mid);
    border-radius: 5px;
    padding: 6px;
    min-height: 28px;
    selection-background-color: #2563eb;
}
QCheckBox {
    min-height: 28px;
    spacing: 8px;
}
QComboBox::drop-down {
    width: 28px;
}
QSpinBox::up-button, QSpinBox::down-button {
    width: 22px;
}
QPushButton {
    border: 1px solid palette(mid);
    border-radius: 5px;
    padding: 7px 11px;
    min-height: 30px;
}
QPushButton:hover {
    border-color: #2563eb;
}
QPlainTextEdit {
    font-family: "JetBrains Mono", "Consolas", monospace;
}
"""

DARK_STYLESHEET = (
    COMMON_STYLESHEET
    + """
QWidget {
    background: #1f2933;
    color: #edf2f7;
}
QTabBar::tab {
    background: #2d3748;
    color: #edf2f7;
}
QTabBar::tab:selected {
    background: #334155;
    border-bottom: 2px solid #60a5fa;
}
QGroupBox {
    background: #243140;
}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox, QTableWidget {
    background: #111827;
    color: #f8fafc;
}
QPushButton {
    background: #374151;
    color: #f8fafc;
}
QPushButton:pressed {
    background: #1f2937;
}
"""
)

LIGHT_STYLESHEET = (
    COMMON_STYLESHEET
    + """
QWidget {
    background: #f8fafc;
    color: #172033;
}
QTabBar::tab {
    background: #e5e7eb;
    color: #172033;
}
QTabBar::tab:selected {
    background: #ffffff;
    border-bottom: 2px solid #2563eb;
}
QGroupBox {
    background: #ffffff;
}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox, QTableWidget {
    background: #ffffff;
    color: #172033;
}
QPushButton {
    background: #ffffff;
    color: #172033;
}
QPushButton:pressed {
    background: #e5e7eb;
}
"""
)
