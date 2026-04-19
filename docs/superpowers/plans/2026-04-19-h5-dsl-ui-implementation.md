# H5 DSL UI System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a declarative DSL system that bridges H5 UI development (HTML/CSS) with a custom game engine's Python UI library, enabling AI-driven UI design workflows.

**Architecture:** Three-layer separation — HTML/CSS design layer → JSON DSL intermediate → Python DSL Loader calling engine UI API. A backend abstraction (`UIBackend`) allows the same loader to work with PyQt5 (demo/validation) or the actual engine.

**Tech Stack:** Python 3.9+, PyQt5 (demo backend), beautifulsoup4 + cssutils (HTML→DSL converter), pytest

---

## File Structure

| File | Responsibility |
|------|----------------|
| `dsl/schema.py` | DSL node validation, widget registry |
| `dsl/loader.py` | DSLPage — recursive load, event dispatch, get/unload |
| `dsl/backends/base.py` | `UIBackend` abstract base class |
| `dsl/backends/pyqt5.py` | PyQt5 backend implementation |
| `dsl/converter/css_mapper.py` | CSS→DSL style property mapping table |
| `dsl/converter/html_to_dsl.py` | HTML DOM → DSL JSON converter |
| `dsl/mappings.json` | Custom widget mapping config |
| `demo/pages/inventory.json` | Inventory page DSL |
| `demo/pages/settings.json` | Settings page DSL (validates Slider/Toggle/Input) |
| `demo/run.py` | Demo entry point |
| `tests/test_schema.py` | Schema validation tests |
| `tests/test_loader.py` | Loader + event tests |
| `tests/test_converter.py` | HTML→DSL conversion tests |

---

### Task 1: Project Setup & Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `dsl/__init__.py`
- Create: `dsl/backends/__init__.py`
- Create: `dsl/converter/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
PyQt5>=5.15
beautifulsoup4>=4.12
cssutils>=2.9
pytest>=7.0
```

- [ ] **Step 2: Install dependencies**

Run: `pip3 install -r requirements.txt`
Expected: all packages install successfully

- [ ] **Step 3: Create all `__init__.py` files**

```python
# dsl/__init__.py, dsl/backends/__init__.py, dsl/converter/__init__.py, tests/__init__.py
# All empty
```

- [ ] **Step 4: Verify project structure**

Run: `python3 -c "import dsl; print('OK')"`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add requirements.txt dsl/__init__.py dsl/backends/__init__.py dsl/converter/__init__.py tests/__init__.py
git commit -m "chore: project scaffold with dependencies"
```

---

### Task 2: DSL Schema — Node Validation

**Files:**
- Create: `dsl/schema.py`
- Create: `tests/test_schema.py`

- [ ] **Step 1: Write failing test for DSL node validation**

```python
# tests/test_schema.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_schema.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dsl.schema'`

- [ ] **Step 3: Implement schema.py**

```python
# dsl/schema.py

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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_schema.py -v`
Expected: all 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add dsl/schema.py tests/test_schema.py
git commit -m "feat: DSL schema validation with tests"
```

---

### Task 3: UIBackend Abstract Base + PyQt5 Backend

**Files:**
- Create: `dsl/backends/base.py`
- Create: `dsl/backends/pyqt5.py`
- Create: `tests/test_backends.py`

- [ ] **Step 1: Write failing test for PyQt5 backend widget creation**

```python
# tests/test_backends.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_backends.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement UIBackend base class**

```python
# dsl/backends/base.py
from abc import ABC, abstractmethod


class UIBackend(ABC):

    @abstractmethod
    def create(self, type_name, props):
        """Create a widget by type name. Returns widget instance."""
        ...

    @abstractmethod
    def apply_style(self, widget, style):
        """Apply style dict to widget."""
        ...

    @abstractmethod
    def create_layout(self, style):
        """Create a layout manager from style. Returns layout or None."""
        ...

    @abstractmethod
    def add_child(self, parent_layout, child):
        """Add child widget to parent layout."""
        ...

    @abstractmethod
    def bind_event(self, widget, event_type, handler):
        """Bind an event handler to widget."""
        ...
```

