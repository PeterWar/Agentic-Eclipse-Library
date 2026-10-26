# config.py - Global configuration and styling for Eclipse Image Processor v0.6.0

APP_VERSION = "0.6.0"

import os

# ============================================================================
# SYSTEM CONFIGURATION
# ============================================================================
CPU_CORES = os.cpu_count() or 4  # Auto-detect CPU cores, default to 4

# ============================================================================
# QT STYLESHEET - Neutral dark editing workspace
# ============================================================================
LIGHTROOM_QSS = '''
    QMainWindow {
        background-color: #2b2b2b;
        color: #ffffff;
    }

    QWidget {
        font-size: 11px;
        background-color: #2b2b2b;
        color: #ffffff;
    }

    QLabel {
        color: #ffffff;
    }

    QSlider::groove:horizontal {
        background: #444444;
        height: 4px;
        margin: 2px 0;
        border-radius: 2px;
    }

    QSlider::handle:horizontal {
        background: #666666;
        width: 12px;
        margin: -4px 0;
        border-radius: 6px;
        border: 1px solid #777777;
    }

    QSlider::handle:horizontal:hover {
        background: #888888;
    }

    QSlider::sub-page:horizontal {
        background: #666666;
        border-radius: 2px;
    }

    QPushButton {
        background-color: #666666;
        color: white;
        border: none;
        padding: 6px 12px;
        border-radius: 3px;
        font-weight: bold;
    }

    QPushButton:hover {
        background-color: #888888;
    }

    QPushButton:pressed {
        background-color: #444444;
    }

    QPushButton:disabled {
        background-color: #555555;
        color: #999999;
    }

    QSpinBox, QDoubleSpinBox {
        background-color: #444444;
        color: #ffffff;
        border: 1px solid #555555;
        padding: 2px;
        border-radius: 2px;
    }

    QSpinBox::up-button, QDoubleSpinBox::up-button {
        background-color: #666666;
        border: none;
    }

    QSpinBox::down-button, QDoubleSpinBox::down-button {
        background-color: #666666;
        border: none;
    }

    QComboBox {
        font-size: 11px;
        background-color: #444444;
        color: #ffffff;
        border: 1px solid #555555;
        padding: 2px 4px;
        border-radius: 2px;
    }

    QComboBox::drop-down {
        background-color: #333333;
        border: none;
    }

    QComboBox QAbstractItemView {
        background-color: #444444;
        color: #ffffff;
        selection-background-color: #666666;
    }

    QCheckBox {
        color: #ffffff;
        spacing: 5px;
    }

    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border: 1px solid #555555;
        border-radius: 2px;
        background-color: #444444;
    }

    QCheckBox::indicator:checked {
        background-color: #666666;
        border: 1px solid #777777;
    }

    QGroupBox {
        color: #ffffff;
        border: 1px solid #555555;
        border-radius: 4px;
        margin-top: 8px;
        padding-top: 8px;
        font-weight: bold;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 3px 0 3px;
    }

    QScrollBar:vertical {
        background: #2b2b2b;
        width: 12px;
        border: none;
    }

    QScrollBar::handle:vertical {
        background: #666666;
        border-radius: 6px;
        min-height: 20px;
    }

    QScrollBar::handle:vertical:hover {
        background: #888888;
    }

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        border: none;
        background: none;
    }

    QScrollBar:horizontal {
        background: #2b2b2b;
        height: 12px;
        border: none;
    }

    QScrollBar::handle:horizontal {
        background: #666666;
        border-radius: 6px;
        min-width: 20px;
    }

    QScrollBar::handle:horizontal:hover {
        background: #888888;
    }

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        border: none;
        background: none;
    }

    QProgressBar {
        background-color: #444444;
        border: 1px solid #555555;
        border-radius: 3px;
        text-align: center;
        color: #ffffff;
        height: 20px;
    }

    QProgressBar::chunk {
        background-color: #666666;
        border-radius: 2px;
    }

    QTabBar::tab {
        background-color: #444444;
        color: #ffffff;
        padding: 4px 16px;
        border: 1px solid #555555;
    }

    QTabBar::tab:selected {
        background-color: #666666;
        border: 1px solid #777777;
    }

    QTabBar::tab:hover {
        background-color: #555555;
    }

    QTabWidget::pane {
        border: 1px solid #555555;
    }

    QMenuBar {
        background-color: #2b2b2b;
        color: #ffffff;
        border-bottom: 1px solid #555555;
    }

    QMenuBar::item:selected {
        background-color: #666666;
    }

    QMenu {
        background-color: #2b2b2b;
        color: #ffffff;
        border: 1px solid #555555;
    }

    QMenu::item:selected {
        background-color: #666666;
    }

    QStatusBar {
        background-color: #2b2b2b;
        color: #ffffff;
        border-top: 1px solid #555555;
    }

    QToolTip {
        background-color: #151a21;
        color: #f5f7fa;
        border: 1px solid #8796a8;
        border-radius: 4px;
        padding: 7px 10px;
        font-size: 12px;
        font-weight: normal;
        opacity: 255;
    }

    QMessageBox QLabel {
        color: #ffffff;
    }

    QMessageBox QPushButton {
        min-width: 60px;
    }
'''
