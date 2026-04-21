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

    def add_child_with_stretch(self, parent_layout, child, fill_stretch, empty_stretch):
        """Add child with stretch factors for percentage-width elements."""
        ...

    @abstractmethod
    def bind_event(self, widget, event_type, handler):
        """Bind an event handler to widget."""
        ...

    def add_stretch(self, layout, factor=1):
        """Add stretch space to layout for justify-content effects."""
        if layout is not None:
            layout.addStretch(factor)
