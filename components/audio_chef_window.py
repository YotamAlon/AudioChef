import logging
import os
import uuid
from typing import List

import pedalboard
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget

import utils.event_dispatcher
from components.helper_classes import (
    OptionsBox,
    PresetButton,
    UnexecutableRecipeError,
)
from components.name_changer import NameChanger
from components.transformation_form import TransformationForm
from models.preset import Preset
from utils.audio_formats import SUPPORTED_AUDIO_FORMATS, AudioFile
from utils.state import state

CURRENT_PRESET = "current_preset"

logger = logging.getLogger("audiochef")


class ExtensionBox(OptionsBox):
    def load_from_state(self, ext: str) -> None:
        self.text = ext


class TransformsBox2(BoxLayout):
    def load_from_state(self, transformations: list[dict]) -> None:
        self.clear_widgets()
        for transform_state in transformations:
            self.add_widget(TransformationForm(remove_callback=self.remove_widget))
            logger.debug(self.children)
            self.children[0].load_state(transform_state)

    def add_transform_item(self, *_):
        self.add_widget(TransformationForm(remove_callback=self.remove_widget))


class AudioChefWindow(BoxLayout):
    name_changer: NameChanger = ObjectProperty()
    name_locked = BooleanProperty()
    ext_box: ExtensionBox = ObjectProperty()
    ext_locked = BooleanProperty()
    transforms_box: TransformsBox2 = ObjectProperty()
    transforms_locked: BooleanProperty()
    presets_box: Widget = ObjectProperty()

    def __init__(self, **kwargs):
        logger.debug("Starting initialization of AudioChef main window ...")
        self.selected_transformations = []
        super().__init__(**kwargs)
        utils.event_dispatcher.dispatcher.bind(
            on_add_transform_item=self.transforms_box.add_transform_item
        )
        logger.debug("Initialization of AudioChef main window completed.")

    def on_kv_post(self, base_widget):
        self.reload_presets()
        default_preset_id = Preset.get_or_none(default=True)
        if default_preset_id:
            self.load_preset(default_preset_id)

    def reload_presets(self):
        presets = Preset.select()
        self.presets_box.clear_widgets()
        for preset in presets:
            self.presets_box.add_widget(
                PresetButton(
                    preset_id=preset.id,
                    preset_name=preset.name,
                    default=preset.default,
                    load_preset=self.load_preset,
                    rename_preset=self.rename_preset,
                    remove_preset=self.remove_preset,
                    make_default=Preset.make_default,
                )
            )

    def execute_preset(self) -> None:
        try:
            self.check_input_file_formats(
                selected_files=state.get_prop("selected_files")
            )
            self.check_output_file_formats(self.ext_box.text)

            transformations = self.get_transformations()
            self.check_selected_transformation(transformations)
            selected_files: List[AudioFile] = state.get_prop("selected_files")
            for audio_file in selected_files:
                audio, sample_rate = audio_file.get_audio_data()

                board = self.prepare_board(transformations)
                res = board(audio, sample_rate)

                audio_file.write_output_file(res, sample_rate)
        except UnexecutableRecipeError as e:
            logger.error(repr(e))
            Popup(
                title="I Encountered an Error!",
                content=Label(
                    text="I wrote all the info for the developer in a log file.\n"
                    "Check the folder with AudioChef it in."
                ),
            )

    def save_preset(self):
        preset = Preset.create(
            name=str(uuid.uuid4()),
            ext=state.get_prop("output_ext", ""),
            transformations=[
                child.get_state() for child in self.transforms_box.children[::-1]
            ],
            name_changer=self.name_changer.get_state(),
        )
        logger.debug(f"Saved Preset {preset} and reloading preset list")
        self.reload_presets()

    def load_preset(self, preset_id):
        logger.debug(f"AudioChefWindow: loading preset {preset_id}")
        preset = Preset.get(id=preset_id)
        logger.debug(f"AudioChefWindow: preset {preset_id} - {preset}")
        state.set_prop(CURRENT_PRESET, preset)
        logger.debug(self.ext_box.options)

        if not self.ext_locked:
            self.ext_box.load_from_state(preset.ext)
        if not self.transforms_locked:
            self.transforms_box.load_from_state(preset.transformations)
        if not self.name_locked:
            self.name_changer.load_state(preset.name_changer)

    def rename_preset(self, preset_id, new_name):
        Preset.rename(preset_id, new_name)
        self.reload_presets()

    def remove_preset(self, preset_id):
        logger.debug(f"Deleting preset with id {preset_id}")
        Preset.delete_by_id(preset_id)
        self.reload_presets()

    def check_input_file_formats(self, selected_files: list[AudioFile]):
        for audio_file in selected_files:
            name, ext = os.path.splitext(audio_file.filename)

            if ext.lower()[1:] not in [
                format_.ext.lower()
                for format_ in SUPPORTED_AUDIO_FORMATS
                if format_.can_decode
            ]:
                raise UnexecutableRecipeError(
                    f'"{audio_file.filename}" is not in a supported format'
                )

    def check_output_file_formats(self, output_ext: str):
        if output_ext not in [
            format_.ext.lower()
            for format_ in SUPPORTED_AUDIO_FORMATS
            if format_.can_encode
        ]:
            raise UnexecutableRecipeError(
                f'"{output_ext}" is not a supported output format'
            )

    def get_transformations(self):
        return [
            child.get_selected_tranform_and_args()
            for child in self.transforms_box.children
        ]

    def check_selected_transformation(self, transformations):
        if len(transformations) == 0 or any(
            transform is None for transform in transformations
        ):
            raise UnexecutableRecipeError("You must choose a transformation to apply")

    def prepare_board(self, transformations):
        logger.debug(transformations)
        return pedalboard.Pedalboard(
            [transform(**kwargs) for transform, kwargs in transformations]
        )
