from os.path import split, join, dirname, abspath
from PyInstaller import __main__ as pyinst

src_dir = split(dirname(abspath(__file__)))[0]
command = [
    join(src_dir, 'main.py'), '-n', 'AudioChef', '-y', '-i',  join(src_dir, 'assets', 'chef_hat.ico'),
    '--onefile',
    '--noconsole',
    '--add-binary', f'{src_dir}/linux/ffmpeg/ffmpeg:.',
    '--add-data', f'{src_dir}/assets:assets',
    '--add-data', f'{src_dir}/audio_chef.kv:.',
    '--add-data', f'{src_dir}/kv:kv',
    ]

pyinst.run(command)
