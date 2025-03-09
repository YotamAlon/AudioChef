import logging
import os
import typing

import pedalboard

from audio_chef.components.helper_classes import UnexecutableRecipeError
from audio_chef.models.preset import Transformation
from audio_chef.utils.audio_formats import AudioFile, SUPPORTED_AUDIO_FORMATS
from audio_chef.utils.transformations import TRANSFORMATIONS

logger = logging.getLogger("audiochef")


class AudioClient:
    @classmethod
    def execute_preset(
        cls,
        output_ext: str,
        selected_files: list[AudioFile],
        transformations: list[Transformation],
    ) -> bool:
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
            return False
        return True

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
    def check_selected_transformation(transformations: list[Transformation]) -> None:
        if len(transformations) == 0 or any(
            transform.name is None for transform in transformations
        ):
            raise UnexecutableRecipeError("You must choose a transformation to apply")

    @classmethod
    def prepare_board(
        cls, transformations: list[Transformation]
    ) -> pedalboard.Pedalboard:
        logger.debug(transformations)
        return pedalboard.Pedalboard(
            [
                cls.get_transform_class(transform.name)(**transform.params)
                for transform in transformations
            ]
        )

    @staticmethod
    def get_transform_class(transform_name: str) -> typing.Type[pedalboard.Plugin]:
        return TRANSFORMATIONS[transform_name].transform
