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
