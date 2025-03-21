import logging

from kivy.uix.boxlayout import BoxLayout

from audio_chef.kivy_helpers import toggle_widget
from audio_chef.models.preset import NameChangeParameters

logger = logging.getLogger("audiochef")


class NameChangerBox(BoxLayout):
    def on_kv_post(self, base_widget):
        self.switch_widgets()

    def switch_widgets(self):
        for widget_name in ['wildcards_box', 'replace_box']:
            hide = not widget_name.startswith(self.ids.name_changer.mode)
            toggle_widget(self.ids.name_changer.ids[widget_name], hide)

    def load_state(self, name_change_parameters: NameChangeParameters):
        if not self.ids.lock.selected:
            return

        logger.debug(f"NameChangerBox: loading state {name_change_parameters}")
        self.ids.name_changer.mode = name_change_parameters.mode
        self.ids.name_changer.ids.wildcards_input.text = (
            name_change_parameters.wildcards_input
        )
        self.ids.name_changer.ids.replace_from_input.text = (
            name_change_parameters.replace_from_input
        )
        self.ids.name_changer.ids.replace_to_input.text = (
            name_change_parameters.replace_to_input
        )
        self.switch_widgets()
