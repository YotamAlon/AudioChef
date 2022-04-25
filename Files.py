import os
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from Dispatcher import dispatcher
from audio_formats import AudioFile, SUPPORTED_AUDIO_FORMATS
from state import state


class FileList(GridLayout):
    def __init__(self, **kwargs):
        state.set_prop("selected_files", [])
        self.file_widget_map = {}
        super().__init__(**kwargs)

    def on_kv_post(self, base_widget):
        Window.bind(on_dropfile=self.add_file)
        dispatcher.bind(on_clear_files=self.clear_files)
        dispatcher.bind(on_name_changer_update=self.update_filenames)
        dispatcher.bind(on_output_format_update=self.update_filenames)

    def add_file(self, window, filename: bytes):
        filename = filename.decode()
        audio_file = AudioFile(filename)
        selected_files = state.get_prop("selected_files")

        if audio_file not in selected_files:
            selected_files.append(audio_file)
            file_label = Label(text=audio_file.filename)
            self.add_widget(file_label)

            preview_label = Label(text=self.get_output_filename(audio_file.filename))
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
        selected_files = state.get_prop("selected_files")
        for audio_file in selected_files:
            self.file_widget_map[audio_file.filename][1].text = self.get_output_filename(
                audio_file.filename
            )

    def get_output_filename(self, filename):
        name, ext = os.path.splitext(filename)
        if ext.strip(".") not in [
            format_.ext for format_ in SUPPORTED_AUDIO_FORMATS if format_.can_decode
        ]:
            return "This file format is not supported"
        return self.get_output_name(name) + self.get_output_ext(ext)

    def get_output_name(self, name):
        path, filename = os.path.split(name)
        return os.path.join(path, state.get_prop('name_change_func')(filename))

    def get_output_ext(self, ext):
        output_ext = state.get_prop("output_ext")
        return "." + (output_ext or ext[1:])
