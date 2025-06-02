from PyQt5.QtWidgets import QPushButton
from YuanAPI.YNameSpace import YAddWidgetAttribute
from YuanAPI.YAPIS import YAPIEngine
from YuanAPI import YNameSpace
from PyQt5.QtCore import Qt, QPoint, QRect, QEvent, QObject
from PyQt5.QtGui import QCursor

Y_NAMESPACE = YNameSpace

class SizeBox(QObject):
    def __init__(self, button, parent_widget):
        super().__init__()
        self.main_button = button
        self.parent_widget = parent_widget
        self.corner_buttons = {}
        self.create_resize_buttons()

        self._resizing = False
        self._resize_direction = None
        self.initial_geometry = QRect()
        self._drag_start_global_pos = QPoint()

    def create_resize_buttons(self):
        positions = {
            'top_left': (0, 0),
            'top_right': (self.main_button.width(), 0),
            'bottom_left': (0, self.main_button.height()),
            'bottom_right': (self.main_button.width(), self.main_button.height())
        }

        for name, (x, y) in positions.items():
            btn = QPushButton(self.parent_widget)
            btn.setStyleSheet(
                "background-color: #fff; border-radius: 0px; width: 5px; height: 5px; border: 0.5px solid black")
            btn.move(self.main_button.x() + x - 5, self.main_button.y() + y - 5)
            btn.setCursor(QCursor(self.get_resize_cursor(name)))
            btn.show()

            btn.mousePressEvent = lambda e, _btn=btn, _name=name: self.on_press_resize(e, _btn, _name)
            btn.mouseMoveEvent = self.on_move_resize
            btn.mouseReleaseEvent = lambda e, _btn=btn: self.on_release_resize(e, _btn)
            self.corner_buttons[name] = btn

    def get_resize_cursor(self, direction):
        cursors = {
            'top_left': Qt.SizeFDiagCursor,
            'top_right': Qt.SizeBDiagCursor,
            'bottom_left': Qt.SizeBDiagCursor,
            'bottom_right': Qt.SizeFDiagCursor
        }
        return cursors[direction]

    def on_press_resize(self, event, button, direction):
        if event.button() == Qt.LeftButton:
            self._resizing = True
            self._resize_direction = direction
            self.initial_geometry = self.main_button.geometry()
            self._drag_start_global_pos = event.globalPos()
            button.grabMouse()

    def on_move_resize(self, event):
        if self._resizing and self._resize_direction:
            current_global_pos = event.globalPos()
            delta = current_global_pos - self._drag_start_global_pos

            x = self.initial_geometry.x()
            y = self.initial_geometry.y()
            w = self.initial_geometry.width()
            h = self.initial_geometry.height()

            new_geo = self.calculate_new_geometry(x, y, w, h, delta)
            self.main_button.setGeometry(new_geo)
            self.update_resize_buttons()

    def calculate_new_geometry(self, x, y, w, h, delta):
        direction = self._resize_direction
        new_x, new_y, new_w, new_h = x, y, w, h

        if direction == 'top_left':
            new_w = max(w - delta.x(), 1)
            new_h = max(h - delta.y(), 1)
            new_x = x + (w - new_w)
            new_y = y + (h - new_h)
        elif direction == 'top_right':
            new_w = max(w + delta.x(), 1)
            new_h = max(h - delta.y(), 1)
            new_y = y + (h - new_h)
        elif direction == 'bottom_left':
            new_w = max(w - delta.x(), 1)
            new_h = max(h + delta.y(), 1)
            new_x = x + (w - new_w)
        elif direction == 'bottom_right':
            new_w = max(w + delta.x(), 1)
            new_h = max(h + delta.y(), 1)

        return QRect(new_x, new_y, new_w, new_h)

    def on_release_resize(self, event, button):
        self._resizing = False
        button.releaseMouse()

    def update_resize_buttons(self):
        m = self.main_button
        self.corner_buttons['top_left'].move(m.x() - 5, m.y() - 5)
        self.corner_buttons['top_right'].move(m.x() + m.width() - 5, m.y() - 5)
        self.corner_buttons['bottom_left'].move(m.x() - 5, m.y() + m.height() - 5)
        self.corner_buttons['bottom_right'].move(m.x() + m.width() - 5, m.y() + m.height() - 5)

    def eventFilter(self, source, event):
        if source == self.main_button:
            if event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self._dragging = True
                    self._start_drag_main_button_pos = self.main_button.pos()
                    self._drag_start_global_pos = event.globalPos()
                    return True
            elif event.type() == QEvent.MouseMove:
                if self._dragging:
                    current_global_pos = event.globalPos()
                    delta = current_global_pos - self._drag_start_global_pos
                    new_pos = self._start_drag_main_button_pos + delta
                    self.main_button.move(new_pos)
                    self.update_resize_buttons()
                    return True
            elif event.type() == QEvent.MouseButtonRelease:
                if event.button() == Qt.LeftButton:
                    self._dragging = False
                    return True
        return super().eventFilter(source, event)

    def show_resize_controls(self):
        for btn in self.corner_buttons.values():
            btn.show()

    def hide_resize_controls(self):
        for btn in self.corner_buttons.values():
            btn.hide()

    def destroy_resize_controls(self):
        for btn in self.corner_buttons.values():
            btn.deleteLater()
        self.corner_buttons.clear()


class _YuGM_(YAddWidgetAttribute):
    def __init__(self, raw, widget):
        super().__init__(raw, widget)
        self.api = YAPIEngine(raw)

    def realize(self, value):
        return {"dragWidget": lambda: self.make_draggable(self.api.globals.getGlobals(self.api.string(value))),
                "sizeBox": lambda: self.sizeBox(value)}

    def sizeBox(self, value):
        self.api.globals.globals(self.api.string(value[0]),
                                 SizeBox(self.api.globals.getGlobals(self.api.string(value[1])), self.raw))

    @staticmethod
    def make_draggable(widget):
        original_mouse_press = widget.mousePressEvent
        original_mouse_move = widget.mouseMoveEvent
        original_mouse_release = widget.mouseReleaseEvent

        def mousePressEvent(event):
            if event.button() == Qt.LeftButton:
                widget._drag_pos = event.globalPos() - widget.frameGeometry().topLeft()
            if callable(original_mouse_press):
                original_mouse_press(event)  # 调用原始的事件
            else:
                event.ignore()

        def mouseMoveEvent(event):
            if event.buttons() & Qt.LeftButton and hasattr(widget, '_drag_pos'):
                widget.move(event.globalPos() - widget._drag_pos)
            if callable(original_mouse_move):
                original_mouse_move(event)
            else:
                event.ignore()

        def mouseReleaseEvent(event):
            if hasattr(widget, '_drag_pos'):
                widget._drag_pos = None
            if callable(original_mouse_release):
                original_mouse_release(event)
            else:
                event.ignore()

        widget.mousePressEvent = mousePressEvent
        widget.mouseMoveEvent = mouseMoveEvent
        widget.mouseReleaseEvent = mouseReleaseEvent
