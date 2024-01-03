from typing import List

from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from components.extension_box import ExtBox
from components.helper_classes import PresetButton
from components.name_changer import NameChangerBox
from components.transforms_box import TransformsBox
from consts import CURRENT_PRESET
from controller import Controller
from models.preset import Preset, NameChangeParameters, PresetMetadata, Transformation
from repository import PresetRepository
from utils.audio_formats import AudioFile
from utils.state import state


class AudioChefWindow(BoxLayout):
    name_changer: NameChangerBox = ObjectProperty()
    name_locked = BooleanProperty()
    ext_box: ExtBox = ObjectProperty()
    transforms_box: TransformsBox = ObjectProperty()
    presets_box: Widget = ObjectProperty()

    def __init__(self, **kwargs):
        self.selected_transformations = []
        super().__init__(**kwargs)

    def on_kv_post(self, base_widget):
        self._load_preset_buttons()

    def update_ext_to_ui(self, ext: str) -> None:
        self.ext_box.load_state(ext)

    def update_transformations_to_ui(self, transformations: list[Transformation]):
        self.transforms_box.load_state(transformations)

    def update_name_changer_to_ui(self, name_change_parameters: NameChangeParameters):
        self.name_changer.load_state(name_change_parameters)

    def _load_preset_buttons(self):
        metadata = PresetRepository.get_metadata()
        self.presets_box.clear_widgets()
        for preset_metadata in metadata:
            self._add_preset_button(preset_metadata)

    def _add_preset_button(self, preset_metadata: PresetMetadata) -> None:
        self.presets_box.add_widget(
            PresetButton(
                preset_id=preset_metadata.id,
                preset_name=preset_metadata.name,
                default=preset_metadata.default,
                load_preset=self.load_preset,
                rename_preset=PresetRepository.rename_preset,
                remove_preset=self.remove_preset,
                make_default=PresetRepository.make_default,
            )
        )

    @staticmethod
    def execute_preset() -> None:
        preset = state.get_prop(CURRENT_PRESET)
        selected_files: List[AudioFile] = state.get_prop("selected_files")
        Controller.execute_preset(preset.ext, selected_files, preset.transformations)

    def save_preset(self):
        current_preset: Preset = state.get_prop(CURRENT_PRESET)
        preset_metadata = PresetRepository.save_preset(current_preset)
        self._add_preset_button(preset_metadata)

    @staticmethod
    def load_preset(preset_id: int) -> None:
        preset = PresetRepository.get_by_id(preset_id)
        state.set_prop(CURRENT_PRESET, preset)

    def remove_preset(self, preset_id: int) -> None:
        PresetRepository.delete(preset_id)
        preset_buttons: list[PresetButton] = self.presets_box.children[:]
        for button in preset_buttons:
            if button.preset_id == preset_id:
                self.presets_box.remove_widget(button)
                break