- [ ] **Step 4: Implement PyQt5 backend**

```python
# dsl/backends/pyqt5.py
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QLineEdit, QSlider,
    QVBoxLayout, QHBoxLayout, QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from .base import UIBackend


def _parse_color(s):
    c = s.lstrip("#")
    if len(c) == 6:
        return QColor(int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))
    if len(c) == 8:
        return QColor(int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), int(c[6:8], 16))
    return QColor(c)


class PyQt5Backend(UIBackend):

    def create(self, type_name, props):
        if type_name == "Panel":
            w = QWidget()
            w.setAutoFillBackground(True)
            return w
        if type_name == "Text":
            w = QLabel(props.get("value", ""))
            w.setAlignment(Qt.AlignCenter)
            return w
        if type_name == "Button":
            return QPushButton(props.get("text", ""))
        if type_name == "Input":
            w = QLineEdit(props.get("value", ""))
            if "placeholder" in props:
                w.setPlaceholderText(props["placeholder"])
            return w
        if type_name == "Slider":
            w = QSlider(Qt.Horizontal)
            w.setRange(props.get("min", 0), props.get("max", 100))
            if "value" in props:
                w.setValue(props["value"])
            return w
        if type_name == "GridView":
            w = QWidget()
            w.setAutoFillBackground(True)
            w.setLayout(QGridLayout())
            w.layout().setSpacing(props.get("gap", 8))
            return w
        # Fallback for custom types
        return QWidget()

    def apply_style(self, widget, style):
        if "bgColor" in style:
            color = _parse_color(style["bgColor"])
            widget.setAutoFillBackground(True)
            pal = widget.palette()
            pal.setColor(widget.backgroundRole(), color)
            widget.setPalette(pal)

        if "color" in style:
            color = _parse_color(style["color"])
            pal = widget.palette()
            pal.setColor(widget.foregroundRole(), color)
            widget.setPalette(pal)

        font = widget.font()
        if "fontSize" in style:
            font.setPixelSize(style["fontSize"])
        if "bold" in style and style["bold"]:
            font.setBold(True)
        widget.setFont(font)

        if "width" in style and "height" in style:
            widget.setFixedSize(style["width"], style["height"])
        elif "width" in style:
            widget.setFixedWidth(style["width"])
        elif "height" in style:
            widget.setFixedHeight(style["height"])

        if "padding" in style:
            p = style["padding"]
            if isinstance(p, (int, float)):
                widget.setContentsMargins(p, p, p, p)

        ss = []
        if "cornerRadius" in style:
            ss.append(f"border-radius: {style['cornerRadius']}px;")
            ss.append("border: none;")
        if "bgColor" in style:
            ss.append(f"background-color: {style['bgColor']};")
        if "color" in style:
            ss.append(f"color: {style['color']};")
        if ss:
            widget.setStyleSheet(widget.styleSheet() + " ".join(ss))

    def create_layout(self, style):
        layout_type = style.get("layout")
        if layout_type == "vertical":
            lay = QVBoxLayout()
        elif layout_type == "horizontal":
            lay = QHBoxLayout()
        else:
            return None

        if "gap" in style:
            lay.setSpacing(style["gap"])

        align_map = {"center": Qt.AlignCenter, "left": Qt.AlignLeft, "right": Qt.AlignRight}
        if "align" in style and style["align"] in align_map:
            lay.setAlignment(align_map[style["align"]])

        return lay

    def add_child(self, parent_layout, child):
        if parent_layout is not None:
            parent_layout.addWidget(child)

    def add_grid_child(self, grid_layout, child, row, col):
        grid_layout.addWidget(child, row, col)

    def bind_event(self, widget, event_type, handler):
        if event_type == "click" and isinstance(widget, QPushButton):
            widget.clicked.connect(lambda checked: handler())
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_backends.py -v`
Expected: all 9 tests PASS

