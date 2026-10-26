"""Shared sidebar controls, section widgets and in-window tooltips."""


from shiboken6 import isValid
from PySide6.QtCore import QEvent, QObject, QPointF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCursor, QPainter, QWheelEvent
from PySide6.QtWidgets import (
    QApplication,
    QAbstractScrollArea,
    QComboBox,
    QListView,
    QStyledItemDelegate,
    QSlider,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QToolTip,
)


def _scroll_sidebar(widget, event):
    """Forward wheel/trackpad motion without editing a parameter, even with focus."""
    parent = widget.parentWidget()
    while parent is not None:
        if isinstance(parent, QAbstractScrollArea):
            viewport = parent.viewport()
            forwarded = QWheelEvent(
                QPointF(viewport.mapFromGlobal(event.globalPosition().toPoint())),
                event.globalPosition(), event.pixelDelta(), event.angleDelta(),
                event.buttons(), event.modifiers(), event.phase(), event.inverted(),
                event.source(),
            )
            QApplication.sendEvent(viewport, forwarded)
            event.accept()
            return
        parent = parent.parentWidget()
    event.ignore()


class ScrollSafeSlider(QSlider):
    """A slider edited by dragging or keyboard; the wheel scrolls its panel."""

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.EnabledChange and hasattr(self, 'value_label'):
            self.value_label.setEnabled(self.isEnabled())
            self.title_label.setEnabled(self.isEnabled())

    def mouseDoubleClickEvent(self, event):
        default = self.property('reset_value')
        if default is not None and event.button() == Qt.MouseButton.LeftButton:
            self.setValue(max(self.minimum(), min(self.maximum(), default)))
            self.sliderReleased.emit()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event):
        _scroll_sidebar(self, event)


