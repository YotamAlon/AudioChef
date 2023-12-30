import dataclasses
from typing import List

from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

import utils.event_dispatcher
from components.helper_classes import (
    OptionsBox,
    PresetButton,
)
from components.name_changer import NameChanger
from components.transformation_form import TransformationForm
from consts import CURRENT_PRESET
from controller import logger, Controller
from models.preset import Preset, Transformation, NameChangeParameters, PresetMetadata
from repository import PresetRepository
from utils.audio_formats import AudioFile
from utils.state import state


class ExtensionBox(OptionsBox):
    def load_from_state(self, ext: str) -> None:
        self.text = ext


class TransformsBox2(BoxLayout):
    def load_from_state(self, transformations: list[Transformation]) -> None:
        self.clear_widgets()
        for transform in transformations:
            self.add_widget(TransformationForm(remove_callback=self.remove_widget))
            logger.debug(self.children)
            self.children[0].load_state(transform)

    def add_transform_item(self, *_):
        preset: Preset = state.get_prop(CURRENT_PRESET)
        transformations = preset.transformations + [
            Transformation(name=None, params={})
        ]
        new_preset = dataclasses.replace(preset, transformations=transformations)
        state.set_prop(CURRENT_PRESET, new_preset)


class AudioChefWindow(BoxLayout):
    name_changer: NameChanger = ObjectProperty()
    name_locked = BooleanProperty()
    ext_box: ExtensionBox = ObjectProperty()
    ext_locked = BooleanProperty()
    transforms_box: TransformsBox2 = ObjectProperty()
    transforms_locked: BooleanProperty()
    presets_box: Widget = ObjectProperty()

    def __init__(self, **kwargs):
        self.selected_transformations = []
        super().__init__(**kwargs)
        utils.event_dispatcher.dispatcher.bind(
            on_add_transform_item=self.transforms_box.add_transform_item
        )

    def on_kv_post(self, base_widget):
        state.set_watcher(CURRENT_PRESET, self._load_preset_into_ui)
        self._load_preset_buttons()
        default_preset = PresetRepository.get_default()
        if default_preset:
            preset = default_preset
        else:
            preset = Preset(
                ext="",
                transformations=[],
                name_change_parameters=NameChangeParameters(
                    mode="replace",
                    wildcards_input="",
                    replace_from_input="",
                    replace_to_input="",
                ),
            )

        state.set_prop(CURRENT_PRESET, preset)

    def _load_preset_into_ui(self, preset: Preset):
        if not self.ext_locked:
            self.ext_box.load_from_state(preset.ext)

        if not self.transforms_locked:
            self.transforms_box.load_from_state(preset.transformations)

        if not self.name_locked:
            self.name_changer.load_state(preset.name_change_parameters)

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

    def execute_preset(self) -> None:
        preset = state.get_prop(CURRENT_PRESET)
        transformations = self.get_transformations()
        selected_files: List[AudioFile] = state.get_prop("selected_files")
        Controller.execute_preset(preset.ext, selected_files, preset.transformations)

    def save_preset(self):
        current_preset: Preset = state.get_prop(CURRENT_PRESET)
        current_preset = dataclasses.replace(
            current_preset,
            transformations=[
                Transformation(
                    name=child.get_state()["transform_name"],
                    params=child.get_state()["args"],
                )
                for child in self.transforms_box.children[::-1]
            ],
        )
        preset_metadata = PresetRepository.save_preset(current_preset)
        self._add_preset_button(preset_metadata)

    def load_preset(self, preset_id: int) -> None:
        preset = PresetRepository.get_by_id(preset_id)
        state.set_prop(CURRENT_PRESET, preset)
        logger.debug(self.ext_box.options)

    def remove_preset(self, preset_id: int) -> None:
        PresetRepository.delete(preset_id)
        preset_buttons: list[PresetButton] = self.presets_box.children[:]
        for button in preset_buttons:
            if button.preset_id == preset_id:
                self.presets_box.remove_widget(button)
                break

    def get_transformations(self):
        return [
            child.get_selected_tranform_and_args()
            for child in self.transforms_box.children
        ]


class ExtBox(BoxLayout):
    ext_text = StringProperty()

    def on_ext_text(self, *_):
        preset: Preset = state.get_prop(CURRENT_PRESET)
        new_preset = dataclasses.replace(preset, ext=self.ext_text)
        state.set_prop(CURRENT_PRESET, new_preset)