- [ ] **Step 6: Commit**

```bash
git add dsl/backends/base.py dsl/backends/pyqt5.py tests/test_backends.py
git commit -m "feat: UIBackend abstraction + PyQt5 backend with tests"
```

---

### Task 4: DSL Loader Core

**Files:**
- Create: `dsl/loader.py`
- Create: `tests/test_loader.py`

- [ ] **Step 1: Write failing test for loader**

```python
# tests/test_loader.py
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


def test_load_inventory_page(app):
    path = os.path.join(PAGES_DIR, "inventory.json")
    if not os.path.exists(path):
        pytest.skip("inventory.json not yet created")
    page = DSLPage().load(path)
    assert page.get("title") is not None
    assert page.get("close_btn") is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_loader.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dsl.loader'`

- [ ] **Step 3: Implement loader.py**

```python
# dsl/loader.py
import inspect
import json
from .backends.pyqt5 import PyQt5Backend
from .schema import validate_dsl


class DSLPage:

    def __init__(self, backend=None):
        self._backend = backend or PyQt5Backend()
        self._widgets = {}
        self._events = {}
        self.root = None

    def load(self, dsl_path):
        from PyQt5.QtWidgets import QApplication
        self._app = QApplication.instance() or QApplication([])
        with open(dsl_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        validate_dsl(data)
        self.root = self._build(data["root"])
        return self

    def on(self, event_name, callback):
        self._events[event_name] = callback
        return self

    def get(self, widget_id):
        return self._widgets.get(widget_id)

    def unload(self):
        if self.root:
            self.root.close()
        self._widgets.clear()
        self._events.clear()

    def show(self):
        self.root.show()
        self._app.exec_()

    def _build(self, node):
        type_name = node["type"]
        props = node.get("props", {})
        style = node.get("style", {})

        widget = self._backend.create(type_name, props)

        if "id" in node:
            self._widgets[node["id"]] = widget
            widget._dsl_id = node["id"]
        else:
            widget._dsl_id = ""

        self._backend.apply_style(widget, style)

        layout = self._backend.create_layout(style)
        if layout is not None:
            widget.setLayout(layout)

        children_data = node.get("children", [])
        if type_name == "GridView":
            grid_layout = widget.layout()
            cols = props.get("columns", 1)
            for idx, child_data in enumerate(children_data):
                child = self._build(child_data)
                row, col = divmod(idx, cols)
                self._backend.add_grid_child(grid_layout, child, row, col)
        else:
            for child_data in children_data:
                child = self._build(child_data)
                self._backend.add_child(layout, child)

        for event_type, event_name in node.get("events", {}).items():
            wid = widget._dsl_id
            self._backend.bind_event(
                widget, event_type,
                lambda name=event_name, w=wid: self._dispatch(name, w)
            )

        return widget

    def _dispatch(self, event_name, widget_id):
        if event_name not in self._events:
            return
        handler = self._events[event_name]
        sig = inspect.signature(handler)
        if sig.parameters:
            handler(widget_id)
        else:
            handler()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_loader.py -v`
Expected: all 6 tests PASS (inventory may skip if not moved yet)

- [ ] **Step 5: Commit**

```bash
git add dsl/loader.py tests/test_loader.py
git commit -m "feat: DSL loader with event dispatch and backend abstraction"
```

---

### Task 5: CSS Mapper

