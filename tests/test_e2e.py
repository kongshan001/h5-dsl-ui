import json
import os
import pytest
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton
from dsl.converter.html_to_dsl import convert_html_to_dsl_file
from dsl.loader import DSLPage


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_html_to_dsl_to_ui(app, tmp_path):
    html = '''
    <div id="root" style="display:flex; flex-direction:column; padding:10px; background-color:#222;">
        <h1 id="title" style="color:white; font-size:28px;">我的背包</h1>
        <button id="btn" style="background-color:#e94560; color:white; width:120px; height:40px;">确定</button>
    </div>
    '''
    output = str(tmp_path / "output.json")
    convert_html_to_dsl_file(html, output, page_name="e2e_test")

    with open(output) as f:
        dsl = json.load(f)
    assert dsl["root"]["type"] == "Panel"
    assert dsl["root"]["style"]["layout"] == "vertical"

    page = DSLPage().load(output)
    title = page.get("title")
    btn = page.get("btn")

    assert isinstance(title, QLabel)
    assert title.text() == "我的背包"
    assert isinstance(btn, QPushButton)
    assert btn.text() == "确定"
    assert page.root is not None
