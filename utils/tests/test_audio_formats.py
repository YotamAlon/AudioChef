from utils.audio_formats import FFMPEGAudioFormatter, SUPPORTED_AUDIO_FORMATS, AudioFile


class TestFFMPEGAudioFormatter:
    def test_initialization(self):
        FFMPEGAudioFormatter(True, True, 'test', 'test_formatter')


class TestAudioFile:
    def test_initialization_with_compatible_format(self):
        SUPPORTED_AUDIO_FORMATS.append(FFMPEGAudioFormatter('', True, 'test', 'test_formatter'))
        AudioFile('filename.test')

    def test_initialization_without_compatible_format(self):
        SUPPORTED_AUDIO_FORMATS.append(FFMPEGAudioFormatter(True, False, 'test', 'test_formatter'))
        AudioFile('filename.test')