**Files:**
- Create: `dsl/converter/css_mapper.py`
- Create: `tests/test_css_mapper.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_css_mapper.py
from dsl.converter.css_mapper import map_css_to_style

def test_basic_color():
    assert map_css_to_style({"background-color": "#ff0000"}) == {"bgColor": "#ff0000"}

def test_font_size():
    assert map_css_to_style({"font-size": "24px"}) == {"fontSize": 24}

def test_font_weight_bold():
    assert map_css_to_style({"font-weight": "bold"}) == {"bold": True}

def test_font_weight_normal():
    assert map_css_to_style({"font-weight": "normal"}) == {"bold": False}

def test_border_radius():
    assert map_css_to_style({"border-radius": "8px"}) == {"cornerRadius": 8}

def test_opacity():
    assert map_css_to_style({"opacity": "0.5"}) == {"opacity": 0.5}

def test_padding():
    assert map_css_to_style({"padding": "20px"}) == {"padding": 20}

def test_unknown_property_ignored():
    assert map_css_to_style({"cursor": "pointer"}) == {}

def test_width_height():
    assert map_css_to_style({"width": "100px", "height": "50px"}) == {"width": 100, "height": 50}

def test_flex_layout():
    assert map_css_to_style({"display": "flex", "flex-direction": "column"}) == {"layout": "vertical"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_css_mapper.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement css_mapper.py**

```python
# dsl/converter/css_mapper
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_css_mapper.py -v`
Expected: all 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add dsl/converter/css_mapper.py tests/test_css_mapper.py
git commit -m "feat: CSS property to DSL style mapper with tests"
```

---

### Task 6: HTML → DSL Converter

**Files:**
- Create: `dsl/converter/html_to_dsl.py`
- Create: `dsl/mappings.json`
- Create: `tests/test_converter.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_converter.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_converter.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Create mappings.json**

```json
{
  "custom_mappings": {}
}
```

- [ ] **Step 4: Implement html_to_dsl.py**

```python
# dsl/converter/html_to_dsl.py
import json
import re
from bs4 import BeautifulSoup
from .css_mapper import map_css_to_style

