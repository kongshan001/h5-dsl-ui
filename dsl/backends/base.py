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
