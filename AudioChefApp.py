import configparser
import json
import logging

from kivy import Config, platform
from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import Metrics
from kivy.uix.settings import SettingsWithSidebar

from components.AudioChefWindow import AudioChefWindow

from utils.Dispatcher import dispatcher
from utils.State import State, state
from utils.audio_formats import SUPPORTED_AUDIO_FORMATS, load_audio_formats
from utils.transformations import TRASNFORMATIONS

logger = logging.getLogger("audiochef")


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
