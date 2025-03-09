import pathlib

PROJECT_ROOT = pathlib.Path(__file__).parent.parent

CURRENT_PRESET = "current_preset"
CURRENT_NAME_CHANGE_PARAMS = "current_name_change_params"
CURRENT_TRANSFORMATIONS = "current_transformations"
CURRENT_EXT = "current_ext"
AVAILABLE_TRANSFORMATIONS = "available_transformations"

FFMPEG_PATH = PROJECT_ROOT / ".ffmpeg" / "ffmpeg"
