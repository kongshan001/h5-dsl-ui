# dsl/converter/html_to_dsl.py
import json
import re
from bs4 import BeautifulSoup
from .css_mapper import map_css_to_style

TAG_MAP = {
    "div": "Panel",
    "button": "Button",
    "span": "Text",
    "p": "Text",
    "h1": "Text",
    "h2": "Text",
    "h3": "Text",
    "h4": "Text",
    "h5": "Text",
    "h6": "Text",
    "img": "Image",
    "ul": "ListView",
    "ol": "ListView",
}

INPUT_TYPE_MAP = {
    "text": "Input",
    "range": "Slider",
    "checkbox": "Toggle",
}


def _parse_inline_style(style_str):
    props = {}
    for part in style_str.split(";"):
        part = part.strip()
        if ":" not in part:
            continue
        key, val = part.split(":", 1)
        props[key.strip().lower()] = val.strip()
    return props


def _extract_props(tag, dsl_type):
    props = {}
    if tag.name.lower() == "body":
        pass
    elif dsl_type == "Text":
        props["value"] = tag.get_text(strip=True)
    elif dsl_type == "Button":
        props["text"] = tag.get_text(strip=True)
    elif dsl_type == "Image":
        props["src"] = tag.get("src", "")
    elif dsl_type == "Input":
        props["placeholder"] = tag.get("placeholder", "")
        props["value"] = tag.get("value", "")
    elif dsl_type == "Slider":
        props["min"] = int(tag.get("min", 0))
        props["max"] = int(tag.get("max", 100))
        props["value"] = int(tag.get("value", 50))

    for key, val in tag.attrs.items():
        if key.startswith("data-"):
            prop_name = key[5:]
            props[prop_name] = val

    return props


def _parse_css_rules(css_text):
    """解析 <style> 块中的 CSS 规则，返回 {selector: {prop: val}} 字典"""
    rules = {}
    for match in re.finditer(r'([^{]+)\{([^}]+)\}', css_text, re.DOTALL):
        selectors = match.group(1).strip()
        props_str = match.group(2).strip()
        props = {}
        for part in props_str.split(";"):
            part = part.strip()
            if ":" not in part:
                continue
            key, val = part.split(":", 1)
            props[key.strip().lower()] = val.strip()
        for sel in selectors.split(","):
            sel = sel.strip()
            if sel:
                rules[sel] = props
    return rules


def _compute_style(tag, css_rules):
    """合并 inline style + CSS class 规则，返回最终 computed style dict"""
    computed = {}

    # 1. 应用 class 样式（按 class 列表顺序）
    classes = tag.get("class", [])
    for cls in classes:
        selector = "." + cls
        if selector in css_rules:
            computed.update(css_rules[selector])

    # 2. 应用标签选择器样式
    tag_selector = tag.name.lower()
    if tag_selector in css_rules:
        computed.update(css_rules[tag_selector])

    # 3. 应用标签+class 组合选择器
    for cls in classes:
        combined = tag_selector + "." + cls
        if combined in css_rules:
            computed.update(css_rules[combined])

    # 4. inline style 优先级最高，覆盖 class 样式
    inline = tag.get("style", "")
    if inline:
        computed.update(_parse_inline_style(inline))

    return computed


def convert_html(html_str, mappings=None):
    soup = BeautifulSoup(html_str, "html.parser")

    # 提取 <style> 块中的 CSS 规则
    css_rules = {}
    for style_tag in soup.find_all("style"):
        css_rules.update(_parse_css_rules(style_tag.string or ""))

    # 找到根元素：<body> 自身，或第一个元素
    body = soup.find("body")
    if body:
        root_tag = body
    else:
        root_tag = soup.find()

    if root_tag is None:
        raise ValueError("No HTML element found")
    return _convert_node(root_tag, mappings or {}, css_rules)


def _is_text_only(tag):
    """判断元素是否只包含纯文本（无子元素）"""
    for child in tag.children:
        if hasattr(child, "name") and child.name:
            return False
    return bool(tag.get_text(strip=True))


def _convert_node(tag, mappings, css_rules):
    tag_name = tag.name.lower()

    # Check custom mappings first
    if tag_name in mappings:
        dsl_type = mappings[tag_name]
    elif tag_name == "body":
        dsl_type = "Panel"
    elif _is_text_only(tag) and tag_name not in ("button", "input", "img", "ul", "ol"):
        dsl_type = "Text"
    elif tag_name in TAG_MAP:
        dsl_type = TAG_MAP[tag_name]
    elif tag_name.startswith("x-"):
        dsl_type = tag_name[2:]
    elif tag_name == "input":
        input_type = tag.get("type", "text").lower()
        dsl_type = INPUT_TYPE_MAP.get(input_type, "Input")
    else:
        dsl_type = "Panel"

    node = {
        "type": dsl_type,
        "props": _extract_props(tag, dsl_type),
    }

    computed = _compute_style(tag, css_rules)
    if computed:
        style = map_css_to_style(computed)
        if style:
            node["style"] = style

    tag_id = tag.get("id")
    if tag_id:
        node["id"] = tag_id

    children = []
    for child in tag.children:
        if hasattr(child, "name") and child.name:
            children.append(_convert_node(child, mappings, css_rules))
    if children:
        node["children"] = children

    return node


def convert_html_to_dsl_file(html_str, output_path, page_name="untitled", mappings=None):
    root = convert_html(html_str, mappings)
    dsl = {"version": 1, "name": page_name, "root": root}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dsl, f, ensure_ascii=False, indent=2)
    return dsl
