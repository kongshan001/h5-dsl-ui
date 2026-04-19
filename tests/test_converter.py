import json
from dsl.converter.html_to_dsl import convert_html


def test_simple_button():
    html = '<button style="background-color: #e94560; color: white;">Close</button>'
    result = convert_html(html)
    assert result["type"] == "Button"
    assert result["props"]["text"] == "Close"
    assert result["style"]["bgColor"] == "#e94560"
    assert result["style"]["color"] == "white"


def test_nested_div_with_text():
    html = '''<div style="display:flex; flex-direction:column; padding:20px;">
        <p style="font-size:24px; color:white;">Hello</p>
    </div>'''
    result = convert_html(html)
    assert result["type"] == "Panel"
    assert result["style"]["layout"] == "vertical"
    assert len(result["children"]) == 1
    assert result["children"][0]["type"] == "Text"
    assert result["children"][0]["props"]["value"] == "Hello"


def test_custom_tag():
    html = '<x-itemslot data-index="0"></x-itemslot>'
    result = convert_html(html, mappings={"x-itemslot": "ItemSlot"})
    assert result["type"] == "ItemSlot"
    assert result["props"]["index"] == "0"


def test_grid_from_css():
    html = '''<div style="display:grid; grid-template-columns:repeat(4,1fr); gap:8px;">
        <div>Slot 1</div>
        <div>Slot 2</div>
    </div>'''
    result = convert_html(html)
    assert result["type"] == "Panel"
    assert result["style"]["layout"] == "grid"
    assert result["style"]["columns"] == 4


def test_full_page_output():
    html = '<div id="root"><button id="btn">Go</button></div>'
    result = convert_html(html)
    assert result["id"] == "root"
    assert result["children"][0]["id"] == "btn"
