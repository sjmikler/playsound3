from __future__ import annotations

import atexit
import logging
import ssl
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING, Any, Callable

# Satisfy mypy
if TYPE_CHECKING or sys.platform == "win32":
    import ctypes
    import uuid

import certifi

logger = logging.getLogger(__name__)

_DOWNLOAD_CACHE = {}


class PlaysoundException(Exception):
    pass


def playsound(
    sound: str | Path,
    block: bool = True,
    backend: str | None = None,
    daemon: bool = True,
) -> Thread | None:
    """Play a sound file using an audio backend availabile in your system.

    Args:
        sound: Path or URL to the sound file. Can be a string or pathlib.Path.
        block: If True, the function will block execution until the sound finishes playing.
               If False, sound will play in a background thread.
        backend: Name of the audio backend to use. Use None for automatic selection.
        daemon: If True, and `block` is True, the background thread will be a daemon thread.
                This means that the thread will stay alive even after the main program exits.

    Returns:
        If `block` is True, the function will return None after the sound finishes playing.
        If `block` is False, the function will return the background thread object.

    """
    if backend is None:
        _play = _PLAYSOUND_DEFAULT_BACKEND
    elif backend in _BACKEND_MAPPING:
        _play = _BACKEND_MAPPING[backend]
    else:
        raise PlaysoundException(f"Unknown backend: {backend}. Available backends: {', '.join(AVAILABLE_BACKENDS)}")

    path = _prepare_path(sound)
    if block:
        _play(path)
    else:
        thread = Thread(target=_play, args=(path,), daemon=daemon)
        thread.start()
        return thread
    return None


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


