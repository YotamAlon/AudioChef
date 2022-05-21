import os
import pprint

import pydub
import logging
import soundfile
import subprocess

ffmpeg_formats = {}
SUPPORTED_AUDIO_FORMATS = []

logger = logging.getLogger("audiochef")


class AudioFormatter:
    def __init__(self, can_encode, can_decode, ext, description):
        self.can_encode = can_encode
        self.can_decode = can_decode
        self.ext = ext
        self.description = description

    def decode(self, input_file, output_file):
        raise NotImplementedError()

    def encode(self, input_file, output_file):
        raise NotImplementedError()

    def __repr__(self):
        return f'AudioFormat ({self.ext}) [{"D" if self.can_decode else ""}{"E" if self.can_encode else ""}]'


class FFMPEGAudioFormatter(AudioFormatter):
    def decode(self, input_file, output_file):
        logger.info(f"Reading from file {input_file}")
        given_audio = pydub.AudioSegment.from_file(input_file, format=self.ext)
        given_audio.export(output_file, format="wav")

    def encode(self, input_file, output_file):
        given_audio = pydub.AudioSegment.from_file(input_file, format="wav")
        logger.info(f"Writing file {output_file}")
        given_audio.export(output_file, format=self.ext)


class NoCompatibleAudioFormatException(Exception):
    pass


class AudioFile:
    def __init__(self, filename: str):
        self.filename = filename
        name, ext = os.path.splitext(filename)
        self.source_name = name
        self.source_ext = ext.strip(".")
        self.source_audio_format = next(
            (
                format_
                for format_ in SUPPORTED_AUDIO_FORMATS
                if format_.can_decode and format_.ext == self.source_ext
            ),
            None,
        )
        if self.source_audio_format is None:
            raise NoCompatibleAudioFormatException(
                f"New supported audio format found for '{filename}'!"
            )
        self.internal_file = None
        self.destination_name = self.source_name
        self.destination_ext = self.source_ext

    def __eq__(self, other):
        if not isinstance(other, AudioFile):
            raise TypeError("second argument is not of type AudioFile")

        return self.filename == other.filename

    def get_audio_data(self):
        if self.internal_file is None:
            self.create_internal_file()
        return soundfile.read(self.internal_file)

    def get_internal_file_path(self, name):
        return os.path.join(os.getcwd(), "internal", name + ".wav")

    def create_internal_file(self):
        _, name = os.path.split(self.source_name)
        self.internal_file = self.get_internal_file_path(name)
        internal_dir = os.path.split(self.internal_file)[0]
        if not os.path.exists(internal_dir):
            os.mkdir(internal_dir)

        if os.path.exists(self.internal_file):
            os.remove(self.internal_file)

        self.source_audio_format.decode(self.filename, self.internal_file)

    def update_destination_name_and_ext(self, new_filename):
        logger.debug(
            f"Updating {self.filename}'s output file to be {os.path.splitext(new_filename)}"
        )
        self.destination_name, self.destination_ext = os.path.splitext(new_filename)
        self.destination_ext = self.destination_ext.strip(".")

    def write_output_file(self, data, sample_rate):
        with soundfile.SoundFile(
            self.internal_file,
            "w",
            samplerate=sample_rate,
            channels=len(data.shape),
        ) as f:
            f.write(data)

        output_format = next(
            (
                format_
                for format_ in SUPPORTED_AUDIO_FORMATS
                if format_.can_encode and format_.ext == self.destination_ext
            ),
            None,
        )
        output_format.encode(
            self.internal_file,
            f"{self.destination_name}.{self.destination_ext}",
        )


def load_audio_formats():
    logger.info("Loading supported audio formats from ffmpeg ...")
    logger.debug(f"running ffmpeg")
    lines = (
        subprocess.check_output(
            ["ffmpeg", "-formats"], stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        .decode()
        .split(os.linesep)
    )
    logger.debug(pprint.pformat(lines))

    for line in lines[lines.index(" --") + 1 : -1]:
        encode_decode, exts, description = line.strip().split(maxsplit=2)
        for ext in exts.split(","):
            if ext in ffmpeg_formats:
                ffmpeg_formats[ext]["can_decode"] |= "D" in encode_decode
                ffmpeg_formats[ext]["can_encode"] |= "E" in encode_decode
                ffmpeg_formats[ext]["description"] += "|" + description
            else:
                ffmpeg_formats[ext] = {
                    "can_decode": "D" in encode_decode,
                    "can_encode": "E" in encode_decode,
                    "description": description,
                }

    SUPPORTED_AUDIO_FORMATS.extend(
        [
            FFMPEGAudioFormatter(**{"ext": ext, **ext_details})
            for ext, ext_details in ffmpeg_formats.items()
        ]
    )

    # m4a is just mp4 that doesn't have video, so use mp4 formatter encoding as a workaround to support m4a fully
    m4a_formatter = next(
        (format_ for format_ in SUPPORTED_AUDIO_FORMATS if format_.ext == "m4a")
    )
    if m4a_formatter.can_encode:
        print(
            "It appears ffmpeg now supports m4a encoding out-of-the-box. You can remove this code"
        )
    else:
        mp4_formatter = next(
            (format_ for format_ in SUPPORTED_AUDIO_FORMATS if format_.ext == "mp4")
        )
        m4a_formatter.can_encode = True
        m4a_formatter.encode = mp4_formatter.encode

    logger.debug(pprint.pformat(SUPPORTED_AUDIO_FORMATS))
    logger.info(f"Loaded {len(SUPPORTED_AUDIO_FORMATS)} audio formats.")
