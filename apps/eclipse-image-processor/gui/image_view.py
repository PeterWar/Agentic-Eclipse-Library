"""Fit/native image viewport; zoom and pan only repaint the visible source ROI."""
import math
from PySide6.QtCore import QEvent, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QApplication, QSizePolicy, QWidget


class ImageView(QWidget):
    circle_center_requested = Signal(int, int)
    view_changed = Signal()
    background_point_added = Signal(int,int)
    background_point_removed = Signal(int,int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.zoom = None
        self.native_w = self.native_h = 0
        self.circle_x = self.circle_y = self.circle_r = None
        self.disk_overlay_visible = True
        self._preview = self._native = None
        self._preview_pixels = self._native_pixels = None
        self._center = QPointF()
        self._press = None
        self._dragged = False
        self._background_points=[]
        self._background_radius=0
        self._background_edit=False
        self.pending = False
        self.pending_message = None
        self.setMinimumSize(1,1)
        self.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Ignored)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName('Image preview; drag or use arrow keys to pan at 100% or 200%')

    @staticmethod
    def _image(pixels):
        h,w=pixels.shape[:2]
        fmt=QImage.Format.Format_RGB888 if pixels.ndim == 3 else QImage.Format.Format_Grayscale8
        return QImage(pixels.data,w,h,pixels.strides[0],fmt)

    def clear(self):
        self.disk_overlay_visible = True
        self._preview = self._native = None
        self._preview_pixels = self._native_pixels = None
        self.native_w = self.native_h = 0
        self.zoom = None
        self.pending = False
        self.update()
        self.view_changed.emit()

    def set_images(self, preview, native, native_w, native_h):
        # Keep NumPy owners alive: QImage wraps their uint8 memory without copying.
        if (native_w,native_h) != (self.native_w,self.native_h):
            self._center=QPointF(native_w/2,native_h/2)
        self.native_w,self.native_h=native_w,native_h
        self._preview_pixels,self._native_pixels=preview,native
        self._preview=self._image(preview)
        self._native=self._image(native) if native is not None else None
        self._clamp_center()
        self._update_cursor()
        self.update()
        self.view_changed.emit()

    def set_circle_parameters(self,x,y,r,native_w=None,native_h=None):
        self.circle_x,self.circle_y,self.circle_r=x,y,r
        self.update()

    def set_disk_overlay_visible(self, visible):
        self.disk_overlay_visible = bool(visible)
        self.update()

    def set_zoom(self, zoom):
        if zoom not in (None,1,2):
            raise ValueError('Supported zoom levels are Fit, 100% and 200%')
        self.zoom=zoom
        self._clamp_center()
        self._update_cursor()
        self.update()
        self.view_changed.emit()

    def set_pending(self, pending, message=None):
        self.pending=pending
        self.pending_message=message
        self.update()
        self.view_changed.emit()

    def set_background_samples(self,points,radius,editing):
        self._background_points=points
        self._background_radius=radius
        self._background_edit=editing
        self._update_cursor();self.update()

    def _update_cursor(self):
        self.setCursor(Qt.CursorShape.CrossCursor if self._background_edit else
                       Qt.CursorShape.OpenHandCursor if self.zoom is not None and self._native is not None else
                       Qt.CursorShape.ArrowCursor)

    def _clamp_center(self):
        if self.zoom is None or self._native is None:
            return
        scale=self.zoom/self.devicePixelRatioF()
        half_w=max(1,self.width()-2)/(2*scale)
        half_h=max(1,self.height()-2)/(2*scale)
        self._center=QPointF(
            self.native_w/2 if 2*half_w>=self.native_w else min(self.native_w-half_w,max(half_w,self._center.x())),
            self.native_h/2 if 2*half_h>=self.native_h else min(self.native_h-half_h,max(half_h,self._center.y())))

    def image_rect(self):
        """Native image edges in logical viewport coordinates; zoom uses physical pixels."""
        if not self.native_w or not self.native_h:
            return QRectF()
        viewport=QRectF(self.rect()).adjusted(1,1,-1,-1)
        if self.zoom is None or self._native is None:
            scale=min(viewport.width()/self.native_w,viewport.height()/self.native_h)
            size=QRectF(0,0,self.native_w*scale,self.native_h*scale)
            size.moveCenter(viewport.center())
            return size
        dpr=self.devicePixelRatioF()
        scale=self.zoom/dpr
        x=round((viewport.center().x()-self._center.x()*scale)*dpr)/dpr
        y=round((viewport.center().y()-self._center.y()*scale)*dpr)/dpr
        return QRectF(x,y,self.native_w*scale,self.native_h*scale)

    def visible_image(self):
        """Return image/target/source rectangles, bounded by viewport size at any zoom."""
        image=self._native if self.zoom is not None and self._native is not None else self._preview
        if image is None:
            return None,QRectF(),QRectF()
        rect=self.image_rect()
        visible=rect.intersected(QRectF(self.rect()).adjusted(1,1,-1,-1))
        if visible.isEmpty():
            return None,QRectF(),QRectF()
        source=QRectF((visible.x()-rect.x())*image.width()/rect.width(),
                      (visible.y()-rect.y())*image.height()/rect.height(),
                      visible.width()*image.width()/rect.width(),
                      visible.height()*image.height()/rect.height())
        return image,visible,source

    def paintEvent(self,event):
        painter=QPainter(self)
        painter.fillRect(self.rect(),QColor('#1c1c1c'))
        image,target,source=self.visible_image()
        if image is not None:
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform,self.zoom is None or self._native is None)
            painter.drawImage(target,image,source)
            if self.disk_overlay_visible and self.circle_r is not None:
                rect=self.image_rect()
                sx,sy=rect.width()/self.native_w,rect.height()/self.native_h
                center=QPointF(rect.x()+(self.circle_x+.5)*sx,rect.y()+(self.circle_y+.5)*sy)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setPen(QPen(QColor(255,50,50,220),2))
                painter.drawEllipse(center,self.circle_r*sx,self.circle_r*sy)
                painter.drawLine(center+QPointF(-6,0),center+QPointF(6,0))
                painter.drawLine(center+QPointF(0,-6),center+QPointF(0,6))
            if self._background_edit and self.circle_x is not None:
                rect=self.image_rect();sx=rect.width()/self.native_w;sy=rect.height()/self.native_h
                center=QPointF(rect.x()+(self.circle_x+.5)*sx,rect.y()+(self.circle_y+.5)*sy)
                painter.setPen(QPen(QColor('#ffcc55'),1,Qt.PenStyle.DashLine))
                painter.drawEllipse(center,self._background_radius*sx,self._background_radius*sy)
                painter.setPen(QPen(QColor('#66ff99'),1))
                for x,y in self._background_points:
                    point=QPointF(rect.x()+(x+.5)*sx,rect.y()+(y+.5)*sy)
                    if self.rect().contains(point.toPoint()):painter.drawRect(QRectF(point.x()-3,point.y()-3,6,6))
        if self.zoom is not None and (self.pending or self._native is None):
            message=self.pending_message or ('Updating native view…' if self._native is not None else 'Preparing native resolution…')
            box=QRectF(8,8,min(self.width()-16,280),26)
            painter.fillRect(box,QColor(20,20,20,230))
            painter.setPen(QColor('#eeeeee'))
            painter.drawText(box,Qt.AlignmentFlag.AlignCenter,message)
        painter.setPen(QColor('#333333'))
        painter.drawRect(self.rect().adjusted(0,0,-1,-1))

    def _pan(self,delta):
        if self.zoom is None or self._native is None:
            return
        scale=self.zoom/self.devicePixelRatioF()
        self._center-=delta/scale
        self._clamp_center()
        self.update()

    def mousePressEvent(self,event):
        if event.button() in (Qt.MouseButton.LeftButton,Qt.MouseButton.MiddleButton,Qt.MouseButton.RightButton):
            self.setFocus()
            self._press=event.position()
            self._last=event.position()
            self._dragged=False
            self._pan_allowed=(self.zoom is not None and self._native is not None and
                (event.button() == Qt.MouseButton.MiddleButton or
                 (event.button() == Qt.MouseButton.LeftButton and not self._background_edit and not event.modifiers() & Qt.KeyboardModifier.ControlModifier)))
            event.accept()

    def mouseMoveEvent(self,event):
        if self._press is not None and self._pan_allowed:
            if (event.position()-self._press).manhattanLength() >= QApplication.startDragDistance():
                self._dragged=True
            if self._dragged:
                self._pan(event.position()-self._last)
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                self._last=event.position()
            event.accept()

    def mouseReleaseEvent(self,event):
        if self._press is not None:
            if not self._dragged and event.button() in (Qt.MouseButton.LeftButton,Qt.MouseButton.RightButton) and self._preview is not None:
                rect=self.image_rect()
                pos=event.position()
                if rect.contains(pos) and pos.x()<rect.right() and pos.y()<rect.bottom():
                    x=min(self.native_w-1,max(0,math.floor((pos.x()-rect.x())*self.native_w/rect.width())))
                    y=min(self.native_h-1,max(0,math.floor((pos.y()-rect.y())*self.native_h/rect.height())))
                    if event.button() == Qt.MouseButton.RightButton:
                        if self._background_edit:self.background_point_removed.emit(x,y)
                    elif event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                        self.circle_center_requested.emit(x,y)
                    elif self._background_edit:self.background_point_added.emit(x,y)
            self._press=None
            self._update_cursor()
            event.accept()

    def wheelEvent(self,event):
        if self.zoom is None or self._native is None:
            event.ignore()
            return
        delta=QPointF(event.pixelDelta()) if not event.pixelDelta().isNull() else QPointF(event.angleDelta())*(80/120)
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            delta=QPointF(delta.y(),delta.x())
        self._pan(delta)
        event.accept()

    def keyPressEvent(self,event):
        directions={Qt.Key.Key_Left:QPointF(80,0),Qt.Key.Key_Right:QPointF(-80,0),
                    Qt.Key.Key_Up:QPointF(0,80),Qt.Key.Key_Down:QPointF(0,-80)}
        if event.key() in directions and self.zoom is not None:
            self._pan(directions[event.key()]);event.accept()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self._clamp_center()
        self.view_changed.emit()

    def event(self,event):
        result=super().event(event)
        if event.type() == QEvent.Type.DevicePixelRatioChange and hasattr(self,'zoom'):
            self._clamp_center()
            self.update()
            self.view_changed.emit()
        return result
