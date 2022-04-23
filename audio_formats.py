import os
import pprint

import pydub
import logging
import soundfile
import subprocess

ffmpeg_formats = {}
SUPPORTED_AUDIO_FORMATS = []

logger = logging.getLogger('audiochef')


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
        given_audio = pydub.AudioSegment.from_file(input_file, format=self.ext)
        given_audio.export(output_file, format="wav")

    def encode(self, input_file, output_file):
        given_audio = pydub.AudioSegment.from_file(input_file, format='wav')
        given_audio.export(output_file, format=self.ext)


class AudioFile:
    def __init__(self, filename: str):
        self.filename = filename
        name, ext = os.path.splitext(filename)
        self.source_name = name
        self.source_ext = ext.strip('.')
        self.source_audio_format = next((format_ for format_ in SUPPORTED_AUDIO_FORMATS if format_.ext == ext), None)
        self.internal_file = None

    def __eq__(self, other):
        if not isinstance(other, AudioFile):
            raise TypeError('second argument is not of type AudioFile')

        return self.filename == other.filename

    def get_audio_data(self):
        if self.internal_file is None:
            self.create_internal_file()
        return soundfile.read(self.internal_file)

    def get_internal_file_path(self, name):
        return os.path.join(os.getcwd(), 'internal', name + '.wav')

    def create_internal_file(self):
        _, name = os.path.split(self.source_name)
        self.internal_file = self.get_internal_file_path(name)

        self.source_audio_format.decode(self.source_name + self.source_ext, self.internal_file)

    def write_output_file(self, output_name, output_ext, data, sample_rate):
        with soundfile.SoundFile(output_name + '.wav', 'w', samplerate=sample_rate, channels=len(data.shape)) as f:
            f.write(data)

        output_format = next((format_ for format_ in SUPPORTED_AUDIO_FORMATS if format_.ext == output_ext.strip('.')), None)
        output_format.encode(output_name + '.wav', output_name + output_ext)


def load_audio_formats():
    logger.info('Loading supported audio formats from ffmpeg ...')
    logger.debug(f'running ffmpeg')
    output = subprocess.check_output(['ffmpeg', '-formats'], stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL).decode()
    logger.debug(output)
    lines = output.split('\r\n')

    for line in lines[lines.index(' --') + 1:-1]:
        encode_decode, exts, description = line.strip().split(maxsplit=2)
        for ext in exts.split(','):
            if ext in ffmpeg_formats:
                ffmpeg_formats[ext]['can_decode'] |= 'D' in encode_decode
                ffmpeg_formats[ext]['can_encode'] |= 'E' in encode_decode
                ffmpeg_formats[ext]['description'] += '|' + description
            else:
                ffmpeg_formats[ext] = {'can_decode': 'D' in encode_decode, 'can_encode': 'E' in encode_decode,
                                       'description': description}

    SUPPORTED_AUDIO_FORMATS.extend([FFMPEGAudioFormatter(**{'ext': ext, **ext_details})
                                    for ext, ext_details in ffmpeg_formats.items()])

    # m4a is just mp4 that doesn't have video, so use mp4 formatter encoding as a workaround to support m4a fully
    m4a_formatter = next((format_ for format_ in SUPPORTED_AUDIO_FORMATS if format_.ext == 'm4a'))
    if m4a_formatter.can_encode:
        print('It appears ffmpeg now supports m4a encoding out-of-the-box. You can remove this code')
    else:
        mp4_formatter = next((format_ for format_ in SUPPORTED_AUDIO_FORMATS if format_.ext == 'mp4'))
        m4a_formatter.can_encode = True
        m4a_formatter.encode = mp4_formatter.encode

    logger.debug(pprint.pformat(SUPPORTED_AUDIO_FORMATS))
    logger.info(f'Loaded {len(SUPPORTED_AUDIO_FORMATS)} audio formats.')

