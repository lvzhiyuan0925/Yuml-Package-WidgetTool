from PyQt5.QtWidgets import QPushButton, QLabel, QApplication
from YuanAPI.YNameSpace import YAddWidgetAttribute, YLoad
from YuanAPI.YAPIS import YAPIEngine
from YuanAPI import YNameSpace
from PyQt5.QtCore import Qt, QPoint, QRect, QEvent, QObject
from PyQt5.QtGui import QCursor

Y_NAMESPACE = YNameSpace


class Init(YLoad):
    def __init__(self, raw):
        super().__init__(raw)
        self.api = YAPIEngine(raw)
        self.api.globals.globals("Qt", Qt)


class SnapLineManager:
    """辅助线管理器，使用QLabel实现"""

    def __init__(self, parent, qss="background-color: #FF5722;"):
        self.parent = parent
        self.style = qss
        self.snap_lines = {}  # 存储所有辅助线 {line_key: QLabel}

    def create_line(self, line_type, position):
        """创建辅助线"""
        key = f"{line_type}_{position}"
        if key in self.snap_lines:
            return self.snap_lines[key]

        line = QLabel(self.parent)
        line.setAttribute(Qt.WA_TransparentForMouseEvents)
        line.setStyleSheet(self.style)
        line.hide()

        # 设置初始位置和大小
        if line_type == 'x':  # 垂直线
            line.setFixedWidth(1)
            line.setFixedHeight(self.parent.height())
            line.move(position, 0)
        else:  # 水平线
            line.setFixedHeight(1)
            line.setFixedWidth(self.parent.width())
            line.move(0, position)

        self.snap_lines[key] = line
        return line

    def show_line(self, line_type, position):
        """显示指定辅助线"""
        line = self.create_line(line_type, position)
        # 更新辅助线尺寸（父窗口大小可能已改变）
        if line_type == 'x':
            line.setFixedHeight(self.parent.height())
            line.move(position, 0)
        else:
            line.setFixedWidth(self.parent.width())
            line.move(0, position)
        line.show()

    def hide_line(self, line_type, position):
        """隐藏指定辅助线"""
        key = f"{line_type}_{position}"
        if key in self.snap_lines:
            self.snap_lines[key].hide()

    def hide_all(self):
        """隐藏所有辅助线"""
        for line in self.snap_lines.values():
            line.hide()

    def update_size(self):
        """更新所有辅助线尺寸"""
        for key, line in self.snap_lines.items():
            line_type, pos = key.split('_')
            pos = int(pos)
            if line_type == 'x':
                line.setFixedHeight(self.parent.height())
                line.move(pos, 0)
            else:
                line.setFixedWidth(self.parent.width())
                line.move(0, pos)


