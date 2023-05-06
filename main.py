import asyncio
import logging.config
import os
import sys
from pathlib import Path

import kivy
from kivy import platform
from kivy.resources import resource_add_path

from audio_chef_app import app

kivy.require('2.0.0')

if platform == "macosx":  # mac will not write into app folder
    home_dir = os.path.expanduser('~/')
    ffmpeg_path = str(Path(__file__).parent / 'mac/ffmpeg')
else:
    home_dir = app.directory
    ffmpeg_path = str(Path(__file__).parent / 'windows/ffmpeg')

log_file_name = os.path.join(home_dir, 'audio_chef.log')

LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {  # The formatter name, it can be anything that I wish
            'format': '%(asctime)s %(name)s[%(process)d] %(levelname)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',  # How to display dates
        },
    },
    'handlers': {
        'file': {
            'formatter': 'default',
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': log_file_name,
        },
        'output': {
            'formatter': 'default',
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        }
    },
    'loggers': {
        'audiochef': {
            'level': 'DEBUG',
            'handlers': [
                'file',
                'output',
            ]
        }
    },
}

logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger('audiochef')

logger.info('Setting ffmpeg path and changing cwd', extra={'ffmpeg_path': ffmpeg_path, 'home_dir': home_dir})
os.environ['PATH'] += os.pathsep + ffmpeg_path
os.chdir(home_dir)

if hasattr(sys, '_MEIPASS'):
    logger.info('Adding MEIPASS path to resource path and PATH env var', extra={'MEIPASS_path': sys._MEIPASS})
    resource_add_path(os.path.join(sys._MEIPASS))
    os.environ['PATH'] += os.pathsep + sys._MEIPASS

if __name__ == "__main__":
    logger.info('Initializing event loop ...')
    loop = asyncio.get_event_loop()
    logger.info('Running AudioChef App ...')
    loop.run_until_complete(app.async_run(async_lib='asyncio'))
    loop.close()
