import asyncio
import logging.config
import os
import pathlib
import sys
from pathlib import Path

import kivy
from kivy import platform
from kivy.resources import resource_add_path

from audio_chef.app import AudioChefApp
from audio_chef.consts import FFMPEG_PATH, PROJECT_ROOT

kivy.require("2.0.0")

project_dir = Path(__file__).parent.parent


if platform == "macosx":  # mac will not write into app folder
    home_dir = os.path.expanduser("~/")
elif platform == "linux":
    home_dir = PROJECT_ROOT
else:
    home_dir = PROJECT_ROOT

log_file_path = pathlib.Path(home_dir) / "audio_chef.log"
log_file_path.touch(exist_ok=True)

# Running inside pyinstaller
if getattr(sys, "frozen", False):
    handlers = {
        "file": {
            "formatter": "default",
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": log_file_path.as_posix(),
        }
    }
else:
    handlers = {
        "output": {
            "formatter": "default",
            "level": "DEBUG",
            "class": "logging.StreamHandler",
        }
    }

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {  # The formatter name, it can be anything that I wish
            "format": "%(asctime)s %(name)s[%(process)d] %(levelname)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",  # How to display dates
        },
    },
    "handlers": handlers,
    "loggers": {
        "audiochef": {
            "level": "DEBUG",
            "handlers": list(handlers.keys()),
        }
    },
}

logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger("audiochef")

logger.info(
    "Setting ffmpeg path and changing cwd",
    extra={"ffmpeg_path": FFMPEG_PATH, "home_dir": home_dir},
)
os.chdir(home_dir)
resource_add_path(project_dir.as_posix())

app = AudioChefApp()

if hasattr(sys, "_MEIPASS"):
    meipass = sys._MEIPASS
    logger.info(
        "Adding MEIPASS path to resource path and PATH env var",
        extra={"MEIPASS_path": meipass},
    )
    resource_add_path(os.path.join(meipass))
    os.environ["PATH"] += os.pathsep + meipass

if __name__ == "__main__":
    logger.info("Initializing event loop ...")
    loop = asyncio.get_event_loop()
    logger.info("Running AudioChef App ...")
    loop.run_until_complete(app.async_run(async_lib="asyncio"))
    loop.close()
