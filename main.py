import os
log_file_name = os.path.join(os.getcwd(), 'audio_chef.log')

import sys
# sys.stdout = sys.stderr = open(log_file_name, 'a')

import kivy
kivy.require('2.0.0')

import asyncio
import traceback
import logging.config
from components.AudioChefApp import app
from kivy.resources import resource_add_path

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

if __name__ == "__main__":
    try:
        logger.info('Initializing event loop ...')
        loop = asyncio.get_event_loop()
        if hasattr(sys, '_MEIPASS'):
            resource_add_path(os.path.join(sys._MEIPASS))
            os.environ['PATH'] += os.pathsep + sys._MEIPASS
            app.run_dir = sys._MEIPASS

        logger.info('Running AudioChef App ...')
        loop.run_until_complete(app.async_run(async_lib='asyncio'))
        loop.close()
    except Exception as e:
        logger.critical(repr(e) + '\n' + traceback.format_exc())
