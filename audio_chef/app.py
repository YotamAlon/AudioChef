import configparser
import dataclasses
import json
import logging
import pathlib

import kivy
import kivy.app
import kivy.base
import kivy.core.window
import kivy.metrics
import kivy.uix.settings
from kivy.modules import inspector
from kivy.uix.label import Label
from kivy.uix.popup import Popup

from audio_chef.adapters.audio_client import AudioClient
from audio_chef.adapters.repository import (
    PresetRepository,
    PluginRepository,
    initialize_db,
)
from audio_chef.components.audio_chef_window import AudioChefWindow
from audio_chef.components.error_popup import ErrorPopup
from audio_chef.components.helper_classes import NoticePopup
from audio_chef.components.plugin_popup import PluginPopup
from audio_chef.models.preset import (
    NameChangeParameters,
    Transformation,
    Preset,
    NameChangeMode,
)

from audio_chef.utils.audio_formats import (
    SUPPORTED_AUDIO_FORMATS,
    load_audio_formats,
    AudioFile,
    NoCompatibleAudioFormatException,
)
from audio_chef.utils.transformations import TRANSFORMATIONS

logger = logging.getLogger("audiochef")


class AppState:
    ext: str = ""
    ext_locked: bool = False
    name_change_params: NameChangeParameters = NameChangeParameters(
        mode=NameChangeMode.REPLACE,
        wildcards_input="",
        replace_from_input="",
        replace_to_input="",
    )
    name_change_locked: bool = False
    transformations: list[Transformation] = []
    transformations_locked: bool = False
    available_transformations: list[Transformation] = []
    selected_files: list[AudioFile] = []


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
    min_width = 1280
    min_height = 720
    supported_audio_formats = SUPPORTED_AUDIO_FORMATS
    audio_chef_window: AudioChefWindow
    ffmpeg_path: pathlib.Path = pathlib.Path(__file__).parent

    def __init__(self):
        logger.setLevel(self.log_level)
        super().__init__()

    def on_kv_post(self, base_widget):
        kivy.core.window.Window.bind(on_drop_file=self.add_file)

    def add_file(self, window, filename: bytes, x, y):
        filename = filename.decode()
        try:
            audio_file = AudioFile(filename)
        except NoCompatibleAudioFormatException:
            logger.error(f"Unable to find audio format for {filename}")
            Popup(
                title="Unsupported file format!",
                content=Label(
                    text=f"The file '{filename}' you just tried to add\n"
                    f"is encoded in an audio format which is not currently suported.\n"
                    f"If you think this is a mistake, please send me your audio_chef.log\n"
                    f"file along with this audio file."
                ),
                size_hint=(0.5, 0.5),
            ).open()
            return

        AppState.selected_files.append(audio_file)
        self.audio_chef_window.update_files_to_ui(AppState.selected_files)

    def build(self):
        logger.info("Loading KV file ...")
        self.kv_directory = str(pathlib.Path(__file__).parent.parent / "kv")
        self.load_kv(str(pathlib.Path(__file__).parent.parent / "kv" / "audio_chef.kv"))

        logger.info("Loading audio formats ...")
        load_audio_formats(self.ffmpeg_path)

        logger.info("Initializing database ...")
        initialize_db("presets.db")

        logger.debug("Binding dropfile event ...")
        kivy.core.window.Window.clearcolor = self.window_background_color
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
        preset = self._get_default_preset()

        self._load_preset(preset)

        AppState.available_transformations = self._get_available_transformations()
        self.audio_chef_window.update_available_transformations_to_ui(
            AppState.available_transformations
        )
        inspector.create_inspector(kivy.core.window.Window, self.audio_chef_window)
        return self.audio_chef_window

    def _get_default_preset(self) -> Preset:
        default_preset = PresetRepository.get_default()
        if default_preset:
            preset = default_preset
        else:
            preset = Preset(
                ext="",
                transformations=[],
                name_change_parameters=NameChangeParameters(
                    mode=NameChangeMode.REPLACE,
                    wildcards_input="",
                    replace_from_input="",
                    replace_to_input="",
                ),
            )
        return preset

    def _get_available_transformations(self) -> list[Transformation]:
        return PluginRepository.get_available_transformations()

    def _save_plugin(self, plugin_path: str) -> None:
        PluginRepository.save_plugin(plugin_path)

    def _get_preset_by_id(self, preset_id: int) -> Preset:
        return PresetRepository.get_by_id(preset_id)

    def load_preset(self, preset_id: int) -> None:
        preset = self._get_preset_by_id(preset_id)
        self._load_preset(preset)

    @staticmethod
    def _load_preset(preset: Preset) -> None:
        if not AppState.ext_locked:
            AppState.ext = preset.ext
        if not AppState.name_change_locked:
            AppState.name_change_params = preset.name_change_parameters
        if not AppState.transformations_locked:
            AppState.transformations = preset.transformations

    def save_preset(self):
        current_preset = self._make_preset()
        if current_preset:
            preset_metadata = PresetRepository.save_preset(current_preset)
            self.audio_chef_window.add_preset_button(preset_metadata)

    def execute_preset(self) -> None:
        preset = self._make_preset()
        if not preset:
            return

        success = AudioClient.execute_preset(
            preset.ext, AppState.selected_files, preset.transformations
        )
        if not success:
            Popup(
                title="I Encountered an Error!",
                content=Label(
                    text="I wrote all the info for the developer in a log file.\n"
                    "Check the folder with AudioChef it in."
                ),
            )

    @staticmethod
    def _make_preset() -> Preset:
        return Preset(
            ext=AppState.ext,
            transformations=AppState.transformations,
            name_change_parameters=AppState.name_change_params,
        )

    @staticmethod
    def open_plugin_selector():
        PluginPopup().open()

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

    def update_ext(self, new_ext: str) -> None:
        AppState.ext = new_ext
        self.audio_chef_window.update_ext_to_ui(AppState.ext)

    def add_transform_item_click_handler(self) -> None:
        AppState.transformations += [Transformation(name=None, params={})]
        self.audio_chef_window.update_transformations_to_ui(AppState.transformations)

    def remove_transform_item(self, transform_index: int) -> None:
        transformations = AppState.transformations
        AppState.transformations = (
            transformations[:transform_index] + transformations[transform_index + 1 :]
        )
        self.audio_chef_window.update_transformations_to_ui(AppState.transformations)

    def shift_up(self, index: int) -> None:
        AppState.transformations = self._move_transform(
            AppState.transformations, index, index + 1
        )
        self.audio_chef_window.update_transformations_to_ui(AppState.transformations)

    def shift_down(self, index: int) -> None:
        AppState.transformations = self._move_transform(
            AppState.transformations, index, max(index - 1, 0)
        )
        self.audio_chef_window.update_transformations_to_ui(AppState.transformations)

    @staticmethod
    def _move_transform(
        transformations: list[Transformation], from_index: int, to_index: int
    ) -> list[Transformation]:
        new_transformations = transformations[:]
        transform = new_transformations.pop(from_index)
        new_transformations.insert(to_index, transform)
        return new_transformations

    def select_transformation(self, index: int, transform_name: str) -> None:
        transform = AppState.transformations[index]
        if transform.name == transform_name:
            return
        new_transform = dataclasses.replace(transform, name=transform_name, params={})
        new_transformations = AppState.transformations[:]
        new_transformations[index] = new_transform
        AppState.transformations = new_transformations
        self.audio_chef_window.update_transformations_to_ui(AppState.transformations)

    def update_transformation_params(self, index: int, params: dict) -> None:
        transform = AppState.transformations[index]
        if transform.params == params:
            return
        new_transform = dataclasses.replace(transform, params=params)
        new_transformations = AppState.transformations[:]
        new_transformations[index] = new_transform
        AppState.transformations = new_transformations
        self.audio_chef_window.update_transformations_to_ui(AppState.transformations)

    def update_name_change_mode(self, new_mode: NameChangeMode) -> None:
        AppState.name_change_params = dataclasses.replace(
            AppState.name_change_params, mode=new_mode
        )
        self.audio_chef_window.update_name_changer_to_ui(AppState.name_change_params)

    def update_name_change_replace_from_input(
        self, new_replace_from_input: str
    ) -> None:
        AppState.name_change_params = dataclasses.replace(
            AppState.name_change_params, replace_from_input=new_replace_from_input
        )
        self.audio_chef_window.update_name_changer_to_ui(AppState.name_change_params)

    def update_name_change_replace_to_input(self, new_replace_to_input: str) -> None:
        AppState.name_change_params = dataclasses.replace(
            AppState.name_change_params, replace_to_input=new_replace_to_input
        )
        self.audio_chef_window.update_name_changer_to_ui(AppState.name_change_params)

    def update_name_change_wildcards_input(self, new_wildcards_input: str) -> None:
        AppState.name_change_params = dataclasses.replace(
            AppState.name_change_params, wildcards_input=new_wildcards_input
        )
        self.audio_chef_window.update_name_changer_to_ui(AppState.name_change_params)

    def clear_files(self, *args, **kwargs):
        AppState.selected_files = []
        self.audio_chef_window.update_files_to_ui(AppState.selected_files)

    def lock_ext(self, lock_status: bool):
        AppState.ext_locked = lock_status

    def lock_name_changer(self, lock_status: bool):
        AppState.name_change_locked = lock_status

    def lock_transformations(self, lock_status: bool):
        AppState.transformations_locked = lock_status

    def load_plugin(self, path: str, selection: list[str]) -> bool:
        if path.lower().endswith(".vst3"):
            vst3_file = path
        elif selection and selection[0].lower().endswith(".vst3"):
            vst3_file = selection[0]
        else:
            NoticePopup(
                title="You have not selected a valid plugin!",
                text="Please try again - the file/folder must be a valid vst3 plugin",
            ).open()
            return False

        self._save_plugin(vst3_file)
        AppState.available_transformations = self._get_available_transformations()
        self.audio_chef_window.update_available_transformations_to_ui(
            AppState.available_transformations
        )
        return True


class CriticalExceptionHandler(kivy.base.ExceptionHandler):
    def handle_exception(self, inst):
        logger.exception("Unhandled Exception!", exc_info=True)
        ErrorPopup().open()
        return kivy.base.ExceptionManager.PASS


kivy.base.ExceptionManager.add_handler(CriticalExceptionHandler())
