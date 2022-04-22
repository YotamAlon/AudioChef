import json
import os
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import (
    StringProperty,
    BooleanProperty,
    ObjectProperty,
    NumericProperty,
)


class UnexecutableRecipeError(Exception):
    pass


class FileLabel(Label):
    pass


class SelectableButton(Button):
    selected = BooleanProperty()

    def select(self):
        self.color = "black"
        self.background_color = "white"

    def unselect(self):
        self.color = "white"
        self.background_color = "grey"


class ValidatedInput(BoxLayout):
    name = StringProperty()
    text = StringProperty()
    validated = BooleanProperty()
    initial = StringProperty()

    def on_text(self, instance, pos):
        try:
            if self.validate(self.text) is False:
                self.validated = False
                return
            self.validated = True
        except ValueError:
            self.validated = False

    def validate(self, text):
        raise NotImplementedError()

    def on_validated(self, instance, value):
        text_input = self.ids.get("text_input")
        if not text_input:
            return

        if value:
            text_input.background_color = "white"
        else:
            text_input.background_color = "lightsalmon"


class OptionsBox(ValidatedInput):
    options = ObjectProperty()

    def validate(self, text):
        return text.lower() in self.options


class ArgumentBox(ValidatedInput):
    type = ObjectProperty()
    min = NumericProperty()
    max = NumericProperty()
    step = NumericProperty()

    def on_kv_post(self, base_widget):
        self.text = self.initial

    def validate(self, text):
        self.type(text)


class ConfigurationFile:
    filename = os.path.join(os.getcwd(), "configuration.db")

    def get_configuration(self) -> dict:
        with open(self.filename, "r") as f:
            return json.load(f)

    def set_configuration(self, configuration: dict) -> None:
        with open(self.filename, "w") as f:
            json.dump(configuration, f, indent=4)

    def save_preset(self, preset: dict) -> None:
        presets_list = self.get_presets()
        if "order" not in preset:
            preset["order"] = len(presets_list)
        presets_list.append(preset)
        self.set_presets(presets_list)

    def get_presets(self) -> list:
        return self.get_configuration()["presets"]

    def get_preset(self, id_: int) -> dict:
        presets = self.get_presets()
        return presets[id_] if len(presets) > id_ else None

    def get_preset_by_name(self, name: str) -> dict:
        presets = self.get_presets()
        return next((preset for preset in presets if preset["name"] == name), None)

    def set_presets(self, presets: list) -> None:
        configuration = self.get_configuration()
        configuration["presets"] = presets
        self.set_configuration(configuration)

    def remove_preset(self, name: str) -> None:
        presets = self.get_presets()
        preset = next((preset for preset in presets if preset["name"] == name), None)
        presets.remove(preset)
        self.set_presets(presets)

    def rename_preset(self, name: str, new_name: str) -> None:
        presets = self.get_presets()
        for preset in presets:
            if preset["name"] == name:
                preset["name"] = new_name
                break

        self.set_presets(presets)

    def initialize(self, TRASNFORMATIONS: dict) -> None:
        if not os.path.exists(self.filename):
            defaults = {}
            for transformation_name, transformation in TRASNFORMATIONS.items():
                arguments_dict = {}
                for argument in transformation.arguments:
                    if argument.type is float:
                        arguments_dict[argument.name] = {
                            "max": argument.max,
                            "min": argument.min,
                            "step": argument.step,
                        }
                if len(arguments_dict) != 0:
                    defaults[transformation_name] = arguments_dict

            self.set_configuration({"defaults": defaults, "presets": []})


class PresetButton(BoxLayout):
    preset_id = NumericProperty()
    preset_name = ObjectProperty()
    default = BooleanProperty()
    load_preset = ObjectProperty()
    rename_preset = ObjectProperty()
    remove_preset = ObjectProperty()
    make_default = ObjectProperty()
