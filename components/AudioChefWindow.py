import os
import uuid
import logging
import traceback
from pedalboard import Pedalboard

from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget

from components.NameChanger import NameChanger
from components.TransformationForm import TransformationForm
from components.helper_classes import (
    OptionsBox,
    ConfigurationFile,
    PresetButton,
    UnexecutableRecipeError,
)

from utils.audio_formats import SUPPORTED_AUDIO_FORMATS
from utils.transformations import TRASNFORMATIONS
from utils.State import state

logger = logging.getLogger("audiochef")


class AudioChefWindow(BoxLayout):
    name_changer: NameChanger = ObjectProperty()
    name_locked = BooleanProperty()
    ext_box: OptionsBox = ObjectProperty()
    ext_locked = BooleanProperty()
    transforms_box: Widget = ObjectProperty()
    transforms_locked: BooleanProperty()
    presets_box: Widget = ObjectProperty()

    def __init__(self, **kwargs):
        logger.debug("Starting initialization of AudioChef main window ...")
        self.presets_file = ConfigurationFile()
        self.presets_file.initialize(TRASNFORMATIONS)
        self.selected_transformations = []
        super().__init__(**kwargs)
        logger.debug("Initialization of AudioChef main window completed.")

    def on_kv_post(self, base_widget):
        presets = self.presets_file.get_presets()
        self.reload_presets(presets)
        default_preset_id = next(
            (i for i, preset in enumerate(presets) if preset.get("default", False)),
            None,
        )
        if default_preset_id:
            self.load_preset(default_preset_id)

    def reload_presets(self, presets):
        self.presets_box.clear_widgets()
        for preset in presets:
            self.presets_box.add_widget(
                PresetButton(
                    preset_id=preset.get("order", 0),
                    preset_name=preset["name"],
                    default=preset.get("default", False),
                    load_preset=self.load_preset,
                    rename_preset=self.rename_preset,
                    remove_preset=self.remove_preset,
                    make_default=self.make_preset_default,
                )
            )

    def execute_preset(self):
        try:
            self.check_input_file_formats()
            self.check_output_file_formats()

            transformations = self.get_transformations()
            self.check_selected_transformation(transformations)
            selected_files = state.get_prop("selected_files")
            for audio_file in selected_files:
                outfile_name = self.get_output_name(audio_file.source_name)
                outfile_ext = self.get_output_ext(audio_file.source_ext)

                audio, sample_rate = audio_file.get_audio_data()

                board = self.prepare_board(sample_rate, transformations)
                res = board(audio)

                audio_file.write_audio_data(outfile_name, outfile_ext, res, sample_rate)
        except UnexecutableRecipeError as e:
            logger.error(repr(e))
            Popup(
                title="I Encountered an Error!",
                content=Label(
                    text="I wrote all the info for the developer in a log file.\n"
                    "Check the folder with AudioChef it in."
                ),
            )
        except Exception:
            logger.error(traceback.format_exc())
            Popup(
                title="I Encountered an Error!",
                content=Label(
                    text="I wrote all the info for the developer in a log file.\n"
                    "Check the folder with AudioChef it in."
                ),
            )

    def save_preset(self):
        preset = {
            "name": str(uuid.uuid4()),
            "ext": state.get_prop("output_ext"),
            "transformations": [
                child.get_state() for child in self.transforms_box.children[::-1]
            ],
            "name_changer": self.name_changer.get_state(),
        }
        self.presets_file.save_preset(preset)

    def load_preset(self, preset_id):
        logger.debug(f"AudioChefWindow: loading preset {preset_id}")
        preset = self.presets_file.get_preset(preset_id)
        logger.debug(f"AudioChefWindow: preset {preset_id} - {preset}")
        logger.debug(self.ext_box.options)
        if not self.ext_locked:
            self.ext_box.text = preset["ext"]

        if not self.transforms_locked:
            self.transforms_box.clear_widgets()
            for transform_state in preset["transformations"]:
                self.add_tranform_item()
                logger.debug(self.transforms_box.children)
                self.transforms_box.children[0].load_state(transform_state)

        if not self.name_locked:
            self.name_changer.load_state(preset["name_changer"])

    def rename_preset(self, preset_name, new_name):
        self.presets_file.rename_preset(preset_name, new_name)
        self.reload_presets(self.presets_file.get_presets())

    def remove_preset(self, preset_name):
        self.presets_file.remove_preset(preset_name)
        self.reload_presets(self.presets_file.get_presets())

    def make_preset_default(self, preset_name, val):
        presets = self.presets_file.get_presets()
        for preset in presets:
            if preset["name"] == preset_name:
                preset["default"] = val
        self.presets_file.set_presets(presets)

    def check_input_file_formats(self):
        selected_files = state.get_prop("selected_files")
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

    def check_output_file_formats(self):
        if not self.ext_box.validated:
            raise UnexecutableRecipeError(
                f'"{self.ext_box.text}" is not a supported output format'
            )

    def get_transformations(self):
        return [child.get_selected_tranform() for child in self.transforms_box.children]

    def check_selected_transformation(self, transformations):
        if len(transformations) == 0 or any(
            transform is None for transform in transformations
        ):
            raise UnexecutableRecipeError("You must choose a transformation to apply")

    def prepare_board(self, sample_rate, transformations):
        return Pedalboard(
            [transform(**kwargs) for (_, transform), kwargs in transformations],
            sample_rate=sample_rate,
        )

    def add_tranform_item(self):
        self.transforms_box.add_widget(
            TransformationForm(remove_callback=self.remove_transformation)
        )

    def remove_transformation(self, accordion_item):
        self.transforms_box.remove_widget(accordion_item)


