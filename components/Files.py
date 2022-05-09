import os
import logging
from typing import List

from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup

from utils.Dispatcher import dispatcher
from utils.audio_formats import (
    AudioFile,
    SUPPORTED_AUDIO_FORMATS,
    NoCompatibleAudioFormatException,
)
from utils.State import state

logger = logging.getLogger("audiochef")


class FileList(GridLayout):
    def __init__(self, **kwargs):
        state.set_prop("selected_files", [])
        self.file_widget_map = {}
        super().__init__(**kwargs)

    def on_kv_post(self, base_widget):
        Window.bind(on_drop_file=self.add_file)
        dispatcher.bind(on_clear_files=self.clear_files)
        dispatcher.bind(on_name_changer_update=self.update_filenames)
        dispatcher.bind(on_output_format_update=self.update_filenames)

    def add_file(self, window, filename: bytes, x, y):
        filename = filename.decode()
        try:
            audio_file = AudioFile(filename)
        except NoCompatibleAudioFormatException:
            logger.error(f"Unable to find audio format for {filename}")
            Popup(
                title="Unsupported file format!",
                content=Label(
                    text=f"The file '{filename}' you just tried to add\n"
                    f"is encoded in an audio format which is not currently suported.\n"
                    f"If you think this is a mistake, please send me your audio_chef.log\n"
                    f"file along with this audio file."
                ),
                size_hint=(0.5, 0.5),
            ).open()
            return
        selected_files = state.get_prop("selected_files")

        if audio_file not in selected_files:
            selected_files.append(audio_file)
            file_label = FileLabel(text=audio_file.filename)
            self.add_widget(file_label)

            preview_label = FileLabel(
                text=self.get_output_filename(audio_file.filename)
            )
            self.add_widget(preview_label)

            remove_button = Button(
                text="-",
                width=50,
                size_hint_x=None,
                on_release=lambda x: self.remove_file(audio_file),
            )
            self.add_widget(remove_button)
            self.file_widget_map[audio_file.filename] = (
                file_label,
                preview_label,
                remove_button,
            )

        state.set_prop("selected_files", selected_files)

    def remove_file(self, file: AudioFile):
        selected_files = state.get_prop("selected_files")

        for widget in self.file_widget_map[file.filename]:
            self.remove_widget(widget)
        del self.file_widget_map[file.filename]
        selected_files.remove(file)

        state.set_prop("selected_files", selected_files)

    def clear_files(self, *args, **kwargs):
        for file in state.get_prop("selected_files")[:]:
            self.remove_file(file)

    def update_filenames(self, *args, **kwargs):
        selected_files: List[AudioFile] = state.get_prop("selected_files")
        for audio_file in selected_files:
            new_filename = self.get_output_filename(audio_file.filename)
            audio_file.update_destination_name_and_ext(new_filename)
            self.file_widget_map[audio_file.filename][1].text = new_filename

    def get_output_filename(self, filename):
        name, ext = os.path.splitext(filename)
        if ext.strip(".") not in [
            format_.ext for format_ in SUPPORTED_AUDIO_FORMATS if format_.can_decode
        ]:
            return "This file format is not supported"
        return self.get_output_name(name) + self.get_output_ext(ext)

    def get_output_name(self, name):
        path, filename = os.path.split(name)
        return os.path.join(path, state.get_prop("name_change_func")(filename))

    def get_output_ext(self, ext):
        output_ext = state.get_prop("output_ext")
        return "." + (output_ext or ext[1:])


class FileLabel(Label):
    pass
