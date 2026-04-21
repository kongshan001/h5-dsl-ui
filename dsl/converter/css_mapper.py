import re

CSS_TO_DSL = {
    "background-color": "bgColor",
    "color": "color",
    "font-size": "fontSize",
    "font-weight": "bold",
    "font-family": "fontFamily",
    "border-radius": "cornerRadius",
    "opacity": "opacity",
    "padding": "padding",
    "margin": "margin",
    "gap": "gap",
    "width": "width",
    "height": "height",
    "min-width": "minWidth",
    "max-width": "maxWidth",
    "min-height": "minHeight",
    "max-height": "maxHeight",
    "border": "border",
    "border-color": "borderColor",
    "border-width": "borderWidth",
    "letter-spacing": "letterSpacing",
    "line-height": "lineHeight",
    "text-align": "textAlign",
    "justify-content": "justifyContent",
    "align-items": "alignItems",
    "box-sizing": "boxSizing",
    "box-shadow": "boxShadow",
    "border-bottom": "borderBottom",
    "border-top": "borderTop",
    "border-left": "borderLeft",
    "border-right": "borderRight",
    "padding-top": "paddingTop",
    "padding-right": "paddingRight",
    "padding-bottom": "paddingBottom",
    "padding-left": "paddingLeft",
}


def _parse_color(value):
    """解析颜色值，支持 #hex, rgba(), rgb()"""
    value = value.strip()
    rgba_match = re.match(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+))?\s*\)", value)
    if rgba_match:
        r, g, b = int(rgba_match.group(1)), int(rgba_match.group(2)), int(rgba_match.group(3))
        a = float(rgba_match.group(4)) if rgba_match.group(4) else 1.0
        if a < 1.0:
            return f"#{r:02x}{g:02x}{b:02x}{round(a*255):02x}"
        return f"#{r:02x}{g:02x}{b:02x}"
    return value


def _parse_px(value):
    m = re.match(r"^(\d+(?:\.\d+)?)px$", value.strip())
    if m:
        return int(float(m.group(1))) if float(m.group(1)).is_integer() else float(m.group(1))
    return None


def _parse_pct(value):
    """Parse percentage value like '78%' → 78"""
    m = re.match(r"^(\d+(?:\.\d+)?)%$", value.strip())
    if m:
        return float(m.group(1))
    return None


def map_css_to_style(css_props):
    result = {}
    display = css_props.get("display", "")
    flex_dir = css_props.get("flex-direction", "")

    if display == "flex":
        if flex_dir == "column":
            result["layout"] = "vertical"
        else:
            result["layout"] = "horizontal"
    elif display == "grid":
        result["layout"] = "grid"
        cols = css_props.get("grid-template-columns", "")
        repeat_match = re.match(r"repeat\((\d+)", cols.strip())
        if repeat_match:
            result["columns"] = int(repeat_match.group(1))
        else:
            col_count = len(cols.split())
            if col_count > 0:
                result["columns"] = col_count

    for css_key, dsl_key in CSS_TO_DSL.items():
        if css_key not in css_props:
            continue
        val = css_props[css_key]

        if dsl_key in ("fontSize", "cornerRadius", "padding", "margin", "gap", "width", "height",
                        "letterSpacing", "minWidth", "maxWidth", "minHeight", "maxHeight",
                        "paddingTop", "paddingRight", "paddingBottom", "paddingLeft"):
            parsed = _parse_px(val)
            if parsed is not None:
                result[dsl_key] = parsed
            elif dsl_key == "padding":
                sides = _parse_padding_shorthand(val)
                if sides:
                    result.update(sides)
            elif dsl_key == "width":
                pct = _parse_pct(val)
                if pct is not None:
                    result["widthPercent"] = pct
        elif dsl_key == "bold":
            result[dsl_key] = val.strip().lower() in ("bold", "bolder", "700", "800", "900")
        elif dsl_key == "opacity":
            try:
                result[dsl_key] = float(val)
            except ValueError:
                pass
        elif dsl_key == "border":
            result["border"] = _parse_border(val)
        elif dsl_key in ("bgColor", "color", "borderColor"):
            result[dsl_key] = _parse_color(val)
        elif dsl_key in ("borderBottom", "borderTop", "borderLeft", "borderRight"):
            parsed = _parse_border(val)
            if parsed:
                result[dsl_key] = parsed
        elif dsl_key in ("textAlign", "justifyContent", "alignItems", "fontFamily", "boxSizing"):
            result[dsl_key] = val.strip()
        elif dsl_key == "lineHeight":
            parsed = _parse_px(val)
            if parsed is not None:
                result[dsl_key] = parsed
            else:
                try:
                    result[dsl_key] = float(val)
                except ValueError:
                    pass
        elif dsl_key == "boxShadow":
            parsed = _parse_box_shadow(val)
            if parsed:
                result[dsl_key] = parsed
        else:
            result[dsl_key] = val

    # flex
    flex_val = css_props.get("flex", "").strip()
    if flex_val:
        try:
            fv = float(flex_val)
            if fv > 0:
                result["flex"] = fv
        except ValueError:
            if flex_val == "grow":
                result["flex"] = 1

    # 解析 gradient（优先于纯色 bgColor）
    clip = css_props.get("-webkit-background-clip", "").strip()
    fill = css_props.get("-webkit-text-fill-color", "").strip()
    is_text_clip = clip == "text" or fill == "transparent"
    for gkey in ("background", "background-image"):
        if gkey in css_props:
            grad = _parse_gradient(css_props[gkey])
            if grad:
                if is_text_clip:
                    # background-clip:text → gradient is for text fill, not background
                    result["gradientText"] = grad
                    # Remove solid bgColor to avoid conflict
                    result.pop("bgColor", None)
                else:
                    # Normal gradient → used as background
                    result["gradient"] = grad
                    result.pop("bgColor", None)
                break

    return result