class SizeBox(QObject):
    def __init__(self, widget, parent_widget,
                 style: str = "background-color: #fff; border-radius: 0px;"
                              "width: 5px; height: 5px; border: 0.5px solid black"):
        super().__init__()
        self.button_style = style
        self.main_button = widget
        self.parent_widget = parent_widget
        self.corner_buttons = {}
        self.create_resize_buttons()
        self._start_drag_main_button_pos = None
        self._dragging = None
        self._resizing = False
        self._resize_direction = None
        self.initial_geometry = QRect()
        self._drag_start_global_pos = QPoint()

    def create_resize_buttons(self):
        positions = {
            'top_left': (0, 0),
            'top_right': (self.main_button.width(), 0),
            'bottom_left': (0, self.main_button.height()),
            'bottom_right': (self.main_button.width(), self.main_button.height()),
            'top': (self.main_button.width() // 2, 0),
            'bottom': (self.main_button.width() // 2, self.main_button.height()),
            'left': (0, self.main_button.height() // 2),
            'right': (self.main_button.width(), self.main_button.height() // 2),
        }

        for name, (x, y) in positions.items():
            btn = QPushButton(self.parent_widget)
            btn.setStyleSheet(self.button_style)
            btn.move(self.main_button.x() + x - 5, self.main_button.y() + y - 5)
            btn.setCursor(QCursor(self.get_resize_cursor(name)))
            btn.show()

            btn.mousePressEvent = lambda e, _btn=btn, _name=name: self.on_press_resize(e, _btn, _name)
            btn.mouseMoveEvent = self.on_move_resize
            btn.mouseReleaseEvent = lambda e, _btn=btn: self.on_release_resize(e, _btn)
            self.corner_buttons[name] = btn

    @staticmethod
    def get_resize_cursor(direction):
        cursors = {
            'top_left': Qt.SizeFDiagCursor,
            'top_right': Qt.SizeBDiagCursor,
            'bottom_left': Qt.SizeBDiagCursor,
            'bottom_right': Qt.SizeFDiagCursor,
            'top': Qt.SizeVerCursor,
            'bottom': Qt.SizeVerCursor,
            'left': Qt.SizeHorCursor,
            'right': Qt.SizeHorCursor
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
            self.updatePos()

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
        elif direction == 'top':
            new_h = max(h - delta.y(), 1)
            new_y = y + (h - new_h)
        elif direction == 'bottom':
            new_h = max(h + delta.y(), 1)
        elif direction == 'left':
            new_w = max(w - delta.x(), 1)
            new_x = x + (w - new_w)
        elif direction == 'right':
            new_w = max(w + delta.x(), 1)

        return QRect(new_x, new_y, new_w, new_h)

    def on_release_resize(self, _event, button):
        self._resizing = False
        button.releaseMouse()

    def updatePos(self):
        m = self.main_button
        self.corner_buttons['top_left'].move(m.x() - 5, m.y() - 5)
        self.corner_buttons['top_right'].move(m.x() + m.width() - 5, m.y() - 5)
        self.corner_buttons['bottom_left'].move(m.x() - 5, m.y() + m.height() - 5)
        self.corner_buttons['bottom_right'].move(m.x() + m.width() - 5, m.y() + m.height() - 5)

        self.corner_buttons['top'].move(m.x() + m.width() // 2 - 5, m.y() - 5)
        self.corner_buttons['bottom'].move(m.x() + m.width() // 2 - 5, m.y() + m.height() - 5)
        self.corner_buttons['left'].move(m.x() - 5, m.y() + m.height() // 2 - 5)
        self.corner_buttons['right'].move(m.x() + m.width() - 5, m.y() + m.height() // 2 - 5)

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
                    self.updatePos()
                    return True
            elif event.type() == QEvent.MouseButtonRelease:
                if event.button() == Qt.LeftButton:
                    self._dragging = False
                    return True
        return super().eventFilter(source, event)

    def show(self):
        for btn in self.corner_buttons.values():
            btn.show()

    def hide(self):
        for btn in self.corner_buttons.values():
            btn.hide()

    def destroy(self):
        for btn in self.corner_buttons.values():
            btn.deleteLater()
        self.corner_buttons.clear()


class _YuGM_(YAddWidgetAttribute):
    def __init__(self, raw, widget_type, widget):
        super().__init__(raw, widget_type, widget)
        self.api = YAPIEngine(raw)

    def realize(self, value):
        def dragWidget():
            for key, v in value.items():
                if isinstance(v, list):
                    value[key] = [self.api.string(item) for item in v]
                else:
                    value[key] = self.api.string(v)

            self.make_draggable(self.widget, parent_window=self.raw, **value)
        return {"dragWidget": dragWidget,
                "sizeBox": lambda: self.sizeBox(value)}

    def sizeBox(self, value):
        self.api.globals.globals(self.api.string(value), SizeBox(self.widget, self.raw))

    @staticmethod
    def make_draggable(widget, parent_window=None, snap_x=None, snap_y=None, snap_threshold=10,
                       style="background-color: #FF5722;",
                       allow_horizontal_drag=[None, True], allow_vertical_drag=[None, True]):
        """
        使部件可拖拽，并添加辅助线吸附功能和视觉辅助线

        参数:
            widget: 要使其可拖拽的部件
            parent_window: 父窗口，用于放置辅助线
            snap_x: x轴辅助线坐标列表 (例如 [100, 200, 300])
            snap_y: y轴辅助线坐标列表 (例如 [50, 150, 250])
            snap_threshold: 吸附阈值(像素)，默认10px
            style: 辅助线样式
            allow_horizontal_drag: 列表形式 [键名, 默认是否允许]，如 [Qt.Key_Shift, False]
            allow_vertical_drag: 同上
        """
        snap_x = snap_x if isinstance(snap_x, (list, tuple)) else [snap_x] if snap_x is not None else []
        snap_y = snap_y if isinstance(snap_y, (list, tuple)) else [snap_y] if snap_y is not None else []

        original_mouse_press = widget.mousePressEvent
        original_mouse_move = widget.mouseMoveEvent
        original_mouse_release = widget.mouseReleaseEvent

        snap_manager = None
        if parent_window:
            if not hasattr(parent_window, '_snap_manager'):
                parent_window._snap_manager = SnapLineManager(parent_window, style)
            snap_manager = parent_window._snap_manager

        widget._current_snap_lines = []

        def is_drag_allowed(option):
            key, default = option
            if key is None:
                return default
            keys = QApplication.queryKeyboardModifiers()
            if default:
                return keys & key  # 只有按下时允许
            else:
                return not (keys & key)  # 按下时禁用

        def mousePressEvent(event):
            if event.button() == Qt.LeftButton:
                widget._drag_pos = event.globalPos() - widget.frameGeometry().topLeft()
                widget._original_pos = widget.pos()
                widget._current_snap_lines = []
                if snap_manager:
                    snap_manager.hide_all()

            if callable(original_mouse_press):
                original_mouse_press(event)
            else:
                event.ignore()

        def mouseMoveEvent(event):
            if event.buttons() & Qt.LeftButton and hasattr(widget, '_drag_pos'):
                new_pos = event.globalPos() - widget._drag_pos

                horizontal_allowed = is_drag_allowed(allow_horizontal_drag)
                vertical_allowed = is_drag_allowed(allow_vertical_drag)

                if not horizontal_allowed:
                    new_pos.setX(widget.x())
                if not vertical_allowed:
                    new_pos.setY(widget.y())

                current_snap_lines = []
                snapped = False

                if snap_x or snap_y:
                    left = new_pos.x()
                    top = new_pos.y()
                    center_x = new_pos.x() + widget.width() // 2
                    center_y = new_pos.y() + widget.height() // 2
                    right = new_pos.x() + widget.width()
                    bottom = new_pos.y() + widget.height()

                    if horizontal_allowed:
                        for line in snap_x:
                            if abs(left - line) < snap_threshold:
                                new_pos.setX(line)
                                current_snap_lines.append(('x', line))
                                snapped = True
                            elif abs(center_x - line) < snap_threshold:
                                new_pos.setX(line - widget.width() // 2)
                                current_snap_lines.append(('x', line))
                                snapped = True
                            elif abs(right - line) < snap_threshold:
                                new_pos.setX(line - widget.width())
                                current_snap_lines.append(('x', line))
                                snapped = True

                    if vertical_allowed:
                        for line in snap_y:
                            if abs(top - line) < snap_threshold:
                                new_pos.setY(line)
                                current_snap_lines.append(('y', line))
                                snapped = True
                            elif abs(center_y - line) < snap_threshold:
                                new_pos.setY(line - widget.height() // 2)
                                current_snap_lines.append(('y', line))
                                snapped = True
                            elif abs(bottom - line) < snap_threshold:
                                new_pos.setY(line - widget.height())
                                current_snap_lines.append(('y', line))
                                snapped = True

                if snap_manager:
                    for line_type, pos in widget._current_snap_lines:
                        snap_manager.hide_line(line_type, pos)
                    for line_type, pos in current_snap_lines:
                        snap_manager.show_line(line_type, pos)
                    widget._current_snap_lines = current_snap_lines

                widget.move(new_pos)

            if callable(original_mouse_move):
                original_mouse_move(event)
            else:
                event.ignore()

        def mouseReleaseEvent(event):
            if hasattr(widget, '_drag_pos'):
                widget._drag_pos = None
                widget._original_pos = None
                if snap_manager:
                    snap_manager.hide_all()
                    widget._current_snap_lines = []

            if callable(original_mouse_release):
                original_mouse_release(event)
            else:
                event.ignore()

        widget.mousePressEvent = mousePressEvent
        widget.mouseMoveEvent = mouseMoveEvent
        widget.mouseReleaseEvent = mouseReleaseEvent

        return snap_manager