def _select_linux_backend() -> Callable[[str], None]:
    """Select the best available audio backend for Linux systems."""
    logger.info("Selecting the best available audio backend for Linux systems.")

    try:
        subprocess.run(["gst-play-1.0", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        logger.info("Using gst-play-1.0 as the audio backend.")
        return _playsound_gst_play
    except FileNotFoundError:
        pass

    try:
        subprocess.run(["ffplay", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        logger.info("Using ffplay as the audio backend.")
        return _playsound_ffplay
    except FileNotFoundError:
        pass

    try:
        subprocess.run(["aplay", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        subprocess.run(["mpg123", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        logger.info("Using aplay and mpg123 as the audio backend.")
        return _playsound_alsa
    except FileNotFoundError:
        pass

    logger.info("No suitable audio backend found.")
    raise PlaysoundException("No suitable audio backend found. Install gstreamer or ffmpeg!")


def _playsound_gst_play(sound: str) -> None:
    """Uses gst-play-1.0 utility (built-in Linux)."""
    logger.debug("gst-play-1.0: starting playing %s", sound)
    try:
        subprocess.run(["gst-play-1.0", "--no-interactive", "--quiet", sound], check=True)
    except subprocess.CalledProcessError as e:
        raise PlaysoundException(f"gst-play-1.0 failed to play sound: {e}")
    logger.debug("gst-play-1.0: finishing play %s", sound)


def _playsound_ffplay(sound: str) -> None:
    """Uses ffplay utility (built-in Linux)."""
    logger.debug("ffplay: starting playing %s", sound)
    try:
        subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", sound],
            check=True,
            stdout=subprocess.DEVNULL,  # suppress output as ffplay prints an unwanted newline
        )
    except subprocess.CalledProcessError as e:
        raise PlaysoundException(f"ffplay failed to play sound: {e}")
    logger.debug("ffplay: finishing play %s", sound)


def _playsound_alsa(sound: str) -> None:
    """Play a sound using alsa and mpg123 (built-in Linux)."""
    suffix = Path(sound).suffix
    if suffix == ".wav":
        logger.debug("alsa: starting playing %s", sound)
        try:
            subprocess.run(["aplay", "--quiet", sound], check=True)
        except subprocess.CalledProcessError as e:
            raise PlaysoundException(f"aplay failed to play sound: {e}")
        logger.debug("alsa: finishing play %s", sound)
    elif suffix == ".mp3":
        logger.debug("mpg123: starting playing %s", sound)
        try:
            subprocess.run(["mpg123", "-q", sound], check=True)
        except subprocess.CalledProcessError as e:
            raise PlaysoundException(f"mpg123 failed to play sound: {e}")
        logger.debug("mpg123: finishing play %s", sound)
    else:
        raise PlaysoundException(f"Backend not supported for {suffix} files")


def _playsound_gst_legacy(sound: str) -> None:
    """Play a sound using gstreamer (built-in Linux)."""

    if not sound.startswith("file://"):
        sound = "file://" + urllib.request.pathname2url(sound)

    try:
        import gi
    except ImportError:
        raise PlaysoundException("PyGObject not found. Run 'pip install pygobject'")

    # Silences gi warning
    gi.require_version("Gst", "1.0")

    try:
        # Gst will be available only if GStreamer is installed
        from gi.repository import Gst
    except ImportError:
        raise PlaysoundException("GStreamer not found. Install GStreamer on your system")

    Gst.init(None)

    playbin = Gst.ElementFactory.make("playbin", "playbin")
    playbin.props.uri = sound

    logger.debug("gstreamer: starting playing %s", sound)
    set_result = playbin.set_state(Gst.State.PLAYING)
    if set_result != Gst.StateChangeReturn.ASYNC:
        raise PlaysoundException("playbin.set_state returned " + repr(set_result))
    bus = playbin.get_bus()
    try:
        bus.poll(Gst.MessageType.EOS, Gst.CLOCK_TIME_NONE)
    finally:
        playbin.set_state(Gst.State.NULL)
    logger.debug("gstreamer: finishing play %s", sound)


def _send_winmm_mci_command(command: str) -> Any:
    if sys.platform != "win32":
        raise RuntimeError("WinMM is only available on Windows systems.")
    winmm = ctypes.WinDLL("winmm.dll")
    buffer = ctypes.create_unicode_buffer(255)  # Unicode buffer for wide characters
    error_code = winmm.mciSendStringW(ctypes.c_wchar_p(command), buffer, 254, 0)  # Use mciSendStringW
    if error_code:
        logger.error("MCI error code: %s", error_code)
    return buffer.value


def _playsound_mci_winmm(sound: str) -> None:
    """Play a sound utilizing windll.winmm."""
    if sys.platform != "win32":
        raise RuntimeError("WinMM is only available on Windows systems.")
    # Select a unique alias for the sound
    alias = str(uuid.uuid4())
    logger.debug("winmm: starting playing %s", sound)
    _send_winmm_mci_command(f'open "{sound}" type mpegvideo alias {alias}')
    _send_winmm_mci_command(f"play {alias} wait")
    _send_winmm_mci_command(f"close {alias}")
    logger.debug("winmm: finishing play %s", sound)


def _playsound_afplay(sound: str) -> None:
    """Uses afplay utility (built-in macOS)."""
    logger.debug("afplay: starting playing %s", sound)
    try:
        subprocess.run(["afplay", sound], check=True)
    except subprocess.CalledProcessError as e:
        raise PlaysoundException(f"afplay failed to play sound: {e}")
    logger.debug("afplay: finishing play %s", sound)


def _initialize_default_backend() -> Callable[[str], None]:
    if sys.platform == "win32":
        return _playsound_mci_winmm
    if sys.platform == "darwin":
        return _playsound_afplay
    # Linux version serves as the fallback
    # because tools like gstreamer and ffmpeg could be installed on unrecognized systems
    return _select_linux_backend()


def _remove_cached_downloads(cache: dict[str, str]) -> None:
    """Remove all files saved in the cache when the program ends."""
    for path in cache.values():
        Path(path).unlink()


# ######################## #
# PLAYSOUND INITIALIZATION #
# ######################## #

_PLAYSOUND_DEFAULT_BACKEND = _initialize_default_backend()
atexit.register(_remove_cached_downloads, _DOWNLOAD_CACHE)

_BACKEND_MAPPING = {
    "afplay": _playsound_afplay,
    "alsa_mpg123": _playsound_alsa,
    "ffplay": _playsound_ffplay,
    "gst_play": _playsound_gst_play,
    "gst_legacy": _playsound_gst_legacy,
    "mci_winmm": _playsound_mci_winmm,
}

AVAILABLE_BACKENDS = list(_BACKEND_MAPPING.keys())
