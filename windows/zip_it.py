from os.path import split, join
from PyInstaller import __main__ as pyinst

src_dir = split(split(__file__)[0])[0]
pyinst.run([
    join(src_dir, 'main.py'), '-n', 'AudioChef', '-y', '-i',  join(src_dir, 'assets', 'chef_hat.ico'),
    # '--onefile',
    '--noconsole',
    '--add-binary', join(src_dir, 'windows\\ffmpeg\\ffmpeg.exe') + ';.',
    '--add-data', join(src_dir, 'assets') + ';.'
    ])