TAG_MAP = {
    "div": "Panel",
    "button": "Button",
    "span": "Text", "p": "Text",
    "h1": "Text", "h2": "Text", "h3": "Text",
    "h4": "Text", "h5": "Text", "h6": "Text",
    "img": "Image",
    "ul": "ListView", "ol": "ListView",
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_converter.py -v`
Expected: all 5 tests PASS

- [ ] **Step 6: Commit**

```bash
git add dsl/converter/html_to_dsl.py dsl/mappings.json tests/test_converter.py
git commit -m "feat: HTML to DSL converter with CSS mapping and custom tag support"
```

---

### Task 7: Demo Pages & Integration Test

**Files:**
- Create: `demo/pages/inventory.json` (move from old demo/)
- Create: `demo/pages/settings.json`
- Create: `demo/run.py`
- Modify: `tests/test_loader.py` — remove skip, inventory now exists

- [ ] **Step 1: Create inventory.json in new location**

Move existing `demo/inventory.json` to `demo/pages/inventory.json`.

- [ ] **Step 2: Create settings.json to test Slider/Input/Toggle**

```json
{
  "version": 1,
  "name": "settings_page",
  "root": {
    "type": "Panel",
    "id": "settings_bg",
    "props": { "width": 500, "height": 400 },
    "style": {
      "bgColor": "#1a1a2e",
      "padding": 20,
      "layout": "vertical",
      "gap": 12,
      "align": "left"
    },
    "children": [
      {
        "type": "Text",
        "id": "settings_title",
        "props": { "value": "设置" },
        "style": { "fontSize": 24, "color": "#FFFFFF", "bold": true }
      },
      {
        "type": "Panel",
        "id": "volume_row",
        "style": { "layout": "horizontal", "gap": 10 },
        "children": [
          {
            "type": "Text",
            "props": { "value": "音量" },
            "style": { "fontSize": 16, "color": "#CCCCCC", "width": 80 }
          },
          {
            "type": "Slider",
            "id": "volume_slider",
            "props": { "min": 0, "max": 100, "value": 80 },
            "style": { "width": 200 }
          }
        ]
      },
      {
        "type": "Panel",
        "id": "name_row",
        "style": { "layout": "horizontal", "gap": 10 },
        "children": [
          {
            "type": "Text",
            "props": { "value": "昵称" },
            "style": { "fontSize": 16, "color": "#CCCCCC", "width": 80 }
          },
          {
            "type": "Input",
            "id": "name_input",
            "props": { "placeholder": "请输入昵称", "value": "Player1" },
            "style": { "width": 200, "height": 30, "bgColor": "#16213e", "color": "#FFFFFF", "cornerRadius": 4 }
          }
        ]
      },
      {
        "type": "Button",
        "id": "save_btn",
        "props": { "text": "保存" },
        "style": { "width": 120, "height": 36, "bgColor": "#0f3460", "color": "#FFFFFF", "cornerRadius": 4 },
        "events": { "click": "on_save" }
      }
    ]
  }
}
```

- [ ] **Step 3: Create demo run.py**

```python
# demo/run.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dsl.loader import DSLPage

PAGES_DIR = os.path.join(os.path.dirname(__file__), "pages")


def inventory_demo():
    page = DSLPage().load(os.path.join(PAGES_DIR, "inventory.json"))

    items = {
        "slot_0": {"name": "木剑", "desc": "普通木剑，攻击+5", "count": 1},
        "slot_1": {"name": "药水", "desc": "恢复50HP", "count": 3},
    }

    def on_slot_click(widget_id):
        if widget_id not in items:
            return
        item = items[widget_id]
        detail = page.get("detail_text")
        if detail:
            detail.setText(f"【{item['name']}】{item['desc']}  x{item['count']}")
        title = page.get("title")
        if title:
            title.setText(f"背包 — 已选中: {item['name']}")

    def on_close():
        page.unload()
        sys.exit(0)

    page.on("on_slot_click", on_slot_click)
    page.on("on_close", on_close)
    page.show()


def settings_demo():
    page = DSLPage().load(os.path.join(PAGES_DIR, "settings.json"))

    def on_save():
        name = page.get("name_input").text()
        volume = page.get("volume_slider").value()
        print(f"Saved: name={name}, volume={volume}")

    page.on("on_save", on_save)
    page.show()


if __name__ == "__main__":
    demo = sys.argv[1] if len(sys.argv) > 1 else "inventory"
    if demo == "settings":
        settings_demo()
    else:
        inventory_demo()
```

- [ ] **Step 4: Run integration test — all tests pass including inventory**

Run: `python3 -m pytest tests/ -v`
Expected: all tests PASS

- [ ] **Step 5: Run demo to verify visually**

Run: `python3 demo/run.py inventory`
Expected: inventory window opens, clicking items updates detail panel

Run: `python3 demo/run.py settings`
Expected: settings window opens with slider, input, and save button

- [ ] **Step 6: Clean up old demo files**

Remove old `demo/dsl_loader.py`, `demo/main.py`, `demo/inventory.json`.

- [ ] **Step 7: Commit**

```bash
git add demo/ tests/
git rm demo/dsl_loader.py demo/main.py demo/inventory.json
git commit -m "feat: demo pages (inventory + settings) with run entry point"
```

---

### Task 8: End-to-End HTML → DSL → UI Test

**Files:**
- Create: `tests/test_e2e.py`

- [ ] **Step 1: Write E2E test**

```python
# tests/test_e2e.py
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

    clicked = {"fired": False}
    page.on("on_e2e_btn", lambda wid: clicked.update(fired=True))
    # Note: event name comes from DSL events, this HTML has none.
    # Verify the widget tree structure is correct.
    assert page.root is not None
```

- [ ] **Step 2: Run E2E test**

Run: `python3 -m pytest tests/test_e2e.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_e2e.py
git commit -m "test: end-to-end HTML → DSL → UI pipeline test"
```

---

## Self-Review Checklist

- [x] Spec coverage: every section maps to a task (schema → T2, backend → T3, loader → T4, converter → T5-T6, demo → T7, e2e → T8)
- [x] No placeholders: all code is complete, no TBD/TODO
- [x] Type consistency: `widget_id` parameter name consistent across loader, backends, and tests; `bgColor`/`cornerRadius` naming consistent in schema, mapper, and backend
- [x] DRY: backend abstraction eliminates duplicated widget creation logic
- [x] YAGNI: no animation support, no runtime CSS parser, no hot-reload — only what the spec requires
