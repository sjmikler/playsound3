import atexit
import ctypes
import logging
import platform
import ssl
import subprocess
import tempfile
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from threading import Thread

import certifi

logger = logging.getLogger(__name__)

SYSTEM = platform.system()
DOWNLOAD_CACHE = dict()


class PlaysoundException(Exception):
    pass


def playsound(sound, block: bool = True) -> None:
    """Play a sound file using an audio backend availabile in your system.

    Args:
        sound: Path or URL to the sound file. Can be a string or pathlib.Path.
        block: If True, the function will block execution until the sound finishes playing.
               If False, sound will play in a background thread.
    """
    sound = _prepare_path(sound)

    if SYSTEM == "Linux":
        func = _playsound_gst_play
    elif SYSTEM == "Windows":
        func = _playsound_mci_winmm
    elif SYSTEM == "Darwin":
        func = _playsound_afplay
    else:
        raise PlaysoundException(f"Platform '{SYSTEM}' is not supported")

    if block:
        func(sound)
    else:
        Thread(target=func, args=(sound,), daemon=True).start()


def _download_sound_from_web(link, destination):
    # Identifies itself as a browser to avoid HTTP 403 errors
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64)"}
    request = urllib.request.Request(link, headers=headers)
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(request, context=context) as response, open(destination, "wb") as out_file:
        out_file.write(response.read())


def _prepare_path(sound):
    if sound.startswith(("http://", "https://")):
        # To play file from URL, we download the file first to a temporary location and cache it
        if sound not in DOWNLOAD_CACHE:
            with tempfile.NamedTemporaryFile(delete=False, prefix="playsound3-") as f:
                _download_sound_from_web(sound, f.name)
                DOWNLOAD_CACHE[sound] = f.name
        sound = DOWNLOAD_CACHE[sound]

    path = Path(sound)

    if not path.exists():
        raise PlaysoundException(f"File not found: {sound}")
    return path.absolute().as_posix()


def _playsound_gst_play(sound):
    """Uses gst-play-1.0 utility (built-in Linux)."""
    logger.debug("gst-play-1.0: starting playing %s", sound)
    try:
        subprocess.run(["gst-play-1.0", "--no-interactive", "--quiet", sound], check=True)
    except subprocess.CalledProcessError as e:
        raise PlaysoundException(f"gst-play-1.0 failed to play sound: {e}")
    logger.debug("gst-play-1.0: finishing play %s", sound)


def _playsound_gstreamer_legacy(sound):
    """Play a sound using gstreamer (built-in Linux)."""

    if not sound.startswith("file://"):
        sound = "file://" + urllib.request.pathname2url(sound)

    import gi

    # Silences gi warning
    gi.require_version("Gst", "1.0")

    # GStreamer is included in all Linux distributions
    from gi.repository import Gst

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


def _send_winmm_mci_command(command):
    winmm = ctypes.WinDLL("winmm.dll")
    buffer = ctypes.create_string_buffer(255)
    error_code = winmm.mciSendStringA(ctypes.c_char_p(command.encode()), buffer, 254, 0)
    if error_code:
        logger.error("MCI error code: %s", error_code)
    return buffer.value


def _playsound_mci_winmm(sound):
    """Play a sound utilizing windll.winmm."""

    # Select a unique alias for the sound
    alias = str(uuid.uuid4())
    logger.debug("winmm: starting playing %s", sound)
    _send_winmm_mci_command(f'open "{sound}" type mpegvideo alias {alias}')
    _send_winmm_mci_command(f"play {alias} wait")
    _send_winmm_mci_command(f"close {alias}")
    logger.debug("winmm: finishing play %s", sound)


def _playsound_afplay(sound):
    """Uses afplay utility (built-in macOS)."""
    logger.debug("afplay: starting playing %s", sound)
    try:
        subprocess.run(["afplay", sound], check=True)
    except subprocess.CalledProcessError as e:
        raise PlaysoundException(f"afplay failed to play sound: {e}")
    logger.debug("afplay: finishing play %s", sound)


def _remove_cached_files(cache):
    """Remove all files saved in the cache when the program ends."""
    import os

    for path in cache.values():
        os.remove(path)


atexit.register(_remove_cached_files, DOWNLOAD_CACHE)
