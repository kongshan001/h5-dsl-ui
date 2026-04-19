import pytest
from dsl.schema import validate_node


def test_valid_minimal_node():
    node = {"type": "Panel"}
    assert validate_node(node) is True


def test_valid_full_node():
    node = {
        "type": "Button",
        "id": "btn1",
        "props": {"text": "Click"},
        "style": {"bgColor": "#FF0000"},
        "events": {"click": "on_click"},
        "children": []
    }
    assert validate_node(node) is True


def test_missing_type_raises():
    with pytest.raises(ValueError, match="type"):
        validate_node({"id": "x"})


def test_invalid_type_raises():
    with pytest.raises(ValueError, match="type"):
        validate_node({"type": 123})


def test_invalid_events_raises():
    with pytest.raises(ValueError, match="events"):
        validate_node({"type": "Panel", "events": "not_a_dict"})
