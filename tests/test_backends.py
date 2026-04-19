import pytest
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QWidget
from dsl.backends.pyqt5 import PyQt5Backend


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_create_panel(app):
    backend = PyQt5Backend()
    w = backend.create("Panel", {})
    assert isinstance(w, QWidget)


def test_create_text(app):
    backend = PyQt5Backend()
    w = backend.create("Text", {"value": "Hello"})
    assert isinstance(w, QLabel)
    assert w.text() == "Hello"


def test_create_button(app):
    backend = PyQt5Backend()
    w = backend.create("Button", {"text": "OK"})
    assert isinstance(w, QPushButton)
    assert w.text() == "OK"


def test_create_custom_fallback(app):
    backend = PyQt5Backend()
    w = backend.create("UnknownWidget", {"a": 1})
    assert isinstance(w, QWidget)


def test_apply_style_bgcolor(app):
    backend = PyQt5Backend()
    w = backend.create("Panel", {})
    backend.apply_style(w, {"bgColor": "#FF0000"})
    pal = w.palette()
    assert pal.color(w.backgroundRole()).red() == 255


def test_apply_style_fontsize(app):
    backend = PyQt5Backend()
    w = backend.create("Text", {"value": "x"})
    backend.apply_style(w, {"fontSize": 24})
    assert w.font().pixelSize() == 24


def test_apply_style_size(app):
    backend = PyQt5Backend()
    w = backend.create("Panel", {})
    backend.apply_style(w, {"width": 100, "height": 50})
    assert w.width() == 100
    assert w.height() == 50


def test_create_layout_vertical(app):
    backend = PyQt5Backend()
    lay = backend.create_layout({"layout": "vertical", "gap": 10})
    assert lay is not None


def test_create_layout_none(app):
    backend = PyQt5Backend()
    lay = backend.create_layout({})
    assert lay is None
