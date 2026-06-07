"""Application stylesheet helpers."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication


def apply_theme(app: QApplication) -> None:
    """Apply the permanent MineBridge dark theme."""
    app.setStyleSheet(DARK_STYLESHEET)


COMMON_STYLESHEET = """
QWidget {
    font-size: 13px;
}
QLabel, QCheckBox, QRadioButton {
    background: transparent;
}
QMainWindow, QDialog {
    background: #111923;
}
QScrollArea {
    border: none;
    background: transparent;
}
QScrollBar:vertical {
    background: #101722;
    width: 10px;
    margin: 2px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #3b4a5e;
    min-height: 36px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #51627a;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: #101722;
    height: 10px;
    margin: 2px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background: #3b4a5e;
    min-width: 36px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal:hover {
    background: #51627a;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QTabWidget::pane {
    border: none;
    top: -1px;
}
QTabWidget {
    background: #111923;
}
QTabBar {
    background: #111923;
}
QTabBar::tab {
    min-width: 74px;
    padding: 10px 14px;
    margin-right: 1px;
    border: 1px solid #273443;
    border-bottom: none;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
}
QGroupBox {
    font-weight: 600;
    border: 1px solid #2e3d4e;
    border-radius: 6px;
    margin-top: 12px;
    padding: 16px 12px 12px 12px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: #d7e1ec;
    background: #172231;
}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox, QTableWidget {
    border: 1px solid #324257;
    border-radius: 5px;
    padding: 5px;
    selection-background-color: #3b82f6;
}
QLineEdit, QSpinBox, QComboBox {
    min-height: 28px;
    max-height: 42px;
}
QSpinBox {
    padding-right: 25px;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    border-color: #60a5fa;
}
QLineEdit[readOnly="true"] {
    color: #aebacc;
}
QCheckBox {
    min-height: 28px;
    max-height: 42px;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 15px;
    height: 15px;
    border: 1px solid #324257;
    border-radius: 3px;
    background: #0d1420;
}
QCheckBox::indicator:hover {
    border-color: #60a5fa;
}
QCheckBox::indicator:checked {
    background: #3b82f6;
    border-color: #60a5fa;
}
QComboBox::drop-down {
    width: 28px;
    border-left: 1px solid #324257;
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
    background: #132033;
}
QComboBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #d7e1ec;
}
QSpinBox::up-button, QSpinBox::down-button {
    subcontrol-origin: border;
    width: 23px;
    border-left: 1px solid #324257;
    background: #132033;
}
QSpinBox::up-button {
    subcontrol-position: top right;
    border-top-right-radius: 5px;
    border-bottom: 1px solid #324257;
    margin: 1px 1px 0 0;
}
QSpinBox::down-button {
    subcontrol-position: bottom right;
    border-bottom-right-radius: 5px;
    margin: 0 1px 1px 0;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background: #1b2b41;
}
QSpinBox::up-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid #d7e1ec;
}
QSpinBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #d7e1ec;
}
QPushButton {
    border: 1px solid #3a4a5f;
    border-radius: 5px;
    padding: 8px 11px;
    min-height: 30px;
}
QPushButton:hover {
    border-color: #60a5fa;
}
QPushButton:disabled {
    color: #7f8da0;
    border-color: #283545;
    background: #202b38;
}
QPlainTextEdit {
    font-family: "JetBrains Mono", "Consolas", monospace;
}
QTableWidget {
    gridline-color: #293849;
    alternate-background-color: #141e2a;
}
QHeaderView::section {
    background: #202b38;
    color: #dce7f3;
    border: none;
    border-right: 1px solid #2e3d4e;
    border-bottom: 1px solid #2e3d4e;
    padding: 7px;
}
QSplitter::handle {
    background: #2b3a4d;
    margin: 6px 0;
    border-radius: 4px;
}
QSplitter::handle:vertical {
    height: 10px;
}
QStatusBar {
    background: #111923;
    color: #aebacc;
    border-top: 1px solid #263443;
}
"""

DARK_STYLESHEET = (
    COMMON_STYLESHEET
    + """
QWidget {
    background: #111923;
    color: #edf2f7;
}
QTabBar::tab {
    background: #182332;
    color: #b9c6d6;
}
QTabBar::tab:selected {
    background: #223044;
    color: #ffffff;
    border-bottom: 2px solid #60a5fa;
}
QTabBar::tab:hover {
    background: #202d3f;
    color: #ffffff;
}
QGroupBox {
    background: #172231;
}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox, QTableWidget {
    background: #0d1420;
    color: #f8fafc;
}
QComboBox QAbstractItemView {
    background: #0d1420;
    color: #f8fafc;
    selection-background-color: #2563eb;
    border: 1px solid #324257;
}
QPushButton {
    background: #263548;
    color: #f8fafc;
}
QPushButton:pressed {
    background: #1d2a3a;
}
"""
)