class ScrollSafeComboBox(QComboBox):
    """Keep sidebar scrolling from changing the selected algorithm."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Avoid the native popup's light top/bottom frame on the dark sidebar.
        self.setStyleSheet("QComboBox { combobox-popup: 0; }")
        view = QListView(self)
        view.setFrameShape(QFrame.Shape.NoFrame)
        view.setItemDelegate(QStyledItemDelegate(view))
        view.setStyleSheet("""
            QListView {
                background-color: #282828;
                color: #eeeeee;
                font-size: 11px;
                border: none;
                outline: 0;
            }
            QListView::item { padding: 6px 10px; border: none; }
            QListView::item:selected {
                background-color: #505050;
                color: #ffffff;
            }
        """)
        self.setView(view)


    def wheelEvent(self, event):
        _scroll_sidebar(self, event)


class InWindowTooltips(QObject):
    """Opaque child overlay: no native tooltip window or cross-app overlap."""

    class Panel(QWidget):
        def paintEvent(self, event):
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor("#151a21"))
            painter.setPen(QColor("#8796a8"))
            painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.panel = self.Panel(window)
        self.panel.setObjectName("inWindowTooltip")
        self.panel.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.panel.setAutoFillBackground(False)
        self.label = QLabel(self.panel)
        self.label.setTextFormat(Qt.TextFormat.PlainText)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("QLabel { color: #f5f7fa; background: transparent; border: none; font-size: 12px; font-weight: normal; }")
        self.panel.hide()
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.panel.hide)
        self.hover_delay_ms = 800
        self.hover_timer = QTimer(self)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self._show_pending)
        self.pending_widget = None
        self.pending_position = None
        QApplication.instance().installEventFilter(self)

    def _cancel_hover(self):
        self.hover_timer.stop()
        self.timer.stop()
        self.pending_widget = None
        self.panel.hide()

    def _schedule(self, widget, position):
        if widget is self.pending_widget:
            return
        self._cancel_hover()
        if widget.toolTip():
            self.pending_widget = widget
            self.pending_position = position
            self.hover_timer.start(self.hover_delay_ms)

    def _show_pending(self):
        widget = self.pending_widget
        if widget is not None and isValid(widget) and widget.isVisible():
            self.show_text(widget, self.pending_position)

    def show_text(self, widget, position):
        text = widget.toolTip()
        if not text:
            return
        width = min(420, max(1, self.window.width()-24))
        self.label.setFixedWidth(max(1, width-22))
        self.label.setText(text)
        height = min(self.window.height()-24,
                     self.label.heightForWidth(self.label.width())+18)
        self.panel.resize(width, max(24, height))
        self.label.setGeometry(11, 9, width-22, self.panel.height()-18)
        point = widget.mapTo(self.window, position)
        x = min(max(12, point.x()+12), self.window.width()-width-12)
        y = point.y()+20
        if y+self.panel.height() > self.window.height()-12:
            y = point.y()-self.panel.height()-16
        y = min(max(12, y), self.window.height()-self.panel.height()-12)
        self.panel.move(x, y)
        self.panel.raise_()
        self.panel.show()
        self.timer.start(10000)

    def detach(self):
        self._cancel_hover()
        QApplication.instance().removeEventFilter(self)

    def eventFilter(self, watched, event):
        if not isValid(self.window) or not isValid(self.panel):
            return False
        belongs = isinstance(watched, QWidget) and (watched is self.window or self.window.isAncestorOf(watched))
        kind = event.type()
        if kind == QEvent.Type.ToolTip and belongs:
            QToolTip.hideText()
            self._schedule(watched, event.pos())
            event.accept()
            return True
        if belongs and kind == QEvent.Type.Enter:
            self._schedule(watched, watched.mapFromGlobal(QCursor.pos()))
        if kind == QEvent.Type.Leave and watched is self.pending_widget:
            self._cancel_hover()
        if kind in (QEvent.Type.MouseButtonPress, QEvent.Type.Wheel,
                    QEvent.Type.ApplicationDeactivate):
            self._cancel_hover()
        if watched is self.pending_widget and kind == QEvent.Type.Hide:
            self._cancel_hover()
        if watched is self.window and kind in (QEvent.Type.Hide, QEvent.Type.Resize,
                                               QEvent.Type.Move, QEvent.Type.WindowDeactivate,
                                               QEvent.Type.Leave):
            self._cancel_hover()
        return False


PANEL_CONTENT_STYLE = """
    QWidget { background: #383838; border-radius: 0; }
    QComboBox { color: #dddddd; background: #333333; border: 1px solid #494949;
                border-radius: 2px; padding: 3px 6px; font-size: 11px; combobox-popup: 0; }
    QComboBox::drop-down { background: transparent; border: none; width: 16px; }
"""

BUTTON_STYLE = """
    QPushButton { background: #3c3c3c; color: #dddddd; border: 1px solid #555555;
                  border-radius: 3px; padding: 4px 6px; font-size: 11px; font-weight: 500; }
    QPushButton:hover { background: #494949; border-color: #777777; }
    QPushButton:pressed, QPushButton:checked { background: #575757; border-color: #999999; }
    QPushButton:disabled { background: #303030; color: #777777; border-color: #444444; }
"""


CHECKBOX_STYLE = """
                QCheckBox {
                    background: transparent;
                    color: #a0a0a0;
                    font-size: 11px;
                    font-weight: 600;
                    spacing: 5px;
                }
                QCheckBox:hover {
                    color: #ffffff;
                }
                QCheckBox::indicator {
                    width: 13px;
                    height: 13px;
                    border-radius: 2px;
                    border: 1px solid #4a4a4a;
                    background-color: #1e1e1e;
                }
                QCheckBox::indicator:hover {
                    border: 1px solid #707070;
                    background-color: #282828;
                }
                QCheckBox::indicator:checked {
                    background-color: #e5a00d;
                    border: 1px solid #f5b025;
                }
            """


class FullRowCheckBox(QCheckBox):
    """Make label and trailing row whitespace one consistent click target."""

    def hitButton(self, position):
        return self.rect().contains(position)


class CollapsibleSection(QWidget):
    """Collapsible UI container with optional filter enable/bypass checkbox."""

    toggled_active = Signal(bool)

    def __init__(
        self,
        title: str,
        has_checkbox: bool = False,
        is_expanded: bool = True,
        is_active: bool = True,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.title_text = title
        self.has_checkbox = has_checkbox
        self.is_expanded = is_expanded

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 2, 0, 2)
        main_layout.setSpacing(2)

        self.header_frame = QFrame()
        self.header_frame.setStyleSheet("QFrame { background: #303030; border: none; border-bottom: 1px solid #202020; }")
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(8, 4, 8, 4)
        header_layout.setSpacing(6)

        self.toggle_btn = QPushButton()
        self.toggle_btn.setToolTip(f"Expand or collapse {title} controls.")
        self.toggle_btn.setFlat(True)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setStyleSheet("QPushButton { color: #dddddd; background: transparent; border: none; text-align: left; font-size: 12px; font-weight: 500; padding: 2px 0; }")
        self.toggle_btn.clicked.connect(self.toggle_expanded)
        header_layout.addWidget(self.toggle_btn, stretch=1)

        if self.has_checkbox:
            self.chk_active = QCheckBox("Active")
            self.chk_active.setToolTip(f"Enable or bypass {title} without resetting its controls.")
            self.chk_active.setChecked(is_active)
            self.chk_active.setCursor(Qt.CursorShape.PointingHandCursor)
            self.chk_active.setStyleSheet(CHECKBOX_STYLE)
            self.chk_active.toggled.connect(self._on_active_toggled)
            header_layout.addWidget(self.chk_active)
        else:
            self.chk_active = None

        main_layout.addWidget(self.header_frame)

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet(PANEL_CONTENT_STYLE)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(8, 6, 8, 8)
        self.content_layout.setSpacing(2)
        self.content_widget.setVisible(self.is_expanded)
        # Note: We do NOT disable content_widget initially, even if not active.
        # Users should be able to configure filter parameters before enabling the filter.

        main_layout.addWidget(self.content_widget)
        self._update_header_text()

    def _update_header_text(self):
        arrow = "▼" if self.is_expanded else "▶"
        self.toggle_btn.setText(f"{arrow}  {self.title_text}")

    def toggle_expanded(self):
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)
        self._update_header_text()

    def _on_active_toggled(self, checked: bool):
        """Handle checkbox toggle. Sliders remain enabled for configuration."""
        # Note: We do NOT disable content_widget when unchecked.
        # This allows users to adjust filter parameters even when the filter is inactive.
        # The pipeline will skip disabled filters anyway.
        self.toggled_active.emit(checked)

    def is_filter_active(self) -> bool:
        if self.has_checkbox and self.chk_active is not None:
            return self.chk_active.isChecked()
        return True
