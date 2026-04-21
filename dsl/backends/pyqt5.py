import math
import re

from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QLineEdit, QSlider,
    QVBoxLayout, QHBoxLayout, QGridLayout, QGraphicsDropShadowEffect,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QColor, QFont, QLinearGradient, QBrush, QPen, QPainter, QPainterPath
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


def _has_alpha(color_str):
    """Check if a hex color has alpha channel with alpha < 255."""
    c = color_str.lstrip("#")
    if len(c) == 8:
        return int(c[6:8], 16) < 255
    return False


def _has_alpha_bg(widget):
    """Check if widget has translucent background configured."""
    bg = getattr(widget, '_translucent_bg', None)
    return bg is not None and bg.alpha() < 255


def _css_gradient_endpoints(angle, w, h):
    """Compute gradient start/end points matching CSS linear-gradient behavior.

    CSS gradient line passes through the center at the given angle,
    with half-length = w/2 * |sin(θ)| + h/2 * |cos(θ)|.
    Returns (x1, y1, x2, y2) in absolute pixel coordinates.
    """
    rad = math.radians(angle)
    sin_a = math.sin(rad)
    cos_a = math.cos(rad)
    half_len = w / 2 * abs(sin_a) + h / 2 * abs(cos_a)
    cx, cy = w / 2, h / 2
    # Gradient start is OPPOSITE the direction, end is IN the direction
    x1 = cx - half_len * sin_a
    y1 = cy + half_len * cos_a
    x2 = cx + half_len * sin_a
    y2 = cy - half_len * cos_a
    return x1, y1, x2, y2


def _gradient_to_qss(gradient):
    """将 DSL gradient 转为 Qt stylesheet qlineargradient 语法"""
    angle = gradient.get("angle", 180)
    stops = gradient.get("stops", [])

    # Use normalized coordinates matching CSS gradient behavior
    x1, y1, x2, y2 = _css_gradient_endpoints(angle, 1.0, 1.0)

    stop_strs = []
    for s in stops:
        pos = s.get("pos", 0)
        color = s["color"]
        # Convert #rrggbbaa for QSS gradient stops
        if len(color) == 9 and color.startswith("#"):
            c = color.lstrip("#")
            a = int(c[6:8], 16)
            if a == 0:
                color = "transparent"
            else:
                r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
                alpha = round(a / 255, 3)
                color = f"rgba({r},{g},{b},{alpha})"
        stop_strs.append(f"stop:{pos/100:.2f} {color}")

    return f"qlineargradient(x1:{x1:.4f}, y1:{y1:.4f}, x2:{x2:.4f}, y2:{y2:.4f}, {', '.join(stop_strs)})"


def _gradient_first_color(gradient):
    """Get the first color stop from a gradient"""
    stops = gradient.get("stops", [])
    if stops:
        return stops[0].get("color", "#ffffff")
    return "#ffffff"


class StyledPanel(QWidget):
    """QWidget with optional translucent background via QPainter alpha compositing.
    QSS rgba() backgrounds don't composite with parent gradient content — this fixes that.
    When translucent bg is active, skips super().paintEvent() to prevent overwrite."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._translucent_bg = None
        self._translucent_radius = 0
        self._border_width = 0
        self._border_color = None

    def set_translucent_bg(self, color_str, radius=0):
        self._translucent_bg = _parse_color(color_str)
        self._translucent_radius = radius

    def set_border_for_custom_paint(self, width, color_str):
        self._border_width = width
        self._border_color = _parse_color(color_str) if color_str else None

    def paintEvent(self, event):
        if self._translucent_bg is not None and self._translucent_bg.alpha() < 255:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            w, h = self.width(), self.height()
            r = self._translucent_radius
            path = QPainterPath()
            path.addRoundedRect(0, 0, w, h, max(r, 0), max(r, 0))
            painter.setClipPath(path)
            painter.fillRect(0, 0, w, h, self._translucent_bg)
            painter.end()
        super().paintEvent(event)


class StyledButton(QPushButton):
    """QPushButton with optional translucent background via QPainter alpha compositing."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._translucent_bg = None
        self._translucent_radius = 0
        self._border_width = 0
        self._border_color = None
        self._text_color = None

    def set_translucent_bg(self, color_str, radius=0):
        self._translucent_bg = _parse_color(color_str)
        self._translucent_radius = radius

    def set_border_for_custom_paint(self, width, color_str):
        self._border_width = width
        self._border_color = _parse_color(color_str) if color_str else None

    def set_text_color_for_custom_paint(self, color_str):
        self._text_color = _parse_color(color_str) if color_str else None

    def paintEvent(self, event):
        if self._translucent_bg is not None and self._translucent_bg.alpha() < 255:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            w, h = self.width(), self.height()
            r = self._translucent_radius
            path = QPainterPath()
            path.addRoundedRect(0, 0, w, h, max(r, 0), max(r, 0))
            painter.setClipPath(path)
            painter.fillRect(0, 0, w, h, self._translucent_bg)
            painter.end()
        super().paintEvent(event)


