from kivy.event import EventDispatcher
from kivy.uix.widget import Widget


class Dispatcher(EventDispatcher):
    """Handle custom events"""

    def __init__(self: Widget, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type("on_clear_files")
        self.register_event_type("on_add_transform_item")
        self.register_event_type("on_name_changer_update")
        self.register_event_type("on_output_format_update")

    def on_clear_files(self, *args, **kwargs):
        pass

    def on_add_transform_item(self, *args, **kwargs):
        pass

    def on_name_changer_update(self, *args, **kwargs):
        pass

    def on_output_format_update(self, *args, **kwargs):
        pass


dispatcher = Dispatcher()
