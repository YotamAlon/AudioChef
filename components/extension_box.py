import dataclasses

from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout

from consts import CURRENT_PRESET
from models.preset import Preset
from utils.state import state


class ExtBox(BoxLayout):
    ext_text = StringProperty()

    def on_ext_text(self, *_):
        preset: Preset = state.get_prop(CURRENT_PRESET)
        new_preset = dataclasses.replace(preset, ext=self.ext_text)
        state.set_prop(CURRENT_PRESET, new_preset)

    def load_from_state(self, ext: str) -> None:
        if not self.ids.lock.selected:
            return
        self.ext_text = ext
