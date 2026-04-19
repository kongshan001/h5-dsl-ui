BUILTIN_TYPES = {"Panel", "Text", "Button", "Image", "Input", "Slider", "ScrollView", "ListView", "GridView"}


def validate_node(node):
    if not isinstance(node, dict):
        raise ValueError("node must be a dict")

    if "type" not in node:
        raise ValueError("node missing required field: type")

    if not isinstance(node["type"], str):
        raise ValueError("type must be a string")

    if "id" in node and not isinstance(node["id"], str):
        raise ValueError("id must be a string")

    if "props" in node and not isinstance(node["props"], dict):
        raise ValueError("props must be a dict")

    if "style" in node and not isinstance(node["style"], dict):
        raise ValueError("style must be a dict")

    if "events" in node and not isinstance(node["events"], dict):
        raise ValueError("events must be a dict")

    if "children" in node and not isinstance(node["children"], list):
        raise ValueError("children must be a list")

    return True


def validate_dsl(data):
    if not isinstance(data, dict):
        raise ValueError("DSL root must be a dict")
    if "version" not in data:
        raise ValueError("DSL missing required field: version")
    if "name" not in data:
        raise ValueError("DSL missing required field: name")
    if "root" not in data:
        raise ValueError("DSL missing required field: root")
    validate_node(data["root"])
    return True
