import abc
import logging
import os
import typing

import kivy.properties  # type: ignore
import kivy.uix.boxlayout  # type: ignore
import kivy.uix.button  # type: ignore
import kivy.uix.dropdown  # type: ignore
from kivy.uix.popup import Popup

logger = logging.getLogger("audiochef")


class UnexecutableRecipeError(Exception):
    pass


class SelectableButton(kivy.uix.button.Button):
    selected = kivy.properties.BooleanProperty()

    def select(self):
        self.color = "black"
        self.background_color = "white"

    def unselect(self):
        self.color = "white"
        self.background_color = "grey"


class ValidatedInput(kivy.uix.boxlayout.BoxLayout):
    name = kivy.properties.StringProperty()
    text = kivy.properties.StringProperty()
    validated = kivy.properties.BooleanProperty()
    initial = kivy.properties.StringProperty()

    def on_kv_post(self, base_widget):
        self.text = self.initial

    def on_text(self, instance, pos):
        try:
            if self.validate(self.text) is False:
                self.validated = False
                return
            self.validated = True
        except ValueError:
            self.validated = False

    @abc.abstractmethod
    def validate(self, text: str) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def get_value(self):
        raise NotImplementedError

    def on_validated(self, _, value):
        text_input = self.ids.get("text_input")
        if not text_input:
            return

        if value:
            text_input.background_color = "white"
        else:
            text_input.background_color = "lightsalmon"


class OptionsBox(ValidatedInput):
    options: typing.List[str] = kivy.properties.ListProperty()

    def __init__(self, **kwargs):
        self.dropdown = kivy.uix.dropdown.DropDown()
        super().__init__(**kwargs)

    def on_kv_post(self, _) -> None:
        for option in self.options:
            self.dropdown.add_widget(self.create_option_button(option))

        self.dropdown.bind(
            on_select=lambda _, selected_option: setattr(self, "text", selected_option)
        )
        self.ids.text_input.bind(
            focus=lambda _, v: self.dropdown.open(self.ids.text_input)
            if v
            else self.dropdown.dismiss()
        )

    def on_text(self, instance, pos):
        super().on_text(instance, pos)
        self.update_dropdown_options()

    def update_dropdown_options(self):
        self.dropdown.clear_widgets()
        for option in self.options:
            if self.text in option:
                self.dropdown.add_widget(self.create_option_button(option))

    def create_option_button(self, option: str):
        option_button = kivy.uix.button.Button(text=option, size_hint_y=None, height=44)
        option_button.bind(on_release=lambda _: self.dropdown.select(option))
        return option_button

    def validate(self, text: str) -> bool:
        return text.lower() in self.options

    def get_value(self) -> str:
        return self.text


class FileArgumentBox(ValidatedInput):
    def validate(self, text: str) -> bool:
        return os.path.exists(text)

    def get_value(self) -> str:
        return self.text


class FloatArgumentBox(ValidatedInput):
    transformation_name = kivy.properties.StringProperty()
    min = kivy.properties.NumericProperty()
    max = kivy.properties.NumericProperty()
    step = kivy.properties.NumericProperty()

    def validate(self, text: str) -> bool:
        try:
            float(text)
            return True
        except ValueError:
            return False

    def get_value(self) -> float:
        return float(self.text)


class PresetButton(kivy.uix.boxlayout.BoxLayout):
    preset_id = kivy.properties.NumericProperty()
    preset_name = kivy.properties.ObjectProperty()
    default = kivy.properties.BooleanProperty()
    load_preset = kivy.properties.ObjectProperty()
    rename_preset = kivy.properties.ObjectProperty()
    remove_preset = kivy.properties.ObjectProperty()
    make_default = kivy.properties.ObjectProperty()


class NoticePopup(Popup):
    text = kivy.properties.StringProperty()