def _parse_box_shadow(value):
    """Parse CSS box-shadow: offsetX offsetY blurRadius [spread] color"""
    value = value.strip()
    if "inset" in value:
        return None
    parts = value.split()
    if len(parts) < 3:
        return None
    try:
        result = {}
        result["offsetX"] = _parse_px(parts[0]) or 0
        result["offsetY"] = _parse_px(parts[1]) or 0
        result["blurRadius"] = _parse_px(parts[2]) or 0
        if len(parts) > 3 and not parts[3].startswith("#") and not parts[3].startswith("rgb"):
            result["spreadRadius"] = _parse_px(parts[3]) or 0
            color_str = " ".join(parts[4:]) if len(parts) > 4 else "#000000"
        else:
            result["spreadRadius"] = 0
            color_str = " ".join(parts[3:]) if len(parts) > 3 else "#000000"
        result["color"] = _parse_color(color_str) if color_str else "#000000"
        return result
    except (ValueError, IndexError):
        return None


def _parse_border(value):
    """解析 border shorthand: 2px solid #ff0000"""
    result = {}
    parts = value.strip().split()
    width_match = re.match(r"^(\d+)px", parts[0]) if parts else None
    if width_match:
        result["width"] = int(width_match.group(1))
    for part in parts[1:]:
        if part == "solid" or part == "dashed":
            result["style"] = part
        elif part.startswith("#") or part.startswith("rgb"):
            result["color"] = _parse_color(part)
    return result


def _parse_gradient(value):
    """解析 linear-gradient，返回 DSL gradient 对象或 None"""
    value = value.strip()
    # Skip multi-gradient CSS values (e.g., "linear-gradient(...), linear-gradient(...)")
    if value.count("linear-gradient(") > 1:
        return None
    if "radial-gradient(" in value:
        return None
    match = re.match(r"linear-gradient\((.+)\)", value)
    if not match:
        return None
    inner = match.group(1).strip()

    # 提取角度
    angle = 180
    angle_match = re.match(r"(\d+)deg\s*,\s*(.+)", inner)
    if angle_match:
        angle = int(angle_match.group(1))
        inner = angle_match.group(2).strip()

    # 提取 color stops
    stops = []
    for part in inner.split(","):
        part = part.strip()
        stop_match = re.match(r"(.+?)\s+(\d+)%", part)
        if stop_match:
            stops.append({"color": _parse_color(stop_match.group(1).strip()), "pos": int(stop_match.group(2))})
        else:
            color = _parse_color(part)
            if color:
                if color == "transparent":
                    color = "#00000000"
                stops.append({"color": color})

    if len(stops) < 2:
        return None

    # 自动分配未指定 pos 的 stop
    if "pos" not in stops[0]:
        stops[0]["pos"] = 0
    if "pos" not in stops[-1]:
        stops[-1]["pos"] = 100
    for i, s in enumerate(stops):
        if "pos" not in s:
            s["pos"] = int(i / (len(stops) - 1) * 100)

    return {"type": "linear", "angle": angle, "stops": stops}


def _parse_padding_shorthand(value):
    """Parse multi-value padding shorthand: '4px 0' or '10px 20px 10px 20px'."""
    parts = re.findall(r'(\d+(?:\.\d+)?)px', value)
    if not parts:
        return None
    parts = [int(float(p)) for p in parts]
    if len(parts) == 2:
        return {"paddingTop": parts[0], "paddingBottom": parts[0],
                "paddingLeft": parts[1], "paddingRight": parts[1]}
    elif len(parts) == 3:
        return {"paddingTop": parts[0], "paddingBottom": parts[2],
                "paddingLeft": parts[1], "paddingRight": parts[1]}
    elif len(parts) >= 4:
        return {"paddingTop": parts[0], "paddingBottom": parts[2],
                "paddingLeft": parts[3], "paddingRight": parts[1]}
    return None