class GradientLabel(QLabel):
    """QLabel that paints text with a linear gradient brush (CSS background-clip:text equivalent).
    Also handles gradient backgrounds clipped to border-radius when QSS can't."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._gradient_info = None
        self._bg_gradient = None
        self._bg_radius = 0
        self._text_color = None
        self._alpha_text_color = None

    def set_text_gradient(self, gradient_info):
        self._gradient_info = gradient_info
        self.update()

    def set_bg_gradient_clipped(self, gradient_info, radius):
        self._bg_gradient = gradient_info
        self._bg_radius = radius
        self.update()

    def set_custom_text_color(self, color):
        self._text_color = QColor(color)
        self.update()

    def set_alpha_text_color(self, color_str):
        self._alpha_text_color = _parse_color(color_str)
        self.update()

    def paintEvent(self, event):
        has_text_grad = self._gradient_info is not None
        has_bg_grad = self._bg_gradient is not None
        has_alpha_text = self._alpha_text_color is not None

        if not has_text_grad and not has_bg_grad and not has_alpha_text:
            super().paintEvent(event)
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Draw clipped gradient background if needed
        if has_bg_grad:
            grad = self._bg_gradient
            angle = grad.get("angle", 180)
            stops = grad.get("stops", [])
            if stops:
                lg = QLinearGradient()
                x1, y1, x2, y2 = _css_gradient_endpoints(angle, w, h)
                lg.setStart(x1, y1)
                lg.setFinalStop(x2, y2)
                for s in stops:
                    pos = s.get("pos", 0) / 100.0
                    lg.setColorAt(pos, QColor(s["color"]))

                path = QPainterPath()
                path.addRoundedRect(0, 0, w, h, self._bg_radius, self._bg_radius)
                painter.setClipPath(path)
                painter.fillRect(0, 0, w, h, QBrush(lg))

        # Draw text (gradient-filled or alpha-colored or solid)
        if has_text_grad:
            grad = self._gradient_info
            angle = grad.get("angle", 180)
            stops = grad.get("stops", [])
            if stops:
                lg = QLinearGradient()
                x1, y1, x2, y2 = _css_gradient_endpoints(angle, w, h)
                lg.setStart(x1, y1)
                lg.setFinalStop(x2, y2)
                for s in stops:
                    pos = s.get("pos", 0) / 100.0
                    lg.setColorAt(pos, QColor(s["color"]))

                painter.setPen(QPen(QBrush(lg), 1))
                painter.setFont(self.font())
                painter.drawText(QRect(0, 0, w, h), self.alignment(), self.text())
        else:
            # Draw text with alpha color or stored/palette foreground color
            if has_alpha_text:
                color = self._alpha_text_color
            else:
                color = self._text_color or self.palette().windowText().color()
            painter.setPen(QPen(color))
            painter.setFont(self.font())
            painter.drawText(QRect(0, 0, w, h), self.alignment(), self.text())

        painter.end()


class PyQt5Backend(UIBackend):

    def create(self, type_name, props):
        if type_name == "Panel":
            return StyledPanel()
        if type_name == "Text":
            w = GradientLabel(props.get("value", ""))
            w.setAlignment(Qt.AlignCenter)
            w.setTextInteractionFlags(Qt.NoTextInteraction)
            return w
        if type_name == "Button":
            return StyledButton(props.get("text", ""))
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
            # For GradientLabel with cornerRadius, use custom painter for proper clipping
            cr = style.get("cornerRadius", 0)
            if is_gradient_label and cr > 0:
                widget.set_bg_gradient_clipped(style["gradient"], cr)
                ss.append("background-color: transparent;")
                # Store text color for custom painter
                if "color" in style:
                    widget.set_custom_text_color(style["color"])
            else:
                qss_grad = _gradient_to_qss(style["gradient"])
                ss.append("background-color: transparent;")
                ss.append(f"background: {qss_grad};")
            if is_label and "color" not in style:
                first_color = _gradient_first_color(style["gradient"])
                ss.append(f"color: {first_color};")
        elif "bgColor" in style:
            has_bg = True
            if _has_alpha(style["bgColor"]) and hasattr(widget, 'set_translucent_bg'):
                widget.set_translucent_bg(style["bgColor"], style.get("cornerRadius", 0))
                ss.append("background-color: transparent;")
                widget.setAutoFillBackground(False)
            else:
                rgba = _color_to_rgba_qss(style["bgColor"])
                ss.append(f"background-color: {rgba};")

        # For GradientLabel with gradientText, custom painter handles text color
        if is_gradient_label and "gradientText" in style:
            widget.setAutoFillBackground(False)
            ss.append("background-color: transparent;")
        elif "color" in style:
            color_val = style["color"]
            has_alpha_color = color_val.startswith("#") and len(color_val.lstrip("#")) == 8
            if has_alpha_color:
                # QSS can't render alpha text color — GradientLabel uses QPainter
                if is_gradient_label:
                    widget.set_alpha_text_color(color_val)
                # Also set QSS as fallback (rgba won't actually alpha-render but gives correct RGB)
                ss.append(f"color: {_color_to_rgba_qss(color_val)};")
            else:
                ss.append(f"color: {color_val};")
            # Store text color for custom button painting
            if hasattr(widget, 'set_text_color_for_custom_paint') and _has_alpha_bg(widget):
                widget.set_text_color_for_custom_paint(style["color"])

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
        if "fontFamily" in style:
            families = style["fontFamily"]
            for name in families.split(","):
                name = name.strip().strip('"').strip("'")
                if name:
                    font.setFamily(name)
                    break
        widget.setFont(font)

        if "width" in style and "height" in style:
            widget.setFixedSize(style["width"], style["height"])
        elif "width" in style:
            widget.setFixedWidth(style["width"])
        elif "height" in style:
            widget.setFixedHeight(style["height"])

        if "minWidth" in style:
            widget.setMinimumWidth(style["minWidth"])
        if "maxWidth" in style:
            widget.setMaximumWidth(style["maxWidth"])
        if "minHeight" in style:
            widget.setMinimumHeight(style["minHeight"])
        if "maxHeight" in style:
            widget.setMaximumHeight(style["maxHeight"])

        if "widthPercent" in style:
            widget._width_percent = style["widthPercent"]

        if "padding" in style:
            p = style["padding"]
            if isinstance(p, (int, float)):
                widget.setContentsMargins(int(p), int(p), int(p), int(p))

        # Individual padding sides override the shorthand
        has_individual_padding = any(k in style for k in ("paddingTop", "paddingRight", "paddingBottom", "paddingLeft"))
        if has_individual_padding:
            margins = widget.contentsMargins()
            pt = int(style.get("paddingTop", margins.top()))
            pr = int(style.get("paddingRight", margins.right()))
            pb = int(style.get("paddingBottom", margins.bottom()))
            pl = int(style.get("paddingLeft", margins.left()))
            widget.setContentsMargins(pl, pt, pr, pb)

        # Ensure labels have minimum height so text + padding + border are visible
        if is_label and "height" not in style:
            min_h = widget.fontMetrics().height() + 2
            margins = widget.contentsMargins()
            min_h += margins.top() + margins.bottom()
            border = style.get("border", {})
            if isinstance(border, dict):
                min_h += border.get("width", 0) * 2
            widget.setMinimumHeight(min_h)

        # line-height: add extra vertical padding for labels
        if "lineHeight" in style and is_label:
            lh = style["lineHeight"]
            if isinstance(lh, (int, float)) and lh > 0:
                font_h = widget.fontMetrics().height()
                if lh > font_h:
                    extra = int((lh - font_h) / 2)
                    margins = widget.contentsMargins()
                    widget.setContentsMargins(margins.left(), extra, margins.right(), extra)

        if "cornerRadius" in style:
            ss.append(f"border-radius: {style['cornerRadius']}px;")

        border = style.get("border", {})
        if border or "borderColor" in style:
            if border:
                bw = border.get("width", 1)
                bstyle = border.get("style", "solid")
                bcolor = style.get("borderColor", border.get("color", "#888888"))
            else:
                bw = style.get("borderWidth", 1)
                bstyle = "solid"
                bcolor = style["borderColor"]
            # Store border info for custom translucent painting
            if hasattr(widget, 'set_border_for_custom_paint') and _has_alpha_bg(widget):
                raw_bcolor = style.get("borderColor", border.get("color", "#888888")) if border else style["borderColor"]
                widget.set_border_for_custom_paint(bw, raw_bcolor)
            # Convert 8-digit hex to rgba() for QSS compatibility
            bcolor = _color_to_rgba_qss(bcolor) if bcolor.startswith("#") and len(bcolor.lstrip("#")) == 8 else bcolor
            ss.append(f"border: {bw}px {bstyle} {bcolor};")
        elif "cornerRadius" in style and not any(k in style for k in ("borderBottom", "borderTop", "borderLeft", "borderRight")):
            ss.append("border: none;")

        # border sides
        for side in ("bottom", "top", "left", "right"):
            key = f"border{side.capitalize()}"
            if key in style:
                b = style[key]
                bw = b.get("width", 1)
                bstyle = b.get("style", "solid")
                bcolor = b.get("color", "#888888")
                bcolor = _color_to_rgba_qss(bcolor) if bcolor.startswith("#") and len(bcolor.lstrip("#")) == 8 else bcolor
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

        # box-shadow via QGraphicsDropShadowEffect
        if "boxShadow" in style:
            sd = style["boxShadow"]
            effect = QGraphicsDropShadowEffect()
            effect.setOffset(sd.get("offsetX", 0), sd.get("offsetY", 0))
            effect.setBlurRadius(sd.get("blurRadius", 10))
            effect.setColor(QColor(sd.get("color", "#000000")))
            widget.setGraphicsEffect(effect)

        # Note: box-sizing: border-box is Qt's default behavior.
        # QSS borders draw inside the widget rect, and setContentsMargins
        # adds internal padding — both already subtract from the content area
        # within the CSS width/height. No size adjustment needed.

    def create_layout(self, style):
        layout_type = style.get("layout")
        if layout_type == "vertical":
            lay = QVBoxLayout()
        elif layout_type == "horizontal":
            lay = QHBoxLayout()
        else:
            return None

        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(style.get("gap", 0))

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
            # Prevent non-flex children from stretching (HTML flexbox default)
            if isinstance(parent_layout, QVBoxLayout):
                child.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
            elif isinstance(parent_layout, QHBoxLayout):
                child.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
            align = self._get_child_alignment(parent_layout)
            if align is not None:
                parent_layout.addWidget(child, 0, align)
            else:
                parent_layout.addWidget(child)

    def add_child_with_stretch(self, parent_layout, child, fill_stretch, empty_stretch):
        """Add a child with stretch factors (for percentage-width progress bars)."""
        if parent_layout is not None:
            # Flex children should be allowed to grow
            if isinstance(parent_layout, QVBoxLayout):
                child.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
            elif isinstance(parent_layout, QHBoxLayout):
                child.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            align = self._get_child_alignment(parent_layout)
            if align is not None:
                parent_layout.addWidget(child, fill_stretch, align)
            else:
                parent_layout.addWidget(child, fill_stretch)
            if empty_stretch > 0:
                parent_layout.addStretch(empty_stretch)

    def add_stretch(self, layout, factor=1):
        if layout is not None:
            layout.addStretch(factor)

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
