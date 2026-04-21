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
        self._app.setStyle('Fusion')
        with open(dsl_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        validate_dsl(data)
        self.root = self._build(data["root"], {})
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

    def _build(self, node, parent_style):
        type_name = node["type"]
        props = node.get("props", {})
        style = dict(node.get("style", {}))

        # Inherit color from parent if not explicitly set
        if "color" not in style and "color" in parent_style:
            style["color"] = parent_style["color"]
        # Inherit fontSize from parent if not explicitly set
        if "fontSize" not in style and "fontSize" in parent_style:
            style["fontSize"] = parent_style["fontSize"]
        # Inherit textAlign from parent
        if "textAlign" not in style and "textAlign" in parent_style:
            style["textAlign"] = parent_style["textAlign"]
        # Inherit fontFamily from parent
        if "fontFamily" not in style and "fontFamily" in parent_style:
            style["fontFamily"] = parent_style["fontFamily"]
        # Inherit bold from parent
        if "bold" not in style and "bold" in parent_style:
            style["bold"] = parent_style["bold"]

        widget = self._backend.create(type_name, props)

        if "id" in node:
            self._widgets[node["id"]] = widget
            widget._dsl_id = node["id"]
        else:
            widget._dsl_id = ""

        self._backend.apply_style(widget, style)

        if "flex" in style and style["flex"] > 0:
            widget._flex = style["flex"]

        layout = self._backend.create_layout(style)
        children_data = node.get("children", [])
        is_grid = type_name == "GridView" or style.get("layout") == "grid"

        # Leaf widget types without children should never have layouts
        # (Text with gradient uses custom paintEvent; Input/Slider are single controls)
        # Button is excluded because it can have children (icon + label pattern)
        is_leaf_no_children = (
            type_name in ("Text", "Input", "Slider")
            or (type_name == "Button" and not children_data)
        )
        if is_leaf_no_children:
            layout = None

        # Auto-create layout for containers with children but no explicit layout
        # Use horizontal if any child has widthPercent (progress bars), else vertical
        if layout is None and not is_grid and children_data:
            has_width_pct = any(
                c.get("style", {}).get("widthPercent") is not None
                for c in children_data
            )
            auto_dir = "horizontal" if has_width_pct else "vertical"
            layout = self._backend.create_layout({"layout": auto_dir})

        if layout is not None:
            widget.setLayout(layout)

        children_data = node.get("children", [])
        jc = style.get("justifyContent", "")

        if is_grid:
            if layout is None:
                from PyQt5.QtWidgets import QGridLayout
                layout = QGridLayout()
                widget.setLayout(layout)
            grid_layout = widget.layout()
            grid_layout.setContentsMargins(0, 0, 0, 0)
            grid_layout.setSpacing(style.get("gap", 0))
            cols = style.get("columns", props.get("columns", 1))
            for idx, child_data in enumerate(children_data):
                child = self._build(child_data, style)
                row, col = divmod(idx, cols)
                self._backend.add_grid_child(grid_layout, child, row, col)
        else:
            if jc == "space-between" and children_data:
                for i, child_data in enumerate(children_data):
                    child = self._build(child_data, style)
                    if i > 0:
                        self._backend.add_stretch(layout)
                    self._add_child_flex(layout, child)
            elif jc == "space-around" and children_data:
                self._backend.add_stretch(layout, factor=1)
                for i, child_data in enumerate(children_data):
                    child = self._build(child_data, style)
                    self._add_child_flex(layout, child)
                    if i < len(children_data) - 1:
                        self._backend.add_stretch(layout, factor=2)
                    else:
                        self._backend.add_stretch(layout, factor=1)
            else:
                for child_data in children_data:
                    child = self._build(child_data, style)
                    self._add_child_flex(layout, child)

        for event_type, event_name in node.get("events", {}).items():
            wid = widget._dsl_id
            self._backend.bind_event(
                widget, event_type,
                lambda name=event_name, w=wid: self._dispatch(name, w)
            )

        return widget

    def _add_child_flex(self, layout, child):
        wp = getattr(child, '_width_percent', 0)
        flex = getattr(child, '_flex', 0)
        if wp > 0:
            self._backend.add_child_with_stretch(layout, child, int(wp), 100 - int(wp))
        elif flex > 0:
            self._backend.add_child_with_stretch(layout, child, int(flex * 100), 0)
        else:
            self._backend.add_child(layout, child)

    def _dispatch(self, event_name, widget_id):
        if event_name not in self._events:
            return
        handler = self._events[event_name]
        sig = inspect.signature(handler)
        if sig.parameters:
            handler(widget_id)
        else:
            handler()
