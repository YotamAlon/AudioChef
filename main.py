import os
os.environ['PATH'] += ';' + os.path.join(os.getcwd(), 'windows', 'ffmpeg', 'bin')

import kivy
kivy.require('2.0.0')

import pydub
import asyncio
import logging
import traceback
import soundfile
from kivy.app import App
from datetime import datetime
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy_helpers import toggle_widget
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ObjectProperty
from pedalboard import Pedalboard
from transformations import TRASNFORMATIONS
from audio_formats import SUPPORTED_AUDIO_FORMATS
from helper_classes import UnexecutableRecipeError, SelectableButton, ArgumentBox, PresetsFile, OptionsBox

logger = logging.getLogger('audiochef')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class OutputChanger(BoxLayout):
    wildcards = ['$item', '$date']
    mode = StringProperty('replace')
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

    def get_state(self):
        return {'mode': self.mode, 'wildcards_input': self.ids.wildcards_input.text,
                'replace_from_input': self.ids.replace_from_input.text,
                'replace_to_input': self.ids.replace_to_input.text}

    def load_state(self, state):
        logger.debug(f'OutputChanger: loading state {state}')
        self.mode = state['mode']
        self.ids.wildcards_input.text = state['wildcards_input']
        self.ids.replace_from_input.text = state['replace_from_input']
        self.ids.replace_to_input.text = state['replace_to_input']


class TransformationForm(BoxLayout):
    remove_callback = ObjectProperty()
    transformations = TRASNFORMATIONS.keys()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_transform = None

    def select_transformation(self, transform_name):
        self.selected_transform = self.get_transform_name_and_object(transform_name)
        self.ids.args_box.clear_widgets()
        self.load_argument_boxes(TRASNFORMATIONS[self.selected_transform[0]])
        self.update_title()

    def select_button_for(self, transform_name):
        for button in self.ids.transform_box.children:
            if button.text == transform_name:
                button.select()

    def get_transform_name_and_object(self, transform_name):
        return (transform_name, TRASNFORMATIONS[transform_name].trasform)

    def load_argument_boxes(self, transform):
        for arg in transform.arguments:
            if arg.options is not None:
                pass
            else:
                logger.debug(f'TransformationForm ({id(self)}): adding ArgumentBox(type={arg.type}, name={arg.name}, '
                             f'text={str(arg.default) if arg.default is not None else arg.type()}')
                self.ids.args_box.add_widget(ArgumentBox(
                    type=arg.type, name=arg.name,
                    initial=str(arg.default) if arg.default is not None else arg.type(),
                    on_text=self.update_title
                ))

    def update_title(self):
        (transform_name, _), kwargs = self.get_selected_tranform()

    def get_selected_tranform(self):
        if self.selected_transform is None:
            return None
        return self.selected_transform, self.get_args_dict()

    def get_args_dict(self):
        return {arg.name: arg.type(arg.text) for arg in self.ids.args_box.children}

    def load_args_dict(self, args_dict):
        for arg in self.ids.args_box.children:
            arg.text = str(args_dict[arg.name])

    def remove(self):
        self.remove_callback(self)

    def get_state(self):
        if self.selected_transform is None:
            return None
        return {'transform_name': self.selected_transform[0], 'args': self.get_args_dict()}

    def load_state(self, state):
        logger.debug(f'TransformationForm ({id(self)}): loading state {state}')
        if state is None:
            return

        self.selected_transform = self.get_transform_name_and_object(state['transform_name'])
        self.select_button_for(state['transform_name'])
        self.load_argument_boxes(TRASNFORMATIONS[self.selected_transform[0]])
        self.load_args_dict(state['args'])


class AudioChefWindow(BoxLayout):
    name_changer: OutputChanger = ObjectProperty()
    ext_box: OptionsBox = ObjectProperty()
    transforms_box: Widget = ObjectProperty()
    presets_box: Widget = ObjectProperty()
    file_box: Widget = ObjectProperty()

    def __init__(self, **kwargs):
        self.presets_file = PresetsFile()
        super().__init__(**kwargs)
        Window.bind(on_dropfile=self.on_dropfile)
        self.selected_transformations = []
        self.selected_files = []
        self.file_widget_map = {}

        self.ext_box.name = 'Choose the output format (empty means the same as the input if supported)'
        self.ext_box.options = [''] + [format_.ext.lower() for format_ in SUPPORTED_AUDIO_FORMATS if format_.can_encode]

    def on_kv_post(self, base_widget):
        presets = self.presets_file.get_presets()
        for i, preset in enumerate(presets):
            self.presets_box.add_widget(Button(text=f'{i}', on_release=lambda x: self.load_preset(i)))

    def on_dropfile(self, window, filename: bytes):
        filename = filename.decode()
        if filename not in self.selected_files:
            self.selected_files.append(filename)
            file_label = Label(text=filename)
            self.file_box.add_widget(file_label)

            preview_label = Label(text=self.get_output_filename(filename))
            self.file_box.add_widget(preview_label)
            self.file_widget_map[filename] = (file_label, preview_label)

    def execute_preset(self):
        self.clear_messages()
        try:
            self.check_input_file_formats()
            self.check_output_file_formats()

            transformations = self.get_transformations()
            self.check_selected_transformation(transformations)
            for filename in self.selected_files:
                name, ext = os.path.splitext(filename)
                outfile_name, outfile_ext = self.get_output_name(name), self.get_output_ext(ext)

                audio, sample_rate = self.get_audio_data(name, ext)

                board = self.prepare_board(sample_rate, transformations)
                res = board(audio)

                self.write_audio_data(outfile_name, outfile_ext, res, sample_rate)
        except UnexecutableRecipeError as e:
            self.add_message(str(e))
        except Exception:
            traceback.print_exc()

    def save_preset(self):
        preset = {'ext': self.ext_box.text,
                  'transformations': [child.get_state() for child in self.transforms_box.children[::-1]],
                  'name_changer': self.name_changer.get_state()}
        self.presets_file.save_preset(preset)

    def load_preset(self, i):
        logger.debug(f'AudioChefWindow: loading preset {i}')
        preset = self.presets_file.get_presets()[i]
        logger.debug(f'AudioChefWindow: preset {i} - {preset}')
        self.ext_box.text = preset['ext']
        self.transforms_box.clear_widgets()
        for transform_state in preset['transformations']:
            self.add_tranform_item()
            logger.debug(self.transforms_box.children)
            self.transforms_box.children[0].load_state(transform_state)
        self.name_changer.load_state(preset['name_changer'])

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
        if not self.ext_box.validated:
            raise UnexecutableRecipeError(f'"{self.ext_box.text}" is not a supported output format')

    def get_transformations(self):
        return [child.get_selected_tranform() for child in self.transforms_box.children]

    def check_selected_transformation(self, transformations):
        if len(transformations) == 0 or any(transform is None for transform in transformations):
            raise UnexecutableRecipeError('You must choose a transformation to apply')

    def prepare_board(self, sample_rate, transformations):
        return Pedalboard([transform(**kwargs) for (_, transform), kwargs in transformations], sample_rate=sample_rate)

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
        return os.path.join(path, self.name_changer.change_name(filename))

    def get_output_ext(self, ext):
        return '.' + (self.ext_box.text or ext[1:])

    def add_tranform_item(self):
        self.transforms_box.add_widget(TransformationForm(remove_callback=self.remove_transformation))

    def remove_transformation(self, accordion_item):
        self.transforms_box.remove_widget(accordion_item)

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
