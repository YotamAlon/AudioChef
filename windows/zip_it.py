from os.path import split, join
from PyInstaller import __main__ as pyinst

src_dir = split(split(__file__)[0])[0]
pyinst.run([
    join(src_dir, 'main.py'),
    '--onefile', '--noconsole',
    '--add-binary', 'C:\\Users\\yotam\\PycharmProjects\\AudioChef\\windows\\ffmpeg\\bin\\ffmpeg.exe;.',
    '--add-data', 'C:\\Users\\yotam\\PycharmProjects\\AudioChef\\assets;.'
    ])
