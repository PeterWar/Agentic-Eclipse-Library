"""UI widget factories for creating sliders, inputs, and groups."""

from typing import Optional, Tuple
import math

from gui.components import ScrollSafeSlider

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


def set_parameter_title(label, text):
    """Keep a trailing unit/qualifier together on the second line if needed."""
    label.ensurePolished()
    name, separator, qualifier = text.partition(' (')
    if separator and label.fontMetrics().horizontalAdvance(text) > label.width():
        text = name + '\n(' + qualifier
    label.setText(text)


def create_slider(
    label_text: str,
    min_v: int,
    max_v: int,
    default_v: int,
    target_layout: QVBoxLayout,
    tooltip: Optional[str] = None,
    on_release_callback=None,
    divisor=1,
    formatter=None,
) -> Tuple[QSlider, QLineEdit]:
    """Create one compact row with a physical-value editor and slider."""
    row = QHBoxLayout()
    lbl_name = QLabel(label_text)
    if tooltip:
        lbl_name.setToolTip(tooltip)

    lbl_val = QLineEdit(str(default_v))
    lbl_val.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
    if tooltip:
        lbl_val.setToolTip(tooltip)

    row.addWidget(lbl_name)

    slider = ScrollSafeSlider(Qt.Orientation.Horizontal)
    slider.setRange(min_v, max_v)
    slider.setValue(default_v)
    if tooltip:
        slider.setToolTip(tooltip)

    slider.value_label = lbl_val
    slider.title_label = lbl_name
    slider.display_divisor = divisor
    slider.display_formatter = formatter
    slider.valueChanged.connect(lambda _: update_slider_display(slider))
    if on_release_callback:
        slider.sliderReleased.connect(on_release_callback)

    container = QWidget()
    container.setLayout(row)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(7)
    lbl_name.setFixedWidth(126)
    lbl_name.setWordWrap(True)
    lbl_name.setStyleSheet("color: #bbbbbb; background: transparent; font-size: 11px;")
    set_parameter_title(lbl_name, label_text)
    lbl_val.setFixedWidth(58)
    lbl_val.setAlignment(Qt.AlignmentFlag.AlignRight)
    lbl_val.setStyleSheet("""
        QLineEdit { color: #dddddd; background: transparent; border: 1px solid transparent;
                    border-radius: 2px; padding: 2px; font-size: 11px; }
        QLineEdit:hover { border-color: #666666; }
        QLineEdit:focus { background: #252525; border-color: #999999; }
        QLineEdit:disabled { color: #777777; }
    """)
    row.addWidget(slider, 1)
    row.addWidget(lbl_val)
    slider.setMinimumWidth(70)
    slider.setStyleSheet("""
        QSlider { background: transparent; min-height: 24px; }
        QSlider::groove:horizontal { height: 3px; background: #252525;
            border: 1px solid #666666; border-radius: 2px; }
        QSlider::sub-page:horizontal { background: transparent; }
        QSlider::handle:horizontal { width: 10px; margin: -5px 0;
            background: #b0b0b0; border: 1px solid #161616; border-radius: 4px; }
        QSlider::handle:horizontal:hover { background: #dddddd; }
        QSlider::handle:horizontal:disabled { background: #626262; }
    """)
    slider.setProperty('reset_value', default_v)
    slider.parameter_row = container
    lbl_val.setAccessibleName(label_text)
    slider.setAccessibleName(label_text)
    def commit_value():
        if not slider.isEnabled():
            update_slider_display(slider)
            return
        try:
            zero_label = slider.property('zero_label')
            text = lbl_val.text().strip()
            physical = (0. if zero_label and text.casefold() == zero_label.casefold()
                        else float(text.replace(',', '.')))
            if not math.isfinite(physical):
                raise ValueError
            if slider.display_formatter:
                tick = min(range(slider.minimum(), slider.maximum()+1),
                           key=lambda v: abs(float(slider.display_formatter(v))-physical))
                if not math.isclose(float(slider.display_formatter(tick)), physical, rel_tol=1e-9):
                    raise ValueError
            else:
                tick = round(physical*slider.display_divisor)
            if not slider.minimum() <= tick <= slider.maximum():
                raise ValueError
            slider.setValue(tick)
        except (ValueError, OverflowError):
            pass
        update_slider_display(slider)
    lbl_val.editingFinished.connect(commit_value)
    update_slider_display(slider)
    target_layout.addWidget(container)
    return slider, lbl_val


def create_slider_float(
    label_text: str,
    min_v: int,
    max_v: int,
    default_v: int,
    divisor: float,
    target_layout: QVBoxLayout,
    tooltip: Optional[str] = None,
    on_release_callback=None,
) -> Tuple[QSlider, QLineEdit]:
    """Create a slider displaying its physical value instead of integer ticks."""
    return create_slider(
        label_text, min_v, max_v, default_v, target_layout,
        tooltip=tooltip, on_release_callback=on_release_callback, divisor=divisor,
    )


