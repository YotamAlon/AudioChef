import os
os.environ['PATH'] += ';' + os.path.join(os.getcwd(), 'windows', 'ffmpeg', 'bin')

import kivy
kivy.require('2.0.0')

import pydub
import asyncio
import soundfile
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ObjectProperty
from pedalboard import Pedalboard
from transformations import TRASNFORMATIONS
from audio_formats import SUPPORTED_AUDIO_FORMATS


class SelectableButton(Button):
    def select(self):
        self.color = 'black'
        self.background_color = 'white'

    def unselect(self):
        self.color = 'white'
        self.background_color = 'grey'


class ArgumentBox(BoxLayout):
    name = StringProperty()
    text = StringProperty()
    type = ObjectProperty()

    def on_text(self, instance, pos):
        try:
            self.type(self.text)
            self.mark_good_value()
        except ValueError:
            self.mark_bad_value()

    def mark_good_value(self):
        text_input = self.ids.get('text_input')
        if text_input is not None:
            text_input.background_color = 'white'

    def mark_bad_value(self):
        text_input = self.ids.get('text_input')
        if text_input is not None:
            text_input.background_color = 'lightsalmon'


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

        for format in SUPPORTED_AUDIO_FORMATS:
            if format.can_encode:
                button = Button(text=f'{format.ext} ({format.description})')
                self.ids.ext_dropdown.add_widget(button)

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
        for filename in self.selected_files:
            output_file_name, (audio, sample_rate) = self.get_audio_data(filename)
            board = self.prepare_board(sample_rate)
            res = board(audio)

            with soundfile.SoundFile(output_file_name, 'w', samplerate=sample_rate, channels=len(res.shape)) as f:
                f.write(res)

    def prepare_board(self, sample_rate):
        kwargs = {arg.name: arg.type(arg.text) for arg in self.ids.args_box.children}
        return Pedalboard([self.selected_transform(**kwargs)], sample_rate=sample_rate)

    def get_audio_data(self, filename):
        name, ext = os.path.splitext(filename)

        if ext[1:].upper() not in soundfile.available_formats():
            given_audio = pydub.AudioSegment.from_file(name + ext, format=ext[1:])
            given_audio.export(name + '.wav', format="wav")
            ext = '.wav'

        output = name + '-output' + ext
        return output, soundfile.read(name + ext)


class AudioChefApp(App):
    def build(self):
        return AudioChefWindow()


if __name__ == "__main__":
    app = AudioChefApp()
    app.load_kv('audio_chef.kv')

    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.async_run(async_lib='asyncio'))
    loop.close()
