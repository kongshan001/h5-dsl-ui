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
        # Fallback for custom types
        return QWidget()

    def apply_style(self, widget, style):
        if "bgColor" in style:
            color = _parse_color(style["bgColor"])
            widget.setAutoFillBackground(True)
            pal = widget.palette()
            pal.setColor(widget.backgroundRole(), color)
            widget.setPalette(pal)

        if "color" in style:
            color = _parse_color(style["color"])
            pal = widget.palette()
            pal.setColor(widget.foregroundRole(), color)
            widget.setPalette(pal)

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

        ss = []
        if "cornerRadius" in style:
            ss.append(f"border-radius: {style['cornerRadius']}px;")
            ss.append("border: none;")
        if "bgColor" in style:
            ss.append(f"background-color: {style['bgColor']};")
        if "color" in style:
            ss.append(f"color: {style['color']};")
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