def update_slider_display(slider, *, divisor=None, formatter=None, title=None):
    """Refresh a physical value, including when a mode changes at the same tick."""
    if divisor is not None:
        slider.display_divisor = divisor
    if formatter is not None:
        slider.display_formatter = formatter
    if title is not None:
        set_parameter_title(slider.title_label, title)
    value = slider.value()
    text = (slider.display_formatter(value) if slider.display_formatter else
            f"{value / slider.display_divisor:.10f}".rstrip('0').rstrip('.'))
    if value == 0 and slider.property("zero_label"):
        text = slider.property("zero_label")
    slider.value_label.setText(text)
    slider.value_label.ensurePolished()
    slider.value_label.setFixedWidth(max(58, slider.value_label.fontMetrics().horizontalAdvance(text) + 12))


def create_stepper_input(
    label_text: str,
    default_value: str,
    target_layout: QHBoxLayout,
    tooltip: Optional[str] = None,
    on_change_callback=None,
) -> QLineEdit:
    """Create a stepper input with +/- buttons."""
    vbox = QVBoxLayout()
    vbox.setSpacing(3)
    lbl = QLabel(label_text)
    lbl.setStyleSheet("color: #aaa; font-size: 11px; font-weight: bold;")
    if tooltip:
        lbl.setToolTip(tooltip)
    vbox.addWidget(lbl)

    row = QHBoxLayout()
    row.setSpacing(3)

    btn_minus = QPushButton("−")
    btn_minus.setToolTip(f"Decrease {label_text.rstrip(':')} by 1. {tooltip or ''}".strip())
    btn_minus.setFixedSize(24, 24)
    btn_minus.setAutoRepeat(True)
    btn_minus.setAutoRepeatInterval(40)
    btn_minus.setAutoRepeatDelay(280)

    txt = QLineEdit(default_value)
    txt.setStyleSheet("""
        QLineEdit { background: #303030; color: #dddddd; border: 1px solid #505050;
                    border-radius: 2px; padding: 3px 2px; font-size: 11px; }
        QLineEdit:focus { border-color: #999999; }
    """)
    if tooltip:
        txt.setToolTip(tooltip)

    btn_plus = QPushButton("+")
    btn_plus.setToolTip(f"Increase {label_text.rstrip(':')} by 1. {tooltip or ''}".strip())
    btn_plus.setFixedSize(24, 24)
    btn_plus.setAutoRepeat(True)
    btn_plus.setAutoRepeatInterval(40)
    btn_plus.setAutoRepeatDelay(280)

    def step_val(delta: int):
        try:
            curr = int(txt.text())
        except ValueError:
            curr = 0
        txt.setText(str(max(0, curr + delta)))
        if on_change_callback:
            on_change_callback()

    btn_minus.clicked.connect(lambda: step_val(-1))
    btn_plus.clicked.connect(lambda: step_val(1))

    row.addWidget(btn_minus)
    row.addWidget(txt)
    row.addWidget(btn_plus)
    vbox.addLayout(row)
    target_layout.addLayout(vbox)
    return txt


def create_filter_group(group_title: str, control_layout: QVBoxLayout) -> QVBoxLayout:
    """Create a labeled filter group with header."""
    group_frame = QFrame()
    group_layout = QVBoxLayout(group_frame)
    group_layout.setContentsMargins(0, 10, 0, 0)
    group_layout.setSpacing(0)

    group_header = QFrame()
    group_header.setStyleSheet("""
        QFrame {
            background-color: #303030;
            border-top: 1px solid #3d3d3d;
            border-bottom: none;
        }
    """)
    header_layout = QHBoxLayout(group_header)
    header_layout.setContentsMargins(8, 4, 8, 4)

    title_label = QLabel(group_title.upper())
    group_help={
        'RADIAL ENHANCEMENT':'Radial normalization uses the configured reference disk geometry.',
        'RADIAL HISTOGRAM EQUALIZATION':'Adjust contrast by ranking working-input intensities within radial distributions.',
        'MULTI-SCALE / WAVELETS':'Extract contrast at multiple spatial scales from the shared working input, including enabled background equalization.',
        'SHARPENING':'Independent signed-detail layers; each starts from the shared working input, including enabled background equalization.',
        'PHOTOSHOP PRESENTATION':'Automatic exposure with manual EV adjustment for Photoshop layers. Screen and JPEG follow it only when Preview PSB presentation is on; the main TIFF is unchanged.',
    }
    title_label.setToolTip(group_help[group_title])
    title_label.setStyleSheet("""
        QLabel {
            background: transparent;
            color: #aaaaaa;
            font-weight: 600;
            font-size: 10px;
            letter-spacing: 0.8px;
        }
    """)
    header_layout.addWidget(title_label)
    group_layout.addWidget(group_header)

    inner_container = QWidget()
    inner_layout = QVBoxLayout(inner_container)
    inner_layout.setContentsMargins(0, 2, 0, 0)
    group_layout.addWidget(inner_container)
    control_layout.addWidget(group_frame)
    return inner_layout


def create_dyadic_slider(
    label_text: str,
    min_exp: int,
    max_exp: int,
    default_exp: int,
    target_layout: QVBoxLayout,
    tooltip: Optional[str] = None,
    on_release_callback=None,
) -> Tuple[QSlider, QLineEdit]:
    """Display the actual segment count while retaining power-of-two steps."""
    return create_slider(
        label_text, min_exp, max_exp, default_exp, target_layout,
        tooltip=tooltip, on_release_callback=on_release_callback,
        formatter=lambda exponent: str(2 ** exponent),
    )
