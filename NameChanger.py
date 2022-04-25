import logging
from datetime import datetime
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout

from Dispatcher import dispatcher
from state import state
from kivy_helpers import toggle_widget
logger = logging.getLogger("audiochef")


class NameChanger(BoxLayout):
    wildcards = ["$item", "$date"]
    mode = StringProperty("replace")
    preview_callback = ObjectProperty()

    def change_name(self, old_name: str) -> str:
        if self.mode == "wildcards":
            new_name = self.ids.wildcards_input.text
            new_name = new_name.replace("$item", old_name)
            new_name = new_name.replace("$date", str(datetime.today()))
            return new_name
        else:
            if self.ids.replace_from_input.text == "":
                return old_name
            return old_name.replace(
                self.ids.replace_from_input.text, self.ids.replace_to_input.text
            )

    def on_kv_post(self, base_widget):
        state.set_prop('name_change_func', self.change_name)

    def on_mode(self, instance, mode):
        self.switch_widgets()
        dispatcher.dispatch("on_name_changer_update")

    def switch_widgets(self):
        for widget_name in self.ids:
            hide = not widget_name.startswith(self.mode)
            toggle_widget(self.ids[widget_name], hide)

    def get_state(self):
        return {
            "mode": self.mode,
            "wildcards_input": self.ids.wildcards_input.text,
            "replace_from_input": self.ids.replace_from_input.text,
            "replace_to_input": self.ids.replace_to_input.text,
        }

    def load_state(self, state):
        logger.debug(f"NameChanger: loading state {state}")
        self.mode = state["mode"]
        self.ids.wildcards_input.text = state["wildcards_input"]
        self.ids.replace_from_input.text = state["replace_from_input"]
        self.ids.replace_to_input.text = state["replace_to_input"]
