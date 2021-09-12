import os
import kivy
kivy.require('2.0.0')
import pydub
import asyncio
import soundfile
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.dropdown import DropDown
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from pedalboard import Pedalboard, Convolution, Compressor, Chorus, Distortion, Gain, HighpassFilter, LadderFilter, \
    Limiter, LowpassFilter, Phaser, Reverb


class SelectableButton(Button):
    def select(self):
        self.color = 'black'
        self.background_color = 'white'

    def unselect(self):
        self.color = 'white'
        self.background_color = 'grey'


class AudioChefWindow(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_dropfile=self.on_dropfile)
        self.transformations = {transform.__name__: transform for transform in [
            Convolution, Compressor, Chorus, Distortion, Gain, HighpassFilter, LadderFilter, Limiter, LowpassFilter,
            Phaser, Reverb]}
        self.selected_transform = None
        self.selected_files = []

        for transform_name in self.transformations:
            button = SelectableButton(text=transform_name)
            button.bind(on_release=self.select_transformation)
            self.ids.transform_box.add_widget(button)

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
        self.selected_transform = self.transformations[transform_button.text]

    def execute_recipe(self):
        for filename in self.selected_files:
            output_file_name, (audio, sample_rate) = self.get_audio_data(filename)
            board = self.prepare_board(sample_rate)
            res = board(audio)

            with soundfile.SoundFile(output_file_name, 'w', samplerate=sample_rate, channels=len(res.shape)) as f:
                f.write(res)

    def prepare_board(self, sample_rate):
        return Pedalboard([self.selected_transform()], sample_rate=sample_rate)

    def get_audio_data(self, filename):
        name, ext = os.path.splitext(filename)

        if ext[1:].upper() not in soundfile.available_formats():
            os.environ['PATH'] += ';' + os.path.join(os.getcwd(), 'windows', 'ffmpeg', 'bin')
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
