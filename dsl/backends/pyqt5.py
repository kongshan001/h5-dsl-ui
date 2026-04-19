from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QLineEdit, QSlider,
    QVBoxLayout, QHBoxLayout, QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from .base import UIBackend


def _parse_color(s):
    c = s.lstrip("#")
    if len(c) == 6:
        return QColor(int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))
    if len(c) == 8:
        return QColor(int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), int(c[6:8], 16))
    return QColor(c)


def _gradient_to_qss(gradient, w, h):
    """将 DSL gradient 转为 Qt stylesheet qlineargradient 语法"""
    angle = gradient.get("angle", 180)
    stops = gradient.get("stops", [])

    # CSS 角度 → Qt x1,y1,x2,y2
    # 0deg=向上, 90deg=向右, 180deg=向下
    import math
    rad = math.radians(angle)
    x2 = round(math.sin(rad), 4)
    y2 = round(-math.cos(rad), 4)

    stop_strs = []
    for s in stops:
        pos = s.get("pos", 0)
        color = s["color"]
        stop_strs.append(f"stop:{pos/100:.2f} {color}")

    return f"qlineargradient(x1:0, y1:0, x2:{x2}, y2:{y2}, {', '.join(stop_strs)})"


class PyQt5Backend(UIBackend):

    def create(self, type_name, props):
        if type_name == "Panel":
            w = QWidget()
            w.setAutoFillBackground(True)
            return w
        if type_name == "Text":
            w = QLabel(props.get("value", ""))
            w.setAlignment(Qt.AlignCenter)
            return w
        if type_name == "Button":
            return QPushButton(props.get("text", ""))
        if type_name == "Input":
            w = QLineEdit(props.get("value", ""))
            if "placeholder" in props:
                w.setPlaceholderText(props["placeholder"])
            return w
        if type_name == "Slider":
            w = QSlider(Qt.Horizontal)
            w.setRange(props.get("min", 0), props.get("max", 100))
            if "value" in props:
                w.setValue(props["value"])
            return w
        if type_name == "GridView":
            w = QWidget()
            w.setAutoFillBackground(True)
            w.setLayout(QGridLayout())
            w.layout().setSpacing(props.get("gap", 8))
            return w
        return QWidget()

    def apply_style(self, widget, style):
        ss = []

        # gradient（优先于 bgColor）
        if "gradient" in style:
            w = style.get("width", 100)
            h = style.get("height", 100)
            qss_grad = _gradient_to_qss(style["gradient"], w, h)
            ss.append(f"background: {qss_grad};")
            widget.setAutoFillBackground(False)
        elif "bgColor" in style:
            color = _parse_color(style["bgColor"])
            widget.setAutoFillBackground(True)
            pal = widget.palette()
            pal.setColor(widget.backgroundRole(), color)
            widget.setPalette(pal)
            ss.append(f"background-color: {style['bgColor']};")

        if "color" in style:
            color = _parse_color(style["color"])
            pal = widget.palette()
            pal.setColor(widget.foregroundRole(), color)
            widget.setPalette(pal)
            ss.append(f"color: {style['color']};")

        font = widget.font()
        if "fontSize" in style:
            font.setPixelSize(style["fontSize"])
        if "bold" in style and style["bold"]:
            font.setBold(True)
        widget.setFont(font)

        if "width" in style and "height" in style:
            widget.setFixedSize(style["width"], style["height"])
        elif "width" in style:
            widget.setFixedWidth(style["width"])
        elif "height" in style:
            widget.setFixedHeight(style["height"])

        if "padding" in style:
            p = style["padding"]
            if isinstance(p, (int, float)):
                widget.setContentsMargins(p, p, p, p)

        if "cornerRadius" in style:
            ss.append(f"border-radius: {style['cornerRadius']}px;")

        border = style.get("border", {})
        if border:
            bw = border.get("width", 1)
            bstyle = border.get("style", "solid")
            bcolor = border.get("color", "#888888")
            ss.append(f"border: {bw}px {bstyle} {bcolor};")
        elif "cornerRadius" in style:
            ss.append("border: none;")

        if "borderColor" in style:
            bw = style.get("borderWidth", 1)
            ss.append(f"border: {bw}px solid {style['borderColor']};")

        if ss:
            widget.setStyleSheet(widget.styleSheet() + " ".join(ss))

    def create_layout(self, style):
        layout_type = style.get("layout")
        if layout_type == "vertical":
            lay = QVBoxLayout()
        elif layout_type == "horizontal":
            lay = QHBoxLayout()
        else:
            return None

        if "gap" in style:
            lay.setSpacing(style["gap"])

        align_map = {"center": Qt.AlignCenter, "left": Qt.AlignLeft, "right": Qt.AlignRight}
        if "align" in style and style["align"] in align_map:
            lay.setAlignment(align_map[style["align"]])

        return lay

    def add_child(self, parent_layout, child):
        if parent_layout is not None:
            parent_layout.addWidget(child)

    def add_grid_child(self, grid_layout, child, row, col):
        grid_layout.addWidget(child, row, col)

    def bind_event(self, widget, event_type, handler):
        if event_type == "click" and isinstance(widget, QPushButton):
            widget.clicked.connect(lambda checked: handler())
