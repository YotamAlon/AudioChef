import os
import re

os.environ['PATH'] += ';' + os.path.join(os.getcwd(), 'windows', 'ffmpeg', 'bin')

import kivy
kivy.require('2.0.0')

import pydub
import asyncio
import traceback
import soundfile
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.dropdown import DropDown
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
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


class OutputNameChanger(GridLayout):
    mode = StringProperty()

    def change_name(self, old_name: str) -> str:
        if self.mode == 'regex':
            try:
                regex = re.compile(self.ids.from_.text)
            except Exception as e:
                raise UnexecutableRecipeError(str(e))

            def get_replacement(match):
                replacement = self.ids.to.text
                for i, group in enumerate(match.groups()):
                    replacement = replacement.replace(f'${i + 1}', group)
                return replacement

            return regex.sub(get_replacement, old_name)
        elif self.mode == 'replace':
            return old_name.replace(self.ids.from_.text, self.ids.to.text)
        else:
            return old_name + self.ids.to.text


class ArgumentBox(ValidatedInput):
    type = ObjectProperty()

    def validate(self, text):
        self.type(text)


class AudioChefWindow(BoxLayout):
    transformations = TRASNFORMATIONS

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_dropfile=self.on_dropfile)
        self.selected_transform = None
        self.selected_files = []

        for transform_name in self.transformations:
            button = SelectableButton(text=transform_name)
            button.bind(on_release=self.select_transformation)
            self.ids.transform_box.add_widget(button)

        self.ids.ext_box.name = 'Choose the output format (empty means the same as the input if supported)'
        self.ids.ext_box.options = [''] + [format_.ext.lower() for format_ in SUPPORTED_AUDIO_FORMATS if format_.can_encode]

    def on_dropfile(self, window, filename: bytes):
        filename = filename.decode()
        if filename not in self.selected_files:
            self.selected_files.append(filename)
            self.ids.file_box.add_widget(Label(text=filename))

    def select_transformation(self, transform_button: SelectableButton):
        transform_button.select()
        for button in self.ids.transform_box.children:
            if button != transform_button:
                button.unselect()
        self.selected_transform = self.transformations[transform_button.text].trasform
        self.ids.args_box.clear_widgets()
        for arg in self.transformations[transform_button.text].arguments:
            if arg.options is not None:
                pass
            else:
                self.ids.args_box.add_widget(ArgumentBox(
                    type=arg.type, name=arg.name,
                    text=str(arg.default) if arg.default is not None else arg.type()))

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
        if self.selected_transform is None:
            raise UnexecutableRecipeError('You must choose a transformation to apply')

    def prepare_board(self, sample_rate):
        kwargs = {arg.name: arg.type(arg.text) for arg in self.ids.args_box.children}
        return Pedalboard([self.selected_transform(**kwargs)], sample_rate=sample_rate)

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

    def get_output_name(self, name):
        path, filename = os.path.split(name)
        return os.path.join(path, self.ids.name_changer.change_name(filename))

    def get_output_ext(self, ext):
        return '.' + self.ids.ext_box.text or ext


class AudioChefApp(App):
    def build(self):
        return AudioChefWindow()


if __name__ == "__main__":
    app = AudioChefApp()
    app.load_kv('audio_chef.kv')

    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.async_run(async_lib='asyncio'))
    loop.close()
