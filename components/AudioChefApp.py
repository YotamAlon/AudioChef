import configparser
import json
import os
import traceback
import uuid

from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import Metrics
from kivy.config import Config
from kivy.uix.settings import SettingsWithSidebar
from kivy.utils import platform
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from pedalboard import Pedalboard
from components.NameChanger import NameChanger
from components.TransformationForm import TransformationForm
from utils.audio_formats import load_audio_formats, SUPPORTED_AUDIO_FORMATS
from components.helper_classes import (
    OptionsBox,
    ConfigurationFile,
    PresetButton,
    UnexecutableRecipeError,
)
import logging
from utils.transformations import TRASNFORMATIONS
from utils.State import state, State
from utils.Dispatcher import dispatcher

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


class AudioChefApp(App):
    version = "0.3"
    settings_cls = SettingsWithSidebar
    use_kivy_settings = False
    icon = "assets/chef_hat.png"
    window_background_color = (220 / 255, 220 / 255, 220 / 255, 1)
    main_color = (43 / 255, 130 / 255, 229 / 255)
    light_color = (118 / 255, 168 / 255, 229 / 255)
    dark_color = (23 / 255, 63 / 255, 107 / 255)
    log_level = logging.INFO
    run_dir = None
    config: configparser.ConfigParser
    state: State = state
    min_width = 1280
    min_height = 720
    dispatcher = dispatcher
    support_audio_formats = SUPPORTED_AUDIO_FORMATS

    def __init__(self):
        logger.setLevel(self.log_level)
        super().__init__()

    def build(self):
        logger.info("Registering custom events ...")

        logger.info("Loading KV file ...")
        self.load_kv("../audio_chef.kv")

        logger.info("Loading audio formats ...")
        load_audio_formats()
        self.main_widget = AudioChefWindow()

        self.dispatcher.bind(on_add_transform_item=self.add_transform_item)

        logger.debug("Binding dropfile event ...")
        Window.clearcolor = app.window_background_color
        Window.size = (
            self.config.getfloat("Window", "width"),
            self.config.getfloat("Window", "height"),
        )
        Window.minimum_width = self.min_width
        Window.minimum_height = self.min_height
        if self.config.has_option("Window", "top") and self.config.has_option(
            "Window", "left"
        ):
            Window.top = self.config.getint("Window", "top")
            Window.left = self.config.getint("Window", "left")
        Window.bind(on_request_close=self.window_request_close)
        return self.main_widget

    def window_request_close(self, *args, **kwargs):
        # Window.size is automatically adjusted for density, must divide by density when saving size
        logger.debug("Saving window config before exiting ...")
        self.config.set("Window", "width", Window.size[0] / Metrics.density)
        self.config.set("Window", "height", Window.size[1] / Metrics.density)
        self.config.set("Window", "top", Window.top)
        self.config.set("Window", "left", Window.left)
        self.config.write()
        return False

    def build_config(self, config):
        Config.set('input', 'mouse', 'mouse,disable_multitouch')
        config.setdefaults(
            "Window", {"width": self.min_width, "height": self.min_height}
        )

        for transformation_name, transformation in TRASNFORMATIONS.items():
            arguments_dict = {}
            for argument in transformation.arguments:
                if argument.type is float:
                    arguments_dict[f"{argument.name} max"] = argument.max
                    arguments_dict[f"{argument.name} min"] = argument.min
                    arguments_dict[f"{argument.name} step"] = argument.step
            config.setdefaults(transformation_name, arguments_dict)

    def get_application_config(self, defaultpath="%(appdir)s/%(appname)s.ini"):
        if platform == "macosx":  # mac will not write into app folder
            s = "~/.%(appname)s.ini"
        else:
            s = defaultpath
        return super().get_application_config(defaultpath=s)

    def build_settings(self, settings):
        for transformation_name, transformation in TRASNFORMATIONS.items():
            arguments_list = []
            for argument in transformation.arguments:
                if argument.type is float:
                    arguments_list.append(
                        {
                            "type": "numeric",
                            "title": f"{argument.name} Max",
                            "desc": f"The maximum value to use for the slider of {argument.name} for {transformation_name}",
                            "section": transformation_name,
                            "key": f"{argument.name} max",
                        }
                    )
                    arguments_list.append(
                        {
                            "type": "numeric",
                            "title": f"{argument.name} Min",
                            "desc": f"The minimum value to use for the slider of {argument.name} for {transformation_name}",
                            "section": transformation_name,
                            "key": f"{argument.name} min",
                        }
                    )
                    arguments_list.append(
                        {
                            "type": "numeric",
                            "title": f"{argument.name} Step",
                            "desc": f"The step size to use for the slider of {argument.name} for {transformation_name}",
                            "section": transformation_name,
                            "key": f"{argument.name} step",
                        }
                    )
            settings.add_json_panel(
                transformation_name, self.config, data=json.dumps(arguments_list)
            )

    def change_name(self, old_name: str) -> str:
        return self.main_widget.change_name(old_name)

    def add_transform_item(self, *args, **kwargs):
        if hasattr(self, "main_widget"):
            self.main_widget.add_tranform_item()


app = AudioChefApp()
