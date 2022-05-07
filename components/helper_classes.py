import json
import os
import logging
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.dropdown import DropDown
from kivy.properties import (
    StringProperty,
    BooleanProperty,
    ObjectProperty,
    NumericProperty, ListProperty
)

logger = logging.getLogger("audiochef")


class UnexecutableRecipeError(Exception):
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
    options = ListProperty()

    def __init__(self, **kwargs):
        self.dropdown = DropDown()
        super().__init__(**kwargs)

    def on_kv_post(self, base_widget):
        for option in self.options:
            logger.debug(f'Adding option {option} to dropdown')
            self.dropdown.add_widget(self.create_option_button(option))

        self.dropdown.bind(on_select=lambda _, option: setattr(self, 'text', option))
        self.ids.text_input.bind(focus=lambda _, v: self.dropdown.open(self.ids.text_input) if v else self.dropdown.dismiss())

    def on_text(self, instance, pos):
        super().on_text(instance, pos)
        self.update_dropdown_options()

    def update_dropdown_options(self):
        self.dropdown.clear_widgets()
        for option in self.options:
            if self.text in option:
                logger.debug(f'Adding option {option} to dropdown')
                self.dropdown.add_widget(self.create_option_button(option))

    def create_option_button(self, option):
        option_button = Button(text=option, size_hint_y=None, height=44)
        option_button.bind(on_release=lambda _: self.dropdown.select(option))
        return option_button

    def validate(self, text):
        return text.lower() in self.options


class FileArgumentBox(ValidatedInput):
    def validate(self, text):
        return os.path.exists(text)


class FloatArgumentBox(ValidatedInput):
    transformation_name = StringProperty()
    min = NumericProperty()
    max = NumericProperty()
    step = NumericProperty()

    def validate(self, text):
        try:
            float(text)
            return True
        except ValueError:
            return False


class PresetButton(BoxLayout):
    preset_id = NumericProperty()
    preset_name = ObjectProperty()
    default = BooleanProperty()
    load_preset = ObjectProperty()
    rename_preset = ObjectProperty()
    remove_preset = ObjectProperty()
    make_default = ObjectProperty()
