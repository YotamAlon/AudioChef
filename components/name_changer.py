import logging

from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout

import consts
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

    def on_kv_post(self, base_widget):
        state.set_watcher(consts.CURRENT_NAME_CHANGE_PARAMS, self.load_state)
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
        state.set_prop(consts.CURRENT_NAME_CHANGE_PARAMS, new_name_change_parameters)

    def switch_widgets(self):
        for widget_name in self.ids:
            hide = not widget_name.startswith(self.mode)
            toggle_widget(self.ids[widget_name], hide)

    def load_state(self, state: NameChangeParameters):
        logger.debug(f"NameChanger: loading state {state}")
        self.mode = state.mode
        self.ids.wildcards_input.text = state.wildcards_input
        self.ids.replace_from_input.text = state.replace_from_input
        self.ids.replace_to_input.text = state.replace_to_input
