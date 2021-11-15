from os.path import split, join
from PyInstaller import __main__ as pyinst


pyinst.run([
    join(split(split(__file__)[0])[0], 'main.py'),
    '--onefile', '--noconsole'
    ])
