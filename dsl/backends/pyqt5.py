import math
import re

from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QLineEdit, QSlider,
    QVBoxLayout, QHBoxLayout, QGridLayout
)
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QColor, QFont, QLinearGradient, QBrush, QPen, QPainter
from .base import UIBackend


def _parse_color(s):
    c = s.lstrip("#")
    if len(c) == 6:
        return QColor(int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))
    if len(c) == 8:
        return QColor(int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), int(c[6:8], 16))
    return QColor(c)


def _color_to_rgba_qss(hex_color):
    """Convert #rrggbbaa or #rrggbb to rgba(r,g,b,a) for QSS"""
    c = hex_color.lstrip("#")
    if len(c) == 8:
        r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
        a = round(int(c[6:8], 16) / 255, 3)
        return f"rgba({r},{g},{b},{a})"
    if len(c) == 6:
        return hex_color
    return hex_color


def _gradient_to_qss(gradient):
    """将 DSL gradient 转为 Qt stylesheet qlineargradient 语法"""
    angle = gradient.get("angle", 180)
    stops = gradient.get("stops", [])

    rad = math.radians(angle)
    x2 = round(math.sin(rad), 4)
    y2 = round(-math.cos(rad), 4)

    stop_strs = []
    for s in stops:
        pos = s.get("pos", 0)
        color = s["color"]
        stop_strs.append(f"stop:{pos/100:.2f} {color}")

    return f"qlineargradient(x1:0, y1:0, x2:{x2}, y2:{y2}, {', '.join(stop_strs)})"


def _gradient_first_color(gradient):
    """Get the first color stop from a gradient"""
    stops = gradient.get("stops", [])
    if stops:
        return stops[0].get("color", "#ffffff")
    return "#ffffff"


