import logging
import os

import pedalboard
from kivy.uix.label import Label
from kivy.uix.popup import Popup

from components.helper_classes import UnexecutableRecipeError
from utils.audio_formats import AudioFile, SUPPORTED_AUDIO_FORMATS

logger = logging.getLogger("audiochef")


class Controller:
    @classmethod
    def execute_preset(cls, output_ext, selected_files, transformations) -> None:
        try:
            cls.check_input_file_formats(selected_files=selected_files)
            cls.check_output_file_formats(output_ext)

            cls.check_selected_transformation(transformations)
            for audio_file in selected_files:
                audio, sample_rate = audio_file.get_audio_data()

                board = cls.prepare_board(transformations)
                res = board(audio, sample_rate)

                audio_file.write_output_file(res, sample_rate)
        except UnexecutableRecipeError as e:
            logger.error(repr(e))
            Popup(
                title="I Encountered an Error!",
                content=Label(
                    text="I wrote all the info for the developer in a log file.\n"
                    "Check the folder with AudioChef it in."
                ),
            )

    @staticmethod
    def check_input_file_formats(selected_files: list[AudioFile]) -> None:
        for audio_file in selected_files:
            name, ext = os.path.splitext(audio_file.filename)

            if ext.lower()[1:] not in [
                format_.ext.lower()
                for format_ in SUPPORTED_AUDIO_FORMATS
                if format_.can_decode
            ]:
                raise UnexecutableRecipeError(
                    f'"{audio_file.filename}" is not in a supported format'
                )

    @staticmethod
    def check_output_file_formats(output_ext: str) -> None:
        if output_ext not in [
            format_.ext.lower()
            for format_ in SUPPORTED_AUDIO_FORMATS
            if format_.can_encode
        ]:
            raise UnexecutableRecipeError(
                f'"{output_ext}" is not a supported output format'
            )

    @staticmethod
    def check_selected_transformation(transformations: list) -> None:
        if len(transformations) == 0 or any(
            transform is None for transform in transformations
        ):
            raise UnexecutableRecipeError("You must choose a transformation to apply")

    @staticmethod
    def prepare_board(transformations: list) -> pedalboard.Pedalboard:
        logger.debug(transformations)
        return pedalboard.Pedalboard(
            [transform(**kwargs) for transform, kwargs in transformations]
        )
