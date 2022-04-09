import os
import traceback
import uuid
from datetime import datetime

from kivy.app import App
from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from pedalboard import Pedalboard

from audio_formats import load_audio_formats, SUPPORTED_AUDIO_FORMATS, AudioFile
from helper_classes import ArgumentBox, OptionsBox, PresetsFile, PresetButton, UnexecutableRecipeError
from kivy_helpers import toggle_widget
import logging
from transformations import TRASNFORMATIONS

logger = logging.getLogger('audiochef')


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
        app.dispatch('on_name_changer_update')

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


class TransformationParameterPopup(Popup):
    save_callback = ObjectProperty()

    def __init__(self, arguments, **kwargs):
        super().__init__(**kwargs)
        for arg in arguments:
            if arg.options is not None:
                pass
            else:
                logger.debug(f'TransformationForm ({id(self)}): adding ArgumentBox(type={arg.type}, name={arg.name}, '
                             f'text={str(arg.default) if arg.default is not None else arg.type()}')
                self.ids.args_box.add_widget(ArgumentBox(
                    type=arg.type, name=arg.name,
                    initial=str(arg.default) if arg.default is not None else arg.type(),
                ))

    def get_argument_dict(self):
        return {arg.name: arg.type(arg.text) for arg in self.ids.args_box.children}


class TransformationForm(BoxLayout):
    remove_callback = ObjectProperty()
    transformations = TRASNFORMATIONS.keys()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_transform: str = None
        self.arg_values = {}

    def shift_up(self):
        self_index = self.parent.children.index(self)
        parent = self.parent
        parent.remove_widget(self)
        parent.add_widget(self, self_index + 1)

    def shift_down(self):
        self_index = self.parent.children.index(self)
        parent = self.parent
        parent.remove_widget(self)
        parent.add_widget(self, max(self_index - 1, 0))

    def select_transformation(self, transform_name):
        self.selected_transform = transform_name
        self.ids.args_box.clear_widgets()

    def open_parameter_popup(self):
        TransformationParameterPopup(TRASNFORMATIONS[self.selected_transform].arguments,
                                     title=f'Edit {self.selected_transform} parameters',
                                     save_callback=self.update_arg_values).open()

    def update_arg_values(self, arg_values: dict):
        self.arg_values = arg_values
        logger.debug(f'Arguments for {self.selected_transform} updated to {arg_values}')

    def get_selected_tranform(self):
        if self.selected_transform is None:
            return None
        return self.selected_transform, self.arg_values

    def load_args_dict(self, args_dict: dict):
        self.arg_values = args_dict

    def remove(self):
        self.remove_callback(self)

    def get_state(self):
        if self.selected_transform is None:
            return None
        return {'transform_name': self.selected_transform, 'args': self.arg_values}

    def load_state(self, state):
        logger.debug(f'TransformationForm ({id(self)}): loading state {state}')
        if state is None:
            return

        self.selected_transform = state['transform_name']
        self.ids.spinner.text = state['transform_name']
        self.load_args_dict(state['args'])


