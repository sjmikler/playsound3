from __future__ import annotations

import atexit
import logging
import os
import shutil
import signal
import subprocess
import tempfile
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from importlib.util import find_spec
from pathlib import Path

try:
    from typing import Protocol
except ImportError:
    # Python 3.7 compatibility
    from typing_extensions import Protocol

from playsound3 import backends

logger = logging.getLogger(__name__)


class PlaysoundException(Exception):
    pass


# Windows uses CTRL_C_EVENT, while Unix uses SIGINT
_SIGINT = signal.CTRL_C_EVENT if os.name == "win32" else signal.SIGINT

####################
## DOWNLOAD TOOLS ##
####################

_DOWNLOAD_CACHE: dict[str, str] = {}


def _download_sound_from_web(link: str, destination: Path) -> None:
    # Identifies itself as a browser to avoid HTTP 403 errors
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64)"}
    request = urllib.request.Request(link, headers=headers)

    with urllib.request.urlopen(request) as response, destination.open("wb") as out_file:
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


# Imitating subprocess.Popen
class PopenLike(Protocol):
    def poll(self) -> int | None: ...
    def wait(self) -> int: ...
    def send_signal(self, sig: int) -> None: ...


class SoundBackend(ABC):
    """Abstract class for sound backends."""

    @abstractmethod
    def check(self) -> bool:
        raise NotImplementedError("check() must be implemented.")

    @abstractmethod
    def play(self, sound: str) -> PopenLike:
        raise NotImplementedError("play() must be implemented.")


