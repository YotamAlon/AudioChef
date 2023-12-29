import dataclasses
import logging
from datetime import datetime

from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout

from consts import CURRENT_PRESET
from kivy_helpers import toggle_widget
from models.preset import NameChangeParameters
from utils.state import state

logger = logging.getLogger("audiochef")


class NameChanger(BoxLayout):
    _wildcards = ["$item", "$date"]
    mode = StringProperty("replace")
    preview_callback = ObjectProperty()
    wildcards_input_text = StringProperty()
    replace_from_input_text = StringProperty()
    replace_to_input_text = StringProperty()

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
        self.switch_widgets()

    def on_mode(self, instance, mode):
        logger.debug(f"Switching mode to {self.mode}")
        self.switch_widgets()
        self.update_state()

    def on_wildcards_input_text(self, *_):
        self.update_state()

    def on_replace_from_input_text(self, *_):
        self.update_state()

    def on_replace_to_input_text(self, *_):
        self.update_state()

    def update_state(self, *_):
        new_name_change_parameters = NameChangeParameters(
            mode=self.mode,
            wildcards_input=self.wildcards_input_text,
            replace_from_input=self.replace_from_input_text,
            replace_to_input=self.replace_to_input_text,
        )
        preset = state.get_prop(CURRENT_PRESET)
        new_preset = dataclasses.replace(
            preset, name_change_parameters=new_name_change_parameters
        )
        state.set_prop(CURRENT_PRESET, new_preset)

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

    def load_state(self, state: NameChangeParameters):
        logger.debug(f"NameChanger: loading state {state}")
        self.mode = state.mode
        self.ids.wildcards_input.text = state.wildcards_input
        self.ids.replace_from_input.text = state.replace_from_input
        self.ids.replace_to_input.text = state.replace_to_input
