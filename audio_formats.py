import subprocess


output = subprocess.check_output(['ffmpeg', '-formats'])
lines = output.split(b'\r\n')
opt_formats = [line.split() for line in lines[lines.index(b' --') + 1:-1]]


class AudioFormat:
    def __init__(self, support, ext, *description):
        self.can_encode = 'E' in support.decode()
        self.can_decode = 'D' in support.decode()
        self.ext = ext.decode()
        self.description = ' '.join(map(bytes.decode, description))


SUPPORTED_AUDIO_FORMATS = [AudioFormat(opt_format[0], opt_format[1], *opt_format[2:])
                           for opt_format in opt_formats]