class Gstreamer(SoundBackend):
    """Gstreamer backend for Linux."""

    def check(self) -> bool:
        try:
            subprocess.run(
                ["gst-play-1.0", "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            return True
        except FileNotFoundError:
            return False

    def play(self, sound: str) -> subprocess.Popen[bytes]:
        return subprocess.Popen(["gst-play-1.0", "--no-interactive", "--quiet", sound])


class Alsa(SoundBackend):
    """ALSA backend for Linux."""

    def check(self) -> bool:
        try:
            subprocess.run(["aplay", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            subprocess.run(["mpg123", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except FileNotFoundError:
            return False

    def play(self, sound: str) -> subprocess.Popen[bytes]:
        suffix = Path(sound).suffix

        if suffix == ".wav":
            return subprocess.Popen(["aplay", "--quiet", sound])
        elif suffix == ".mp3":
            return subprocess.Popen(["mpg123", "-q", sound])
        else:
            raise PlaysoundException(f"ALSA does not support for {suffix} files.")


class Ffplay(SoundBackend):
    """FFplay backend for systems with ffmpeg installed."""

    def check(self) -> bool:
        try:
            subprocess.run(["ffplay", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except FileNotFoundError:
            return False

    def play(self, sound: str) -> subprocess.Popen[bytes]:
        return subprocess.Popen(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", sound])


class Wmplayer(SoundBackend):
    """Windows Media Player backend for Windows."""

    def check(self) -> bool:
        # The recommended way to check for missing library
        if find_spec("pythoncom") is None:
            return False

        try:
            import win32com.client  # type: ignore

            _ = win32com.client.Dispatch("WMPlayer.OCX")
            return True
        except (ImportError, Exception):
            # pywintypes.com_error can be raised, which inherits directly from Exception
            return False

    def play(self, sound: str) -> backends.WmplayerPopen:
        return backends.WmplayerPopen(sound)


class Winmm(SoundBackend):
    """WinMM backend for Windows."""

    def check(self) -> bool:
        try:
            import ctypes

            _ = ctypes.WinDLL("winmm.dll")  # type: ignore
            return True
        except (ImportError, FileNotFoundError, AttributeError):
            return False

    def play(self, sound: str) -> backends.WinmmPopen:
        return backends.WinmmPopen(sound)


class Afplay(SoundBackend):
    """Afplay backend for macOS."""

    def check(self) -> bool:
        # For some reason successful 'afplay -h' returns non-zero code
        # So we must use shutil to test if afplay exists
        return shutil.which("afplay") is not None

    def play(self, sound: str) -> subprocess.Popen[bytes]:
        return subprocess.Popen(["afplay", sound])


class Appkit(SoundBackend):
    """Appkit backend for macOS."""

    def check(self) -> bool:
        try:
            from AppKit import NSSound  # type: ignore # noqa: F401
            from Foundation import NSURL  # type: ignore # noqa: F401

            return True
        except ImportError:
            return False

    def play(self, sound: str) -> backends.AppkitPopen:
        return backends.AppkitPopen(sound)


################
## PLAYSOUND  ##
################

_NO_BACKEND_MESSAGE = """no supported audio backends on this system!
Please create an issue on https://github.com/sjmikler/playsound3/issues."""


def _auto_select_backend() -> str | None:
    if "PLAYSOUND3_BACKEND" in os.environ:
        # Allow users to override the automatic backend choice
        return os.environ["PLAYSOUND3_BACKEND"]

    for backend in _BACKEND_PREFERENCE:
        if backend in AVAILABLE_BACKENDS:
            return backend

    logging.warning(_NO_BACKEND_MESSAGE)
    return None


class Sound:
    """Play subprocess-based sound."""

    def __init__(
        self,
        name: str,
        backend: SoundBackend,
        block: bool,
    ) -> None:
        """Initialize the player and begin playing."""
        self.backend: str = str(type(backend)).lower()
        self.subprocess: PopenLike = backend.play(name)

        if block:
            self.wait()

    def is_alive(self) -> bool:
        return self.subprocess.poll() is None

    def wait(self) -> None:
        self.subprocess.wait()

    def stop(self) -> None:
        if self.is_alive():
            self.subprocess.send_signal(_SIGINT)


def playsound(
    sound: str | Path,
    block: bool = True,
    backend: str | None | SoundBackend | type[SoundBackend] = None,
) -> Sound:
    """Play a sound file using an audio backend availabile in your system.

    Args:
        sound: Path or URL to the sound file. Can be a string or pathlib.Path.
        block: If True, the function will block execution until the sound finishes playing.
               If False, sound will play in background.
        backend: Name of the audio backend to use. Leave None for automatic selection.

    Returns:
        If `block` is True, the function will return None after the sound finishes playing.
        If `block` is False, the function will return the background thread object.

    """
    path = _prepare_path(sound)
    backend = backend or DEFAULT_BACKEND
    if backend is None:
        raise PlaysoundException(_NO_BACKEND_MESSAGE)

    if isinstance(backend, str):
        assert backend in AVAILABLE_BACKENDS, f"Unsupported backend: {backend}"
        backend_obj = _BACKEND_MAP[backend]
    elif isinstance(backend, SoundBackend):
        backend_obj = backend
    elif isinstance(backend, type) and issubclass(backend, SoundBackend):
        backend_obj = backend()
    else:
        raise TypeError(f"invalid backend type '{type(backend)}'")
    return Sound(path, backend_obj, block)


def _remove_cached_downloads(cache: dict[str, str]) -> None:
    """Remove all files saved in the cache when the program ends."""
    for path in cache.values():
        Path(path).unlink()


####################
## INITIALIZATION ##
####################

atexit.register(_remove_cached_downloads, _DOWNLOAD_CACHE)

_BACKEND_PREFERENCE = [
    "gstreamer",  # Linux; should be installed on every Linux
    "ffplay",  # Multi; requires ffmpeg
    "appkit",  # macOS; requires PyObjC dependency
    "afplay",  # macOS; should be installed on every macOS
    "wmplayer",  # Windows; requires pywin32 -- should be workign well on Windows
    "winmm",  # Windows; should be installed on every Windows, but is quirky with variable bitrate MP3s
    "alsa",  # Linux; only supports .mp3 and .wav and might not be installed
]

_BACKEND_MAP: dict[str, SoundBackend] = {
    name.lower(): obj()
    for name, obj in globals().items()
    if isinstance(obj, type) and issubclass(obj, SoundBackend) and obj is not SoundBackend
}

assert sorted(_BACKEND_PREFERENCE) == sorted(_BACKEND_MAP.keys()), "forgot to update _BACKEND_PREFERENCE?"
AVAILABLE_BACKENDS: list[str] = [name for name in _BACKEND_PREFERENCE if _BACKEND_MAP[name].check()]
DEFAULT_BACKEND: str | None = _auto_select_backend()