class GradientLabel(QLabel):
    """QLabel that paints text with a linear gradient brush (CSS background-clip:text equivalent)."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._gradient_info = None

    def set_text_gradient(self, gradient_info):
        self._gradient_info = gradient_info
        self.update()

    def paintEvent(self, event):
        if not self._gradient_info:
            super().paintEvent(event)
            return

        grad = self._gradient_info
        angle = grad.get("angle", 180)
        stops = grad.get("stops", [])
        if not stops:
            super().paintEvent(event)
            return

        painter = QPainter(self)
        lg = QLinearGradient()
        rad = math.radians(angle)
        lg.setStart(0, 0)
        w, h = self.width(), self.height()
        lg.setFinalStop(math.sin(rad) * w, -math.cos(rad) * h)
        for s in stops:
            pos = s.get("pos", 0) / 100.0
            lg.setColorAt(pos, QColor(s["color"]))

        painter.setPen(QPen(QBrush(lg), 1))
        painter.setFont(self.font())
        painter.drawText(QRect(0, 0, w, h), self.alignment(), self.text())
        painter.end()


class PyQt5Backend(UIBackend):

    def create(self, type_name, props):
        if type_name == "Panel":
            w = QWidget()
            w.setAttribute(Qt.WA_StyledBackground, True)
            return w
        if type_name == "Text":
            w = GradientLabel(props.get("value", ""))
            w.setAlignment(Qt.AlignCenter)
            w.setTextInteractionFlags(Qt.NoTextInteraction)
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
            w.setAttribute(Qt.WA_StyledBackground, True)
            w.setLayout(QGridLayout())
            w.layout().setSpacing(props.get("gap", 8))
            return w
        w = QWidget()
        w.setAttribute(Qt.WA_StyledBackground, True)
        return w

    def apply_style(self, widget, style):
        ss = []
        is_label = isinstance(widget, QLabel)
        is_gradient_label = isinstance(widget, GradientLabel)
        is_button = isinstance(widget, QPushButton)

        has_bg = False
        # gradientText: CSS background-clip:text → gradient is for text fill
        if "gradientText" in style and is_gradient_label:
            widget.set_text_gradient(style["gradientText"])
        # gradient: CSS background gradient → always used as background
        elif "gradient" in style:
            has_bg = True
            qss_grad = _gradient_to_qss(style["gradient"])
            ss.append(f"background: {qss_grad};")
            if is_label and "color" not in style:
                first_color = _gradient_first_color(style["gradient"])
                ss.append(f"color: {first_color};")
        elif "bgColor" in style:
            has_bg = True
            rgba = _color_to_rgba_qss(style["bgColor"])
            ss.append(f"background-color: {rgba};")

        # For GradientLabel with gradientText, custom painter handles text color
        if is_gradient_label and "gradientText" in style:
            widget.setAutoFillBackground(False)
            ss.append("background-color: transparent;")
        elif "color" in style:
            ss.append(f"color: {style['color']};")

        # Prevent child widgets from filling background and covering parent gradients
        if not has_bg and not is_button:
            ss.append("background-color: transparent;")
            widget.setAutoFillBackground(False)

        font = widget.font()
        if "fontSize" in style:
            font.setPixelSize(style["fontSize"])
        if "bold" in style and style["bold"]:
            font.setBold(True)
        if "letterSpacing" in style:
            px = _parse_px_value(style["letterSpacing"])
            if px is not None:
                font.setLetterSpacing(QFont.AbsoluteSpacing, int(px))
        widget.setFont(font)

        if "width" in style and "height" in style:
            widget.setFixedSize(style["width"], style["height"])
        elif "width" in style:
            widget.setFixedWidth(style["width"])
        elif "height" in style:
            widget.setFixedHeight(style["height"])

        # Ensure labels have minimum height so text is always visible
        if is_label and "height" not in style:
            min_h = widget.fontMetrics().height() + 2
            widget.setMinimumHeight(min_h)

        if "widthPercent" in style:
            widget._width_percent = style["widthPercent"]

        if "padding" in style:
            p = style["padding"]
            if isinstance(p, (int, float)):
                widget.setContentsMargins(int(p), int(p), int(p), int(p))

        if "cornerRadius" in style:
            ss.append(f"border-radius: {style['cornerRadius']}px;")

        border = style.get("border", {})
        if border:
            bw = border.get("width", 1)
            bstyle = border.get("style", "solid")
            bcolor = border.get("color", "#888888")
            ss.append(f"border: {bw}px {bstyle} {bcolor};")
        elif "cornerRadius" in style and not any(k in style for k in ("borderBottom", "borderTop", "borderLeft", "borderRight")):
            ss.append("border: none;")

        if "borderColor" in style:
            bw = style.get("borderWidth", 1)
            ss.append(f"border: {bw}px solid {style['borderColor']};")

        # border sides
        for side in ("bottom", "top", "left", "right"):
            key = f"border{side.capitalize()}"
            if key in style:
                b = style[key]
                bw = b.get("width", 1)
                bstyle = b.get("style", "solid")
                bcolor = b.get("color", "#888888")
                ss.append(f"border-{side}: {bw}px {bstyle} {bcolor};")

        # textAlign
        if "textAlign" in style and is_label:
            ta = style["textAlign"]
            align_map = {
                "center": Qt.AlignCenter,
                "left": Qt.AlignLeft | Qt.AlignVCenter,
                "right": Qt.AlignRight | Qt.AlignVCenter,
            }
            if ta in align_map:
                widget.setAlignment(align_map[ta])

        if ss:
            # Build complete stylesheet with proper selector for buttons
            if is_button:
                widget.setStyleSheet("QPushButton { " + " ".join(ss) + " }")
            else:
                widget.setStyleSheet(" ".join(ss))

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

        # align (legacy)
        align_map = {"center": Qt.AlignCenter, "left": Qt.AlignLeft, "right": Qt.AlignRight}
        if "align" in style and style["align"] in align_map:
            lay.setAlignment(align_map[style["align"]])

        # Store justifyContent for later use in add_child
        jc = style.get("justifyContent", "")
        lay._justify_content = jc
        if jc == "center":
            lay.setAlignment(Qt.AlignCenter)
        elif jc in ("space-between", "space-around"):
            lay.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        # Store alignItems for per-child alignment
        ai = style.get("alignItems", "")
        lay._align_items = ai
        lay._layout_type = layout_type

        return lay

    def _get_child_alignment(self, parent_layout):
        """Compute per-child alignment from layout's alignItems setting."""
        ai = getattr(parent_layout, '_align_items', '')
        lt = getattr(parent_layout, '_layout_type', '')
        if ai == 'center':
            if lt == 'horizontal':
                return Qt.AlignVCenter
            elif lt == 'vertical':
                return Qt.AlignHCenter
            return Qt.AlignCenter
        elif ai == 'flex-start' or ai == 'start':
            return Qt.AlignTop if lt == 'horizontal' else Qt.AlignLeft
        elif ai == 'flex-end' or ai == 'end':
            return Qt.AlignBottom if lt == 'horizontal' else Qt.AlignRight
        return None

    def add_child(self, parent_layout, child):
        if parent_layout is not None:
            align = self._get_child_alignment(parent_layout)
            if align is not None:
                parent_layout.addWidget(child, 0, align)
            else:
                parent_layout.addWidget(child)

    def add_child_with_stretch(self, parent_layout, child, fill_stretch, empty_stretch):
        """Add a child with stretch factors (for percentage-width progress bars)."""
        if parent_layout is not None:
            align = self._get_child_alignment(parent_layout)
            if align is not None:
                parent_layout.addWidget(child, fill_stretch, align)
            else:
                parent_layout.addWidget(child, fill_stretch)
            if empty_stretch > 0:
                parent_layout.addStretch(empty_stretch)

    def add_stretch(self, layout):
        if layout is not None:
            layout.addStretch()

    def add_grid_child(self, grid_layout, child, row, col):
        grid_layout.addWidget(child, row, col)

    def bind_event(self, widget, event_type, handler):
        if event_type == "click" and isinstance(widget, QPushButton):
            widget.clicked.connect(lambda checked: handler())


def _parse_px_value(val):
    """Parse '8px' → 8, '2px' → 2, or bare number"""
    if isinstance(val, (int, float)):
        return val
    m = re.match(r"^(\d+(?:\.\d+)?)px$", str(val).strip())
    if m:
        return float(m.group(1))
    try:
        return float(val)
    except (ValueError, TypeError):
        return None
