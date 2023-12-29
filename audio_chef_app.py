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

from components.audio_chef_window import AudioChefWindow
from components.error_popup import ErrorPopup
from consts import CURRENT_PRESET
from models import db_proxy
from models.preset import NameChangeParameters
from repository import PresetModel
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
        return AudioChefWindow()

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
    def update_name_change_parameters(
        new_name_change_parameters: NameChangeParameters,
    ) -> None:
        preset = state.get_prop(CURRENT_PRESET)
        new_preset = dataclasses.replace(
            preset, name_change_parameters=new_name_change_parameters
        )
        state.set_prop(CURRENT_PRESET, new_preset)


class CriticalExceptionHandler(kivy.base.ExceptionHandler):
    def handle_exception(self, inst):
        logger.exception("Unhandled Exception!", exc_info=True)
        ErrorPopup().open()
        return kivy.base.ExceptionManager.PASS


kivy.base.ExceptionManager.add_handler(CriticalExceptionHandler())

app = AudioChefApp()
