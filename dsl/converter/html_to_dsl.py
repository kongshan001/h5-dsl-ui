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


def _has_element_children(tag):
    """判断元素是否有子元素节点（非纯文本）"""
    for child in tag.children:
        if hasattr(child, "name") and child.name:
            return True
    return False


def _direct_text(tag):
    """获取元素的直接文本节点内容（不包括子元素的文本）"""
    texts = []
    for child in tag.children:
        if not (hasattr(child, "name") and child.name):
            t = str(child).strip()
            if t:
                texts.append(t)
    return " ".join(texts) if texts else ""


def _extract_props(tag, dsl_type):
    props = {}
    if tag.name.lower() == "body":
        pass
    elif dsl_type == "Text":
        if _has_element_children(tag):
            # 混合内容：只用直接文本，子元素会作为 children 独立处理
            props["value"] = _direct_text(tag)
        else:
            props["value"] = tag.get_text(strip=True)
    elif dsl_type == "Button":
        if _has_element_children(tag):
            props["text"] = ""
        else:
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


def _compute_specificity(selector):
    """计算 CSS 选择器特异性 (ids, classes, tags)。"""
    ids = classes = tags = 0
    # Split into parts by descendant combinator (space)
    for part in selector.split():
        # Parse each part: may contain tag, .class, #id combined
        tokens = re.split(r'([.#])', part)
        for i, token in enumerate(tokens):
            if token == '#':
                ids += 1
            elif token == '.':
                classes += 1
            elif token and i == 0:
                # First token with no prefix is a tag name
                if token != '*':
                    tags += 1
            elif token and i > 0 and tokens[i - 1] not in ('.', '#'):
                # Standalone token (shouldn't happen in well-formed selectors)
                pass
    return (ids, classes, tags)


def _parse_selector_part(part):
    """Parse a single selector part like 'tag.class1.class2#id' into components."""
    result = {"tag": None, "classes": [], "id": None}
    tokens = re.split(r'([.#])', part)
    for i, token in enumerate(tokens):
        if not token:
            continue
        if token == '#' and i + 1 < len(tokens):
            result["id"] = tokens[i + 1]
        elif token == '.':
            if i + 1 < len(tokens) and tokens[i + 1]:
                result["classes"].append(tokens[i + 1])
        elif i == 0 or tokens[i - 1] not in ('.', '#'):
            if token != '*':
                result["tag"] = token
    return result


def _matches_part(tag, part_info):
    """Check if a tag matches a parsed selector part."""
    if part_info["tag"] and tag.name.lower() != part_info["tag"]:
        return False
    if part_info["id"] and tag.get("id") != part_info["id"]:
        return False
    tag_classes = tag.get("class", [])
    if isinstance(tag_classes, str):
        tag_classes = [tag_classes]
    for cls in part_info["classes"]:
        if cls not in tag_classes:
            return False
    return True


def _matches_selector(tag, selector):
    """Check if a BeautifulSoup tag matches a CSS selector string."""
    selector = selector.strip()
    if selector == '*':
        return True

    parts = selector.split()
    if len(parts) == 1:
        # Simple selector: .class, tag, tag.class, .c1.c2, #id
        return _matches_part(tag, _parse_selector_part(parts[0]))

    # Descendant selector: match rightmost, then walk ancestors for the rest
    if not _matches_part(tag, _parse_selector_part(parts[-1])):
        return False

    ancestors = []
    parent = tag.parent
    while parent and hasattr(parent, 'name') and parent.name:
        ancestors.append(parent)
        parent = parent.parent

    remaining = parts[:-1]
    ancestor_idx = 0
    for sel_part in remaining:
        matched = False
        while ancestor_idx < len(ancestors):
            if _matches_part(ancestors[ancestor_idx], _parse_selector_part(sel_part)):
                matched = True
                ancestor_idx += 1
                break
            ancestor_idx += 1
        if not matched:
            return False
    return True


def _compute_style(tag, css_rules):
    """合并所有匹配的 CSS 规则，按特异性排序，返回 computed style dict"""
    matched = []
    for selector, props in css_rules.items():
        if _matches_selector(tag, selector):
            specificity = _compute_specificity(selector)
            matched.append((specificity, props))

    # 按特异性升序排列，高特异性的后应用会覆盖
    matched.sort(key=lambda x: x[0])

    computed = {}
    for _, props in matched:
        computed.update(props)

    # inline style 优先级最高
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
    has_elements = _has_element_children(tag)
    for child in tag.children:
        if hasattr(child, "name") and child.name:
            children.append(_convert_node(child, mappings, css_rules))
        elif has_elements:
            # NavigableString: 混合内容中的直接文本（子元素的兄弟文本）
            text = str(child).strip()
            if text:
                children.append({
                    "type": "Text",
                    "props": {"value": text},
                })
    if children:
        node["children"] = children

    return node


def convert_html_to_dsl_file(html_str, output_path, page_name="untitled", mappings=None):
    root = convert_html(html_str, mappings)
    dsl = {"version": 1, "name": page_name, "root": root}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dsl, f, ensure_ascii=False, indent=2)
    return dsl
