import os
import re

from kivy_helpers import toggle_widget

os.environ['PATH'] += ';' + os.path.join(os.getcwd(), 'windows', 'ffmpeg', 'bin')

import kivy
kivy.require('2.0.0')

import pydub
import asyncio
import traceback
import soundfile
from kivy.app import App
from datetime import datetime
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.accordion import AccordionItem
from kivy.properties import StringProperty, ObjectProperty, BooleanProperty
from pedalboard import Pedalboard
from transformations import TRASNFORMATIONS
from audio_formats import SUPPORTED_AUDIO_FORMATS


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


class OutputNameChanger(BoxLayout):
    wildcards = ['$item', '$date']
    mode = StringProperty()
    preview_callback = ObjectProperty()

    def change_name(self, old_name: str) -> str:
        if self.mode == 'wildcards':
            new_name = self.ids.wildcards_input.text
            new_name = new_name.replace('$item', old_name)
            new_name = new_name.replace('$date', str(datetime.today()))
            return new_name
        else:
            if self.ids.replace_from_input.text == '':
                return old_name
            return old_name.replace(self.ids.replace_from_input.text, self.ids.replace_to_input.text)

    def on_mode(self, instance, mode):
        self.switch_widgets()
        self.preview_callback()

    def switch_widgets(self):
        for widget_name in self.ids:
            hide = not widget_name.startswith(self.mode)
            toggle_widget(self.ids[widget_name], hide)


class ArgumentBox(ValidatedInput):
    type = ObjectProperty()

    def validate(self, text):
        self.type(text)


class TransformationForm(BoxLayout):
    remove_callback = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_transform = None

    def on_kv_post(self, base_widget):
        for transform_name in TRASNFORMATIONS:
            button = SelectableButton(text=transform_name)
            button.bind(on_release=self.select_transformation)
            self.ids.transform_box.add_widget(button)

    def select_transformation(self, transform_button: SelectableButton):
        transform_button.select()
        for button in self.ids.transform_box.children:
            if button != transform_button:
                button.unselect()

        self.selected_transform = (transform_button.text, TRASNFORMATIONS[transform_button.text].trasform)
        self.ids.args_box.clear_widgets()
        for arg in TRASNFORMATIONS[transform_button.text].arguments:
            if arg.options is not None:
                pass
            else:
                self.ids.args_box.add_widget(ArgumentBox(
                    type=arg.type, name=arg.name,
                    initial=str(arg.default) if arg.default is not None else arg.type(),
                    on_text=self.update_title
                ))
        self.update_title()

    def update_title(self):
        (transform_name, _), kwargs = self.get_selected_tranform()

    def get_selected_tranform(self):
        return self.selected_transform, {arg.name: arg.type(arg.text) for arg in self.ids.args_box.children}

    def remove(self):
        self.remove_callback(self)


class AudioChefWindow(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_dropfile=self.on_dropfile)
        self.selected_transformations = []
        self.selected_files = []
        self.file_widget_map = {}

        self.ids.ext_box.name = 'Choose the output format (empty means the same as the input if supported)'
        self.ids.ext_box.options = [''] + [format_.ext.lower() for format_ in SUPPORTED_AUDIO_FORMATS if format_.can_encode]

    def on_dropfile(self, window, filename: bytes):
        filename = filename.decode()
        if filename not in self.selected_files:
            self.selected_files.append(filename)
            file_label = Label(text=filename)
            self.ids.file_box.add_widget(file_label)

            preview_label = Label(text=self.get_output_filename(filename))
            self.ids.file_box.add_widget(preview_label)
            self.file_widget_map[filename] = (file_label, preview_label)

    def execute_recipe(self):
        self.clear_messages()
        try:
            self.check_input_file_formats()
            self.check_output_file_formats()
            self.check_selected_transformation()
            for filename in self.selected_files:
                name, ext = os.path.splitext(filename)
                outfile_name, outfile_ext = self.get_output_name(name), self.get_output_ext(ext)

                audio, sample_rate = self.get_audio_data(name, ext)

                board = self.prepare_board(sample_rate)
                res = board(audio)

                self.write_audio_data(outfile_name, outfile_ext, res, sample_rate)
        except UnexecutableRecipeError as e:
            self.add_message(str(e))
        except Exception:
            traceback.print_exc()

    def write_audio_data(self, outfile_name, outfile_ext, res, sample_rate):
        if outfile_ext[1:].upper() in soundfile.available_formats():
            with soundfile.SoundFile(outfile_name + outfile_ext, 'w',
                                     samplerate=sample_rate, channels=len(res.shape)) as f:
                f.write(res)
            return

        with soundfile.SoundFile(outfile_name + '.wav', 'w',
                                 samplerate=sample_rate, channels=len(res.shape)) as f:
            f.write(res)

        given_audio = pydub.AudioSegment.from_file(outfile_name + '.wav', format='wav')
        given_audio.export(outfile_name + outfile_ext, format=outfile_ext[1:])

    def check_input_file_formats(self):
        for filename in self.selected_files:
            name, ext = os.path.splitext(filename)
            if ext.upper()[1:] in soundfile.available_formats():
                return

            if ext.lower()[1:] not in [format_.ext.lower() for format_ in SUPPORTED_AUDIO_FORMATS if format_.can_decode]:
                raise UnexecutableRecipeError(f'"{filename}" is not in a supported format')

    def check_output_file_formats(self):
        if not self.ids.ext_box.validated:
            raise UnexecutableRecipeError(f'"{self.ids.ext_box.text}" is not a supported output format')

    def check_selected_transformation(self):
        if len(self.selected_transformations) == 0:
            raise UnexecutableRecipeError('You must choose a transformation to apply')

    def prepare_board(self, sample_rate):
        return Pedalboard(self.selected_transformations, sample_rate=sample_rate)

    def get_audio_data(self, name, ext):
        if ext[1:].upper() not in soundfile.available_formats():
            given_audio = pydub.AudioSegment.from_file(name + ext, format=ext[1:])
            given_audio.export(name + '.wav', format="wav")
            ext = '.wav'

        return soundfile.read(name + ext)

    def clear_messages(self):
        self.ids.messages_label.text = ''

    def add_message(self, message):
        self.ids.messages_label.text += '\n' + message

    def get_output_filename(self, filename):
        name, ext = os.path.splitext(filename)
        return self.get_output_name(name) + self.get_output_ext(ext)

    def get_output_name(self, name):
        path, filename = os.path.split(name)
        return os.path.join(path, self.ids.name_changer.change_name(filename))

    def get_output_ext(self, ext):
        return '.' + (self.ids.ext_box.text or ext[1:])

    def add_tranform_item(self):
        self.ids.transforms_box.add_widget(TransformationForm(remove_callback=self.remove_transformation))

    def remove_transformation(self, accordion_item):
        self.ids.transforms_box.remove_widget(accordion_item)

    def filename_preview(self):
        for filename in self.selected_files:
            self.file_widget_map[filename][1].text = self.get_output_filename(filename)


class AudioChefApp(App):
    def build(self):
        return AudioChefWindow()


if __name__ == "__main__":
    app = AudioChefApp()
    app.load_kv('audio_chef.kv')

    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.async_run(async_lib='asyncio'))
    loop.close()