class AudioChefWindow(BoxLayout):
    name_changer: OutputChanger = ObjectProperty()
    name_locked = BooleanProperty()
    ext_box: OptionsBox = ObjectProperty()
    ext_locked = BooleanProperty()
    transforms_box: Widget = ObjectProperty()
    transforms_locked: BooleanProperty()
    presets_box: Widget = ObjectProperty()
    file_box: Widget = ObjectProperty()

    def __init__(self, **kwargs):
        logger.debug('Starting initialization of AudioChef main window ...')
        self.presets_file = PresetsFile()
        self.selected_transformations = []
        self.selected_files = []
        self.file_widget_map = {}
        super().__init__(**kwargs)

        logger.debug('Binding dropfile event ...')
        Window.bind(on_dropfile=self.on_dropfile)
        Window.clearcolor = app.window_background_color
        logger.debug('Initialization of AudioChef main window completed.')

    def on_kv_post(self, base_widget):
        self.ext_box.name = 'Choose the output format (empty means the same as the input if supported)'
        self.ext_box.options = [''] + [format_.ext.lower() for format_ in SUPPORTED_AUDIO_FORMATS if format_.can_encode]

        presets = self.presets_file.get_presets()
        self.reload_presets(presets)
        default_preset_name = next((i for i, preset in enumerate(presets) if preset.get('default', False)), None)
        if default_preset_name:
            self.load_preset(default_preset_name)

        app.bind(on_clear_files=self.clear_files)
        app.bind(on_add_transform_item=self.add_tranform_item)
        app.bind(on_name_changer_update=self.filename_preview)

    def reload_presets(self, presets):
        self.presets_box.clear_widgets()
        for preset in presets:
            self.presets_box.add_widget(PresetButton(
                preset_name=preset['name'], default=preset.get('default', False),
                load_preset=self.load_preset, rename_preset=self.rename_preset, remove_preset=self.remove_preset,
                make_default=self.make_preset_default))

    def on_dropfile(self, window, filename: bytes):
        filename = filename.decode()
        audio_file = AudioFile(filename)
        if audio_file not in self.selected_files:
            self.selected_files.append(audio_file)
            file_label = Label(text=audio_file.filename)
            self.file_box.add_widget(file_label)

            preview_label = Label(text=self.get_output_filename(audio_file.filename))
            self.file_box.add_widget(preview_label)

            remove_button = Button(text='-', width=50, size_hint_x=None,
                                   on_release=lambda x: self.remove_file(audio_file))
            self.file_box.add_widget(remove_button)
            self.file_widget_map[audio_file.filename] = (file_label, preview_label, remove_button)

    def remove_file(self, file: AudioFile):
        for widget in self.file_widget_map[file.filename]:
            self.file_box.remove_widget(widget)
        del self.file_widget_map[file.filename]
        self.selected_files.remove(file)

    def clear_files(self, button):
        for file in self.selected_files[:]:
            self.remove_file(file)

    def execute_preset(self):
        try:
            self.check_input_file_formats()
            self.check_output_file_formats()

            transformations = self.get_transformations()
            self.check_selected_transformation(transformations)
            for audio_file in self.selected_files:
                outfile_name = self.get_output_name(audio_file.source_name)
                outfile_ext = self.get_output_ext(audio_file.source_ext)

                audio, sample_rate = audio_file.get_audio_data()

                board = self.prepare_board(sample_rate, transformations)
                res = board(audio)

                audio_file.write_audio_data(outfile_name, outfile_ext, res, sample_rate)
        except UnexecutableRecipeError as e:
            logger.error(repr(e))
            Popup(title='I Encountered an Error!',
                  content=Label(text='I wrote all the info for the developer in a log file.\n'
                                     'Check the folder with AudioChef it in.'))
        except Exception:
            logger.error(traceback.format_exc())
            Popup(title='I Encountered an Error!',
                  content=Label(text='I wrote all the info for the developer in a log file.\n'
                                     'Check the folder with AudioChef it in.'))

    def save_preset(self):
        preset = {'name': str(uuid.uuid4()), 'ext': self.ext_box.text,
                  'transformations': [child.get_state() for child in self.transforms_box.children[::-1]],
                  'name_changer': self.name_changer.get_state()}
        self.presets_file.save_preset(preset)

    def load_preset(self, preset_id):
        logger.debug(f'AudioChefWindow: loading preset {preset_id}')
        preset = self.presets_file.get_preset(preset_id)
        logger.debug(f'AudioChefWindow: preset {preset_id} - {preset}')
        logger.debug(self.ext_box.options)
        if not self.ext_locked:
            self.ext_box.text = preset['ext']

        if not self.transforms_locked:
            self.transforms_box.clear_widgets()
            for transform_state in preset['transformations']:
                self.add_tranform_item(None)
                logger.debug(self.transforms_box.children)
                self.transforms_box.children[0].load_state(transform_state)

        if not self.name_locked:
            self.name_changer.load_state(preset['name_changer'])

    def rename_preset(self, preset_name, new_name):
        self.presets_file.rename_preset(preset_name, new_name)
        self.reload_presets(self.presets_file.get_presets())

    def remove_preset(self, preset_name):
        self.presets_file.remove_preset(preset_name)
        self.reload_presets(self.presets_file.get_presets())

    def make_preset_default(self, preset_name, val):
        presets = self.presets_file.get_presets()
        for preset in presets:
            if preset['name'] == preset_name:
                preset['default'] = val
        self.presets_file.set_presets(presets)

    def check_input_file_formats(self):
        for audio_file in self.selected_files:
            name, ext = os.path.splitext(audio_file.filename)

            if ext.lower()[1:] not in [format_.ext.lower() for format_ in SUPPORTED_AUDIO_FORMATS if format_.can_decode]:
                raise UnexecutableRecipeError(f'"{audio_file.filename}" is not in a supported format')

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

    def get_output_filename(self, filename):
        name, ext = os.path.splitext(filename)
        if ext.strip('.') not in [format_.ext for format_ in SUPPORTED_AUDIO_FORMATS if format_.can_decode]:
            return "This file format is not supported"
        return self.get_output_name(name) + self.get_output_ext(ext)

    def get_output_name(self, name):
        path, filename = os.path.split(name)
        return os.path.join(path, self.name_changer.change_name(filename))

    def get_output_ext(self, ext):
        return '.' + (self.ext_box.text or ext[1:])

    def add_tranform_item(self, button):
        self.transforms_box.add_widget(TransformationForm(remove_callback=self.remove_transformation))

    def remove_transformation(self, accordion_item):
        self.transforms_box.remove_widget(accordion_item)

    def filename_preview(self, button):
        for audio_file in self.selected_files:
            self.file_widget_map[audio_file.filename][1].text = self.get_output_filename(audio_file.filename)


class AudioChefApp(App):
    version = '0.1'
    icon = 'assets/chef_hat.png'
    window_background_color = (220 / 255, 220 / 255, 220 / 255, 1)
    main_color = (43 / 255, 130 / 255, 229 / 255)
    light_color = (118 / 255, 168 / 255, 229 / 255)
    dark_color = (23 / 255, 63 / 255, 107 / 255)
    log_level = logging.INFO
    run_dir = None

    def __init__(self):
        logger.setLevel(self.log_level)
        super().__init__()

    def build(self):
        logger.info('Registering custom events ...')
        self.register_event_type('on_clear_files')
        self.register_event_type('on_add_transform_item')
        self.register_event_type('on_name_changer_update')

        logger.info('Loading KV file ...')
        self.load_kv('audio_chef.kv')

        logger.info('Loading audio formats ...')
        load_audio_formats()
        return AudioChefWindow()

    def on_clear_files(self):
        pass

    def on_add_transform_item(self):
        pass

    def on_name_changer_update(self):
        pass


app = AudioChefApp()
