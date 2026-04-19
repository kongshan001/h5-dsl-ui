import json
import os
import pytest
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QWidget
from dsl.loader import DSLPage

PAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "demo", "pages")


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def _write_temp_dsl(tmp_path, data):
    p = tmp_path / "test.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


def test_load_minimal(app, tmp_path):
    dsl = {"version": 1, "name": "test", "root": {"type": "Panel", "id": "root"}}
    path = _write_temp_dsl(tmp_path, dsl)
    page = DSLPage().load(path)
    assert page.get("root") is not None
    assert isinstance(page.get("root"), QWidget)


def test_load_with_children(app, tmp_path):
    dsl = {
        "version": 1, "name": "test",
        "root": {
            "type": "Panel", "id": "root",
            "style": {"layout": "vertical"},
            "children": [
                {"type": "Text", "id": "lbl", "props": {"value": "Hi"}},
                {"type": "Button", "id": "btn", "props": {"text": "Go"}}
            ]
        }
    }
    path = _write_temp_dsl(tmp_path, dsl)
    page = DSLPage().load(path)
    assert isinstance(page.get("lbl"), QLabel)
    assert isinstance(page.get("btn"), QPushButton)
    assert page.get("lbl").text() == "Hi"


def test_event_dispatch(app, tmp_path):
    clicked = {"fired": False, "wid": None}

    dsl = {
        "version": 1, "name": "test",
        "root": {
            "type": "Panel", "id": "root",
            "children": [
                {"type": "Button", "id": "btn", "props": {"text": "X"},
                 "events": {"click": "on_btn"}}
            ]
        }
    }
    path = _write_temp_dsl(tmp_path, dsl)
    page = DSLPage().load(path)

    def handler(widget_id):
        clicked["fired"] = True
        clicked["wid"] = widget_id

    page.on("on_btn", handler)
    btn = page.get("btn")
    btn.click()

    assert clicked["fired"] is True
    assert clicked["wid"] == "btn"


def test_event_no_args_handler(app, tmp_path):
    closed = {"fired": False}

    dsl = {
        "version": 1, "name": "test",
        "root": {
            "type": "Panel", "id": "root",
            "children": [
                {"type": "Button", "id": "close", "props": {"text": "Close"},
                 "events": {"click": "on_close"}}
            ]
        }
    }
    path = _write_temp_dsl(tmp_path, dsl)
    page = DSLPage().load(path)

    def handler():
        closed["fired"] = True

    page.on("on_close", handler)
    page.get("close").click()

    assert closed["fired"] is True


def test_gridview_children(app, tmp_path):
    dsl = {
        "version": 1, "name": "test",
        "root": {
            "type": "GridView", "id": "grid", "props": {"columns": 2},
            "children": [
                {"type": "Text", "props": {"value": "A"}},
                {"type": "Text", "props": {"value": "B"}},
                {"type": "Text", "props": {"value": "C"}},
                {"type": "Text", "props": {"value": "D"}}
            ]
        }
    }
    path = _write_temp_dsl(tmp_path, dsl)
    page = DSLPage().load(path)
    grid = page.get("grid")
    assert grid is not None
    assert grid.layout().count() == 4
