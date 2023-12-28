import uuid
from typing import List

from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

import utils.event_dispatcher
from components.helper_classes import (
    OptionsBox,
    PresetButton,
)
from components.name_changer import NameChanger
from components.transformation_form import TransformationForm
from controller import logger, Controller
from models.preset import PresetModel, Preset, Transformation, NameChangeParameters
from utils.audio_formats import AudioFile
from utils.state import state

CURRENT_PRESET = "current_preset"


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
        default_preset_id = PresetModel.get_or_none(default=True)
        if default_preset_id:
            self.load_preset(default_preset_id)

    def reload_presets(self):
        presets = PresetModel.select()
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
                    make_default=PresetModel.make_default,
                )
            )

    def execute_preset(self) -> None:
        output_ext = self.ext_box.text
        transformations = self.get_transformations()
        selected_files: List[AudioFile] = state.get_prop("selected_files")
        Controller.execute_preset(output_ext, selected_files, transformations)

    def save_preset(self):
        preset = PresetModel.create(
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
        preset = PresetModel.get(id=preset_id)
        logger.debug(f"AudioChefWindow: preset {preset_id} - {preset}")
        preset = Preset(
            name=preset.name,
            ext=preset.ext,
            transformations=[
                Transformation(
                    name=transformation["transform_name"], params=transformation["args"]
                )
                for transformation in preset.transformations
            ],
            name_change_parameters=NameChangeParameters(
                mode=preset.name_changer["mode"],
                wildcards_input=preset.name_changer["wildcards_input"],
                replace_from_input=preset.name_changer["replace_from_input"],
                replace_to_input=preset.name_changer["replace_to_input"],
            ),
        )

        def load_ext(preset: Preset):
            if not self.ext_locked:
                self.ext_box.load_from_state(preset.ext)

        def load_transformations(preset: Preset):
            if not self.transforms_locked:
                self.transforms_box.load_from_state(preset.transformations)

        def load_name_changer(preset: Preset):
            if not self.name_locked:
                self.name_changer.load_state(preset.name_change_parameters)

        state.set_watcher(CURRENT_PRESET, load_ext)
        state.set_watcher(CURRENT_PRESET, load_transformations)
        state.set_watcher(CURRENT_PRESET, load_name_changer)

        state.set_prop(CURRENT_PRESET, preset)

        logger.debug(self.ext_box.options)

    def rename_preset(self, preset_id, new_name):
        PresetModel.rename(preset_id, new_name)
        self.reload_presets()

    def remove_preset(self, preset_id):
        logger.debug(f"Deleting preset with id {preset_id}")
        PresetModel.delete_by_id(preset_id)
        self.reload_presets()

    def get_transformations(self):
        return [
            child.get_selected_tranform_and_args()
            for child in self.transforms_box.children
        ]
