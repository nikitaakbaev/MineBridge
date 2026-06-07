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
QTabWidget::pane {
    border: none;
    top: -1px;
}
QTabBar::tab {
    min-width: 74px;
    padding: 9px 12px;
    margin-right: 2px;
}
QGroupBox {
    font-weight: 600;
    border: 1px solid palette(mid);
    border-radius: 6px;
    margin-top: 10px;
    padding: 14px 10px 10px 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox, QTableWidget {
    border: 1px solid palette(mid);
    border-radius: 5px;
    padding: 5px;
    selection-background-color: #2563eb;
}
QLineEdit, QSpinBox, QComboBox {
    min-height: 28px;
    max-height: 42px;
}
QCheckBox {
    min-height: 28px;
    max-height: 42px;
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
    padding: 7px 10px;
    min-height: 30px;
}
QPushButton:hover {
    border-color: #2563eb;
}
QPlainTextEdit {
    font-family: "JetBrains Mono", "Consolas", monospace;
}
QSplitter::handle {
    background: palette(mid);
    margin: 5px 0;
}
QSplitter::handle:vertical {
    height: 10px;
}
"""

DARK_STYLESHEET = (
    COMMON_STYLESHEET
    + """
QWidget {
    background: #17212b;
    color: #edf2f7;
}
QTabBar::tab {
    background: #243140;
    color: #edf2f7;
}
QTabBar::tab:selected {
    background: #2f3f52;
    border-bottom: 2px solid #60a5fa;
}
QGroupBox {
    background: #1e2a36;
}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox, QTableWidget {
    background: #101722;
    color: #f8fafc;
}
QPushButton {
    background: #314052;
    color: #f8fafc;
}
QPushButton:pressed {
    background: #223041;
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
