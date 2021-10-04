import json
import os
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty


class UnexecutableRecipeError(Exception): pass


class FileLabel(Label): pass


class SelectableButton(Button):
    def select(self):
        self.color = 'black'
        self.background_color = 'white'

    def unselect(self):
        self.color = 'white'
        self.background_color = 'grey'


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
        text_input = self.ids.get('text_input')
        if not text_input:
            return

        if value:
            text_input.background_color = 'white'
        else:
            text_input.background_color = 'lightsalmon'


class OptionsBox(ValidatedInput):
    options = ObjectProperty()

    def validate(self, text):
        return text.lower() in self.options


class ArgumentBox(ValidatedInput):
    type = ObjectProperty()

    def on_kv_post(self, base_widget):
        self.text = self.initial

    def validate(self, text):
        self.type(text)


class PresetsFile:
    filename = os.path.join(os.getcwd(), 'presets.db')

    def save_preset(self, preset):
        presets_list = self.get_presets()
        presets_list.append(preset)
        self.set_presets(presets_list)

    def get_presets(self):
        if not os.path.exists(self.filename):
            with open(self.filename, 'w') as f:
                json.dump([], f)

        with open(self.filename, 'r') as f:
            return json.load(f)

    def set_presets(self, presets):
        with open(self.filename, 'w') as f:
            json.dump(presets, f, indent=4)

    def remove_preset(self, i):
        presets = self.get_presets()
        presets.pop(i)
        self.set_presets(presets)


class PresetButton(BoxLayout):
    preset_id = ObjectProperty()
    default = BooleanProperty()
    text = StringProperty()
    load_preset = ObjectProperty()
    remove_preset = ObjectProperty()
    make_default = ObjectProperty()
