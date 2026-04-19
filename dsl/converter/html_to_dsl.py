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
    if dsl_type == "Text":
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


def convert_html(html_str, mappings=None):
    soup = BeautifulSoup(html_str, "html.parser")
    root_tag = soup.find()
    if root_tag is None:
        raise ValueError("No HTML element found")
    return _convert_node(root_tag, mappings or {})


def _convert_node(tag, mappings):
    tag_name = tag.name.lower()

    # Check custom mappings first
    if tag_name in mappings:
        dsl_type = mappings[tag_name]
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

    css_str = tag.get("style", "")
    if css_str:
        css_props = _parse_inline_style(css_str)
        style = map_css_to_style(css_props)
        if style:
            node["style"] = style

    tag_id = tag.get("id")
    if tag_id:
        node["id"] = tag_id

    children = []
    for child in tag.children:
        if hasattr(child, "name") and child.name:
            children.append(_convert_node(child, mappings))
    if children:
        node["children"] = children

    return node


def convert_html_to_dsl_file(html_str, output_path, page_name="untitled", mappings=None):
    root = convert_html(html_str, mappings)
    dsl = {"version": 1, "name": page_name, "root": root}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dsl, f, ensure_ascii=False, indent=2)
    return dsl
