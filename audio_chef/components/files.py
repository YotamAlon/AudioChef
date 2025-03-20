import logging
import os
from typing import List

from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label

from audio_chef.models.preset import NameChangeParameters, NameChangeMode
from audio_chef.utils.audio_formats import (
    AudioFile,
    SUPPORTED_AUDIO_FORMATS,
)

logger = logging.getLogger("audiochef")


class FileList(GridLayout):
    def __init__(self, **kwargs):
        self.selected_files: list[AudioFile] = []
        self.ext = ""
        self.name_change_parameters = NameChangeParameters(mode=NameChangeMode.REPLACE, wildcards_input="", replace_from_input="", replace_to_input="")
        self.file_widget_map = {}
        super().__init__(**kwargs)

    def add_file(self, audio_file: AudioFile):
        if audio_file not in self.selected_files:
            audio_file.update_destination_name_and_ext(
                self.get_output_filename(audio_file.filename)
            )
            self.selected_files.append(audio_file)

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

    def remove_file(self, file: AudioFile):
        for widget in self.file_widget_map[file.filename]:
            self.remove_widget(widget)
        del self.file_widget_map[file.filename]
        self.selected_files.remove(file)

    def update_files(self, files: List[AudioFile]):
        self.clear_files()
        for file in files:
            self.add_file(file)

    def clear_files(self, *args, **kwargs):
        for file in self.selected_files[:]:
            self.remove_file(file)

    def update_filenames(self, *args, **kwargs):
        for audio_file in self.selected_files:
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
        new_name = self.name_change_parameters.change_name(filename)
        return os.path.join(path, new_name)

    def get_output_ext(self, ext):
        return "." + (self.ext or ext[1:])


class FileLabel(Label):
    pass
