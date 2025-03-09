"""
Script to download install dependencies from requirements.txt file and download the relevant ffmpeg binary
"""

import os
import urllib.request

import platform
import pathlib
import zipfile

project_root = pathlib.Path(__file__).parent
ffmpeg_dir = project_root / ".ffmpeg"
ffmpeg_zip = ffmpeg_dir / "ffmpeg.zip"


def print_progress(block_num, block_size, total_size):
    downloaded = block_num * block_size
    progress = (downloaded / total_size) * 100
    print(f"\rDownloading ffmpeg: {progress:.2f}%", end="")


def download_ffmpeg():
    platform_name = platform.system()
    if platform_name == "Windows":
        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    elif platform_name == "Darwin":
        url = "https://evermeet.cx/ffmpeg/ffmpeg-7.1.1.zip"
    elif platform_name == "Linux":
        url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
    else:
        raise Exception(f"Unsupported platform: {platform_name}")

    ffmpeg_dir.mkdir(exist_ok=True, parents=True)
    if ffmpeg_zip.exists():
        try:
            with zipfile.ZipFile(ffmpeg_zip, "r") as zip_ref:
                zip_ref.testzip()
        except zipfile.BadZipFile:
            ffmpeg_zip.unlink()
    urllib.request.urlretrieve(url, ffmpeg_zip, print_progress)
    with zipfile.ZipFile(ffmpeg_zip, "r") as zip_ref:
        zip_ref.extractall(ffmpeg_dir)

    # find ffmpeg binary in the extracted directory
    if platform_name == "Windows":
        os.rename(next(ffmpeg_dir.glob("**/ffmpeg.exe")), ffmpeg_dir / "ffmpeg.exe")
    elif platform_name == "Darwin":
        os.rename(next(ffmpeg_dir.glob("**/ffmpeg")), ffmpeg_dir / "ffmpeg")
    elif platform_name == "Linux":
        os.rename(next(ffmpeg_dir.glob("**/ffmpeg")), ffmpeg_dir / "ffmpeg")
        os.chmod(ffmpeg_dir / "ffmpeg", 0o755)


if __name__ == "__main__":
    download_ffmpeg()
