import configparser
import dataclasses
import json
import logging

import kivy
import kivy.app
import kivy.base
import kivy.core.window
import kivy.metrics
import kivy.uix.settings
import peewee

import consts
from components.audio_chef_window import AudioChefWindow
from components.error_popup import ErrorPopup
from consts import CURRENT_PRESET
from models.preset import NameChangeParameters, Transformation, Preset
from repository import PresetModel, db_proxy, PresetRepository
from utils.audio_formats import SUPPORTED_AUDIO_FORMATS, load_audio_formats
from utils.event_dispatcher import dispatcher
from utils.state import State, state
from utils.transformations import TRANSFORMATIONS

logger = logging.getLogger("audiochef")


class AudioChefApp(kivy.app.App):
    version = "0.3"
    settings_cls = kivy.uix.settings.SettingsWithSidebar
    use_kivy_settings = False
    icon = "assets/chef_hat.png"
    window_background_color = (220 / 255, 220 / 255, 220 / 255, 1)
    main_color = (43 / 255, 130 / 255, 229 / 255)
    light_color = (118 / 255, 168 / 255, 229 / 255)
    dark_color = (23 / 255, 63 / 255, 107 / 255)
    log_level = logging.INFO
    config: configparser.ConfigParser
    state: State = state
    min_width = 1280
    min_height = 720
    dispatcher = dispatcher
    supported_audio_formats = SUPPORTED_AUDIO_FORMATS
    audio_chef_window: AudioChefWindow

    def __init__(self):
        logger.setLevel(self.log_level)
        super().__init__()

    def build(self):
        logger.info("Loading KV file ...")
        self.load_kv("audio_chef.kv")

        logger.info("Loading audio formats ...")
        load_audio_formats()

        logger.info("Initializing database ...")
        db = peewee.SqliteDatabase("presets.db")
        db_proxy.initialize(db)
        db.create_tables([PresetModel])

        logger.debug("Binding dropfile event ...")
        kivy.core.window.Window.clearcolor = app.window_background_color
        kivy.core.window.Window.size = (
            self.config.getfloat("Window", "width"),
            self.config.getfloat("Window", "height"),
        )
        kivy.core.window.Window.minimum_width = self.min_width
        kivy.core.window.Window.minimum_height = self.min_height
        if self.config.has_option("Window", "top") and self.config.has_option(
            "Window", "left"
        ):
            kivy.core.window.Window.top = self.config.getint("Window", "top")
            kivy.core.window.Window.left = self.config.getint("Window", "left")
        if self.config.getboolean("Window", "maximized"):
            kivy.core.window.Window.maximize()

        kivy.core.window.Window.bind(on_request_close=self.window_request_close)
        kivy.core.window.Window.bind(on_maximize=self.set_window_maximized_state)
        kivy.core.window.Window.bind(on_restore=self.set_window_restored_state)
        self.audio_chef_window = AudioChefWindow()
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

        self.update_ext(preset.ext)
        state.set_prop(consts.CURRENT_NAME_CHANGE_PARAMS, preset.name_change_parameters)
        self.audio_chef_window.update_name_changer_to_ui(preset.name_change_parameters)
        state.set_prop(consts.CURRENT_TRANSFORMATIONS, preset.transformations)
        self.audio_chef_window.update_transformations_to_ui(preset.transformations)
        # inspector.create_inspector(kivy.core.window.Window, audio_chef_window)
        return self.audio_chef_window

    def set_window_maximized_state(self, window):
        self.config.set("Window", "maximized", "true")

    def set_window_restored_state(self, window):
        self.config.set("Window", "maximized", "false")

    def window_request_close(self, *args, **kwargs):
        # Window.size is automatically adjusted for density, must divide by density when saving size
        logger.debug("Saving window config before exiting ...")
        self.config.set(
            "Window",
            "width",
            kivy.core.window.Window.size[0] / kivy.metrics.Metrics.density,
        )
        self.config.set(
            "Window",
            "height",
            kivy.core.window.Window.size[1] / kivy.metrics.Metrics.density,
        )
        self.config.set("Window", "top", kivy.core.window.Window.top)
        self.config.set("Window", "left", kivy.core.window.Window.left)
        # self.config.set('graphics', 'window_state', Window.ma)
        self.config.write()
        return False

    def build_config(self, config):
        kivy.Config.set("input", "mouse", "mouse,disable_multitouch")
        config.setdefaults(
            "Window",
            {"width": self.min_width, "height": self.min_height, "maximized": "false"},
        )

        for transformation_name, transformation in TRANSFORMATIONS.items():
            arguments_dict = {}
            for argument in transformation.arguments:
                if argument.type is float:
                    arguments_dict[f"{argument.name} max"] = argument.max
                    arguments_dict[f"{argument.name} min"] = argument.min
                    arguments_dict[f"{argument.name} step"] = argument.step
            config.setdefaults(transformation_name, arguments_dict)

    def get_application_config(self, defaultpath="%(appdir)s/%(appname)s.ini"):
        if kivy.platform == "macosx":  # mac will not write into app folder
            s = "~/.%(appname)s.ini"
        else:
            s = defaultpath
        return super().get_application_config(defaultpath=s)

    def build_settings(self, settings):
        for transformation_name, transformation in TRANSFORMATIONS.items():
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

    @staticmethod
    def update_transformations(new_transformations: list[Transformation]) -> None:
        preset: Preset = state.get_prop(CURRENT_PRESET)
        new_preset = dataclasses.replace(preset, transformations=new_transformations)
        state.set_prop(CURRENT_PRESET, new_preset)

    def update_ext(self, new_ext: str) -> None:
        state.set_prop(consts.CURRENT_EXT, new_ext)
        self.audio_chef_window.update_ext_to_ui(new_ext)

    def add_transform_item_click_handler(self):
        transformations: list[Transformation] = state.get_prop(
            consts.CURRENT_TRANSFORMATIONS
        )
        new_transformations = transformations + [Transformation(name=None, params={})]
        state.set_prop(consts.CURRENT_TRANSFORMATIONS, new_transformations)
        self.audio_chef_window.update_transformations_to_ui(new_transformations)

    def remove_transform_item(self, transform_index: int) -> None:
        transformations: list[Transformation] = state.get_prop(
            consts.CURRENT_TRANSFORMATIONS
        )
        new_transformations = (
            transformations[:transform_index] + transformations[transform_index + 1 :]
        )
        state.set_prop(consts.CURRENT_TRANSFORMATIONS, new_transformations)
        self.audio_chef_window.update_transformations_to_ui(new_transformations)

    def shift_up(self, index: int):
        transformations: list[Transformation] = state.get_prop(
            consts.CURRENT_TRANSFORMATIONS
        )
        new_transformations = self._move_transform(transformations, index, index + 1)
        state.set_prop(consts.CURRENT_TRANSFORMATIONS, new_transformations)
        self.audio_chef_window.update_transformations_to_ui(new_transformations)

    def shift_down(self, index: int):
        transformations: list[Transformation] = state.get_prop(
            consts.CURRENT_TRANSFORMATIONS
        )
        new_transformations = self._move_transform(
            transformations, index, max(index - 1, 0)
        )
        state.set_prop(consts.CURRENT_TRANSFORMATIONS, new_transformations)
        self.audio_chef_window.update_transformations_to_ui(new_transformations)

    @staticmethod
    def _move_transform(
        transformations: list[Transformation], from_index: int, to_index: int
    ) -> list[Transformation]:
        new_transformations = transformations[:]
        transform = new_transformations.pop(from_index)
        new_transformations.insert(to_index, transform)
        return new_transformations

    def select_transformation(self, index: int, transform_name: str) -> None:
        transformations: list[Transformation] = state.get_prop(
            consts.CURRENT_TRANSFORMATIONS
        )
        transform = transformations[index]
        if transform.name == transform_name:
            return
        new_transform = dataclasses.replace(transform, name=transform_name, params={})
        new_transformations = transformations[:]
        new_transformations[index] = new_transform
        state.set_prop(consts.CURRENT_TRANSFORMATIONS, new_transformations)
        self.audio_chef_window.update_transformations_to_ui(new_transformations)

    def update_transformation_params(self, index: int, params: dict):
        transformations: list[Transformation] = state.get_prop(
            consts.CURRENT_TRANSFORMATIONS
        )
        transform = transformations[index]
        if transform.params == params:
            return
        new_transform = dataclasses.replace(transform, params=params)
        new_transformations = transformations[:]
        new_transformations[index] = new_transform
        state.set_prop(consts.CURRENT_TRANSFORMATIONS, new_transformations)
        self.audio_chef_window.update_transformations_to_ui(new_transformations)

    def update_name_change_mode(self, new_mode: str):
        name_change_parameters: NameChangeParameters = state.get_prop(
            consts.CURRENT_NAME_CHANGE_PARAMS
        )
        new_name_change_parameters = dataclasses.replace(
            name_change_parameters, mode=new_mode
        )
        state.set_prop(consts.CURRENT_NAME_CHANGE_PARAMS, new_name_change_parameters)
        self.audio_chef_window.update_name_changer_to_ui(new_name_change_parameters)

    def update_name_change_replace_from_input(self, new_replace_from_input: str):
        name_change_parameters: NameChangeParameters = state.get_prop(
            consts.CURRENT_NAME_CHANGE_PARAMS
        )
        new_name_change_parameters = dataclasses.replace(
            name_change_parameters, replace_from_input=new_replace_from_input
        )
        state.set_prop(consts.CURRENT_NAME_CHANGE_PARAMS, new_name_change_parameters)
        self.audio_chef_window.update_name_changer_to_ui(new_name_change_parameters)

    def update_name_change_replace_to_input(self, new_replace_to_input: str):
        name_change_parameters: NameChangeParameters = state.get_prop(
            consts.CURRENT_NAME_CHANGE_PARAMS
        )
        new_name_change_parameters = dataclasses.replace(
            name_change_parameters, replace_to_input=new_replace_to_input
        )
        state.set_prop(consts.CURRENT_NAME_CHANGE_PARAMS, new_name_change_parameters)
        self.audio_chef_window.update_name_changer_to_ui(new_name_change_parameters)

    def update_name_change_wildcards_input(self, new_wildcards_input: str):
        name_change_parameters: NameChangeParameters = state.get_prop(
            consts.CURRENT_NAME_CHANGE_PARAMS
        )
        new_name_change_parameters = dataclasses.replace(
            name_change_parameters, wildcards_input=new_wildcards_input
        )
        state.set_prop(consts.CURRENT_NAME_CHANGE_PARAMS, new_name_change_parameters)
        self.audio_chef_window.update_name_changer_to_ui(new_name_change_parameters)


class CriticalExceptionHandler(kivy.base.ExceptionHandler):
    def handle_exception(self, inst):
        logger.exception("Unhandled Exception!", exc_info=True)
        ErrorPopup().open()
        return kivy.base.ExceptionManager.PASS


kivy.base.ExceptionManager.add_handler(CriticalExceptionHandler())

app = AudioChefApp()
