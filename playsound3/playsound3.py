from __future__ import annotations

import atexit
import logging
import os
import signal
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from threading import Thread
from typing import Callable

import certifi

logger = logging.getLogger(__name__)


class PlaysoundException(Exception):
    pass


####################
## DOWNLOAD TOOLS ##
####################

_DOWNLOAD_CACHE: dict[str, str] = {}


def _download_sound_from_web(link: str, destination: Path) -> None:
    # Identifies itself as a browser to avoid HTTP 403 errors
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64)"}
    request = urllib.request.Request(link, headers=headers)
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(request, context=context) as response, destination.open("wb") as out_file:
        out_file.write(response.read())


def _prepare_path(sound: str | Path) -> str:
    if isinstance(sound, str) and sound.startswith(("http://", "https://")):
        # To play file from URL, we download the file first to a temporary location and cache it
        if sound not in _DOWNLOAD_CACHE:
            sound_suffix = Path(sound).suffix
            with tempfile.NamedTemporaryFile(delete=False, prefix="playsound3-", suffix=sound_suffix) as f:
                _download_sound_from_web(sound, Path(f.name))
                _DOWNLOAD_CACHE[sound] = f.name
        sound = _DOWNLOAD_CACHE[sound]

    path = Path(sound)

    if not path.exists():
        raise PlaysoundException(f"File not found: {sound}")
    return path.absolute().as_posix()


####################
## SOUND BACKENDS ##
####################


def _select_linux_backend() -> str:
    """Select the best available audio backend for Linux systems."""
    logger.info("Selecting the best available audio backend for Linux systems.")

    try:
        subprocess.run(["gst-play-1.0", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        logger.info("Using gst-play-1.0 as the audio backend.")
        return "gst_play"
    except FileNotFoundError:
        pass

    try:
        subprocess.run(["ffplay", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        logger.info("Using ffplay as the audio backend.")
        return "ffplay"
    except FileNotFoundError:
        pass

    try:
        subprocess.run(["aplay", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        subprocess.run(["mpg123", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        logger.info("Using alsa (aplay-mpg123) as the audio backend.")
        return "aplay-mpg123"
    except FileNotFoundError:
        pass

    logger.info("No suitable audio backend found.")
    raise PlaysoundException("No suitable audio backend found. Install gstreamer or ffmpeg!")


def _check_wmplayer_exists() -> bool:
    return True


def _check_afplay_exists() -> bool:
    try:
        subprocess.run(["command", "-v", "afplay"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except FileNotFoundError:
        return False


def _select_default_backend() -> str:
    if "PLAYSOUND3_BACKEND" in os.environ:
        return os.environ["PLAYSOUND3_BACKEND"]

    if sys.platform == "win32" and _check_wmplayer_exists():
        return "wmplayer"
    if sys.platform == "darwin" and _check_afplay_exists():
        return "afplay"

    # Linux backends is the most suitable as a fallback
    # Some tools like gstreamer or ffmpeg could be installed on different systems
    return _select_linux_backend()


class _WMPlayerFakePopen:
    """Fake Popen-like object for wmplayer."""

    def __init__(self, sound: str):
        self._play: bool = True
        self.thread = Thread(target=self.play, args=(sound,), daemon=True)
        self.thread.start()

    def play(self, sound: str) -> None:
        try:
            import pythoncom  # type: ignore
            import win32com.client  # type: ignore
        except ImportError as e:
            raise PlaysoundException("pywin32 required to use the 'wmplayer' backend.") from e

        logger.debug("wmplayer: start play %s", sound)

        # Create the Windows Media Player COM object
        wmp = win32com.client.Dispatch("WMPlayer.OCX")
        wmp.settings.autoStart = True  # Ensure playback starts automatically

        # Set the URL to your MP3 file
        wmp.URL = sound
        wmp.controls.play()  # Start playback

        while wmp.playState != 1:  # playState 1 indicates stopped
            pythoncom.PumpWaitingMessages()  # Process COM events
            time.sleep(0.05)

            if not self._play:
                logger.debug("wmplayer: stop play %s", sound)
                wmp.controls.stop()
                break

        self._play = False
        logger.debug("wmplayer: finish play %s", sound)

    def send_signal(self, *_) -> None:
        self._play = False

    def poll(self) -> bool:
        return self._play

    def wait(self) -> None:
        self.thread.join()


def _get_gst_play_subprocess(sound) -> subprocess.Popen:
    return subprocess.Popen(["gst-play-1.0", "--no-interactive", "--quiet", sound])


def _get_afplay_subprocess(sound) -> subprocess.Popen:
    return subprocess.Popen(["afplay", sound])


def _get_alsa_subprocess(sound) -> subprocess.Popen:
    suffix = Path(sound).suffix

    if suffix == ".wav":
        return subprocess.Popen(["aplay", "--quiet", sound])
    elif suffix == ".mp3":
        return subprocess.Popen(["mpg123", "-q", sound])
    else:
        raise PlaysoundException(f"Backend not supported for {suffix} files")


def _get_alsa_mpg_subprocess(sound) -> subprocess.Popen:
    return subprocess.Popen(["mpg123", "-q", sound])


def _get_ffplay_subprocess(sound) -> subprocess.Popen:
    return subprocess.Popen(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", sound])


def _get_wmplayer_subprocess(sound) -> _WMPlayerFakePopen:
    return _WMPlayerFakePopen(sound)


################
## PLAYSOUND  ##
################


class Sound:
    """Play subprocess-based sound."""

    def __init__(
        self,
        name: str,
        subprocess_factory: Callable[[str], subprocess.Popen],
        block: bool,
    ) -> None:
        """Initialize the player and begin playing."""
        self.subprocess = subprocess_factory(name)

        if block:
            self.wait()

    def is_alive(self) -> bool:
        return self.subprocess.poll() is None

    def wait(self) -> None:
        self.subprocess.wait()

    def stop(self) -> None:
        if self.is_alive():
            self.subprocess.send_signal(signal.SIGINT)


def playsound(
    sound: str | Path,
    block: bool = True,
    backend: str | None = None,
) -> Sound:
    """Play a sound file using an audio backend availabile in your system.

    Args:
        sound: Path or URL to the sound file. Can be a string or pathlib.Path.
        block: If True, the function will block execution until the sound finishes playing.
               If False, sound will play in a background thread.
        backend: Name of the audio backend to use. Leave None for automatic selection.

    Returns:
        If `block` is True, the function will return None after the sound finishes playing.
        If `block` is False, the function will return the background thread object.

    """
    path = _prepare_path(sound)
    backend = backend or _PLAYSOUND_DEFAULT_BACKEND
    assert backend in _BACKEND_MAPPING, f"Unknown backend: {backend}"
    backend_fn = _BACKEND_MAPPING[backend]
    return Sound(path, backend_fn, block)


def _remove_cached_downloads(cache: dict[str, str]) -> None:
    """Remove all files saved in the cache when the program ends."""
    for path in cache.values():
        Path(path).unlink()


####################
## INITIALIZATION ##
####################


_BACKEND_MAPPING = {
    "afplay": _get_afplay_subprocess,
    "alsa": _get_alsa_subprocess,
    "gst_play": _get_gst_play_subprocess,
    "ffplay": _get_ffplay_subprocess,
    "wmplayer": _get_wmplayer_subprocess,
}
AVAILABLE_BACKENDS = list(_BACKEND_MAPPING)

_PLAYSOUND_DEFAULT_BACKEND: str = _select_default_backend()

atexit.register(_remove_cached_downloads, _DOWNLOAD_CACHE)
