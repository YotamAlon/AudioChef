import pathlib
import platform
from PyInstaller import __main__ as pyinst
from kivy_deps import sdl2, glew


def main():
    src_dir = pathlib.Path(__file__).parent
    command = [
        src_dir / "audio_chef" / "main.py",
        "-y",
        "-n",
        "AudioChef",
        "-i",
        src_dir / "assets" / "chef_hat.ico",
        "--onefile",
        "--noconsole",
        "--add-binary",
        f"{src_dir / '.ffmpeg/ffmpeg'}/:.ffmpeg/ffmpeg",
        "--add-data",
        f"{src_dir / 'assets'}:assets",
        "--add-data",
        f"{src_dir / 'kv'}:kv",
    ]

    match platform.system():
        case "Darwin":
            pass
        case "Linux":
            pass
        case "Windows":
            for dep in sdl2.dep_bins + glew.dep_bins:
                command.extend(["--add-binary", f"{dep}/;."])
        case default:
            raise NotImplementedError(f"Unsupported platform: {default}")

    pyinst.run(list(map(str, command)))


if __name__ == "__main__":
    main()
