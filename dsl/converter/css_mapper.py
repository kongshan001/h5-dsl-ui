import re

CSS_TO_DSL = {
    "background-color": "bgColor",
    "color": "color",
    "font-size": "fontSize",
    "font-weight": "bold",
    "border-radius": "cornerRadius",
    "opacity": "opacity",
    "padding": "padding",
    "margin": "margin",
    "gap": "gap",
    "width": "width",
    "height": "height",
}


def _parse_px(value):
    m = re.match(r"^(\d+(?:\.\d+)?)px$", value.strip())
    if m:
        return int(float(m.group(1))) if float(m.group(1)).is_integer() else float(m.group(1))
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
        col_count = len(cols.split())
        if col_count > 0:
            result["columns"] = col_count

    for css_key, dsl_key in CSS_TO_DSL.items():
        if css_key not in css_props:
            continue
        val = css_props[css_key]

        if dsl_key in ("fontSize", "cornerRadius", "padding", "margin", "gap", "width", "height"):
            parsed = _parse_px(val)
            if parsed is not None:
                result[dsl_key] = parsed
        elif dsl_key == "bold":
            result[dsl_key] = val.strip().lower() in ("bold", "bolder", "700", "800", "900")
        elif dsl_key == "opacity":
            try:
                result[dsl_key] = float(val)
            except ValueError:
                pass
        else:
            result[dsl_key] = val

    return result
