"""
DSL Loader - 将 DSL JSON 加载为 PyQt5 控件树
模拟引擎 Python UI 库的接口，验证 DSL 方案可行性
"""
import json
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QScrollArea, QLineEdit, QSlider, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont


def parse_color(color_str):
    """将 #RRGGBB 或 #RRGGBBAA 转为 QColor"""
    c = color_str.lstrip("#")
    if len(c) == 6:
        return QColor(int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))
    if len(c) == 8:
        return QColor(int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), int(c[6:8], 16))
    return QColor(c)


class DSLWidget(QWidget):
    """支持 DSL 通用样式的 QWidget 基类"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dsl_id = ""
        self._dsl_type = ""

    def set_style(self, key, value):
        handler = getattr(self, f"_style_{key}", None)
        if handler:
            handler(value)

    def _style_bgColor(self, color):
        self.setStyleSheet(self.styleSheet() + f"background-color: {color};")

    def _style_color(self, color):
        self.setStyleSheet(self.styleSheet() + f"color: {color};")

    def _style_fontSize(self, size):
        font = self.font()
        font.setPixelSize(size)
        self.setFont(font)

    def _style_bold(self, bold):
        font = self.font()
        font.setBold(bool(bold))
        self.setFont(font)

    def _style_padding(self, pad):
        if isinstance(pad, list):
            pad = " ".join(str(p) for p in pad)
        self.setContentsMargins(pad, pad, pad, pad)
        self.setStyleSheet(self.styleSheet() + f"padding: {pad}px;")

    def _style_cornerRadius(self, radius):
        self.setStyleSheet(self.styleSheet() + f"border-radius: {radius}px;")


class DSLPage:
    """DSL 页面加载器 - 核心类"""

    WIDGET_MAP = {
        "Panel": QWidget,
        "Text": QLabel,
        "Button": QPushButton,
        "Input": QLineEdit,
        "Slider": QSlider,
    }

    def __init__(self):
        self._widgets = {}
        self._events = {}
        self.root = None
        self._app = None

    def load(self, dsl_path):
        self._app = QApplication.instance() or QApplication([])
        with open(dsl_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.root = self._build(data["root"])
        return self

    def on(self, event_name, callback):
        """注册事件回调"""
        self._events[event_name] = callback
        return self

    def get(self, widget_id):
        """按 id 获取控件"""
        return self._widgets.get(widget_id)

    def unload(self):
        if self.root:
            self.root.close()

    def show(self):
        self.root.show()
        self._app.exec_()

    def _build(self, node):
        type_name = node["type"]
        props = node.get("props", {})
        style = node.get("style", {})

        # 创建控件
        widget = self._create(type_name, props)

        # 注册 id
        if "id" in node:
            self._widgets[node["id"]] = widget
            widget._dsl_id = node["id"]

        # 应用样式
        self._apply_style(widget, style, type_name)

        # 设置布局
        layout = self._create_layout(style)
        if layout and isinstance(widget, QWidget):
            old = widget.layout()
            if old:
                QWidget().setLayout(old)
            widget.setLayout(layout)

        # 构建子节点
        children_data = node.get("children", [])
        if type_name == "GridView":
            grid = widget.layout()
            cols = props.get("columns", 1)
            for idx, child_data in enumerate(children_data):
                child = self._build(child_data)
                row, col = divmod(idx, cols)
                grid.addWidget(child, row, col)
        else:
            for child_data in children_data:
                child = self._build(child_data)
                if layout:
                    layout.addWidget(child)

        # 绑定事件
        for event_type, event_name in node.get("events", {}).items():
            self._bind_event(widget, event_type, event_name)

        return widget

    def _create(self, type_name, props):
        if type_name == "Panel":
            w = DSLWidget()
            w.setAutoFillBackground(True)
            return w

        if type_name == "Text":
            w = QLabel(props.get("value", ""))
            w.setAlignment(Qt.AlignCenter)
            return w

        if type_name == "Button":
            w = QPushButton(props.get("text", ""))
            return w

        if type_name == "GridView":
            w = DSLWidget()
            w.setAutoFillBackground(True)
            cols = props.get("columns", 1)
            w.setLayout(QGridLayout())
            w.layout().setSpacing(props.get("gap", 8))
            return w

        if type_name in self.WIDGET_MAP:
            return self.WIDGET_MAP[type_name]()

        return DSLWidget()

    def _apply_style(self, widget, style, type_name):
        # 背景色
        if "bgColor" in style:
            color = parse_color(style["bgColor"])
            widget.setAutoFillBackground(True)
            palette = widget.palette()
            palette.setColor(widget.backgroundRole(), color)
            widget.setPalette(palette)

        # 文字颜色
        if "color" in style:
            color = parse_color(style["color"])
            palette = widget.palette()
            palette.setColor(widget.foregroundRole(), color)
            widget.setPalette(palette)

        # 字体
        font = widget.font()
        if "fontSize" in style:
            font.setPixelSize(style["fontSize"])
        if "bold" in style:
            font.setBold(style["bold"])
        widget.setFont(font)

        # 尺寸
        if "width" in style and "height" in style:
            widget.setFixedSize(style["width"], style["height"])
        elif "width" in style:
            widget.setFixedWidth(style["width"])
        elif "height" in style:
            widget.setFixedHeight(style["height"])

        # padding
        if "padding" in style:
            pad = style["padding"]
            if isinstance(pad, (int, float)):
                widget.setContentsMargins(pad, pad, pad, pad)

        # 圆角 + 边框样式
        ss_parts = []
        if "cornerRadius" in style:
            ss_parts.append(f"border-radius: {style['cornerRadius']}px;")
            ss_parts.append("border: none;")
        if "bgColor" in style:
            ss_parts.append(f"background-color: {style['bgColor']};")
        if "color" in style:
            ss_parts.append(f"color: {style['color']};")
        if ss_parts:
            widget.setStyleSheet(widget.styleSheet() + " ".join(ss_parts))

    def _create_layout(self, style):
        layout_type = style.get("layout")
        gap = style.get("gap", 0)
        align = style.get("align")

        if layout_type == "vertical":
            lay = QVBoxLayout()
        elif layout_type == "horizontal":
            lay = QHBoxLayout()
        else:
            return None

        if gap:
            lay.setSpacing(gap)

        if align == "center":
            lay.setAlignment(Qt.AlignCenter)
        elif align == "left":
            lay.setAlignment(Qt.AlignLeft)
        elif align == "right":
            lay.setAlignment(Qt.AlignRight)

        return lay

    def _bind_event(self, widget, event_type, event_name):
        if event_type == "click" and isinstance(widget, QPushButton):
            wid = widget._dsl_id
            widget.clicked.connect(lambda checked, name=event_name, w=wid: self._dispatch(name, widget_id=w))

    def _dispatch(self, event_name, **kwargs):
        if event_name in self._events:
            handler = self._events[event_name]
            import inspect
            sig = inspect.signature(handler)
            if sig.parameters:
                handler(**kwargs)
            else:
                handler()
