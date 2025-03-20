from kivy.properties import BooleanProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from audio_chef.adapters.repository import PresetRepository
from audio_chef.components import FileList
from audio_chef.components.extension_box import ExtBox
from audio_chef.components.helper_classes import PresetButton
from audio_chef.components.name_changer import NameChangerBox
from audio_chef.components.transforms_box import TransformsBox
from audio_chef.models.preset import (
    NameChangeParameters,
    PresetMetadata,
    Transformation,
)
from audio_chef.utils.audio_formats import AudioFile


class AudioChefWindow(BoxLayout):
    name_changer: NameChangerBox = ObjectProperty()
    name_locked = BooleanProperty()
    ext_box: ExtBox = ObjectProperty()
    transforms_box: TransformsBox = ObjectProperty()
    presets_box: Widget = ObjectProperty()
    file_list: FileList = ObjectProperty()

    def __init__(self, **kwargs):
        self.selected_transformations = []
        super().__init__(**kwargs)

    def on_kv_post(self, base_widget):
        self._load_preset_buttons()

    def update_ext_to_ui(self, ext: str) -> None:
        self.ext_box.load_state(ext)
        self.file_list.ext = ext

    def update_transformations_to_ui(self, transformations: list[Transformation]):
        self.transforms_box.load_state(transformations)

    def update_available_transformations_to_ui(
        self, available_transformations: list[Transformation]
    ):
        self.transforms_box.load_available_tranformations(available_transformations)

    def update_name_changer_to_ui(self, name_change_parameters: NameChangeParameters):
        self.name_changer.load_state(name_change_parameters)
        self.file_list.name_change_parameters = name_change_parameters

    def _load_preset_buttons(self):
        metadata = PresetRepository.get_metadata()
        self.presets_box.clear_widgets()
        for preset_metadata in metadata:
            self.add_preset_button(preset_metadata)

    def add_preset_button(self, preset_metadata: PresetMetadata) -> None:
        self.presets_box.add_widget(
            PresetButton(
                preset_id=preset_metadata.id,
                preset_name=preset_metadata.name,
                default=preset_metadata.default,
                rename_preset=PresetRepository.rename_preset,
                remove_preset=self.remove_preset,
                make_default=PresetRepository.make_default,
            )
        )

    def remove_preset(self, preset_id: int) -> None:
        PresetRepository.delete(preset_id)
        preset_buttons: list[PresetButton] = self.presets_box.children[:]
        for button in preset_buttons:
            if button.preset_id == preset_id:
                self.presets_box.remove_widget(button)
                break

    def update_files_to_ui(self, selected_files: list[AudioFile]):
        self.file_list.update_files(selected_files)
