import ctypes
import logging
import os
import subprocess
import uuid
from pathlib import Path
from platform import system
from threading import Thread
from urllib.request import pathname2url

logger = logging.getLogger(__name__)

SYSTEM = system()


class PlaysoundException(Exception):
    pass


def playsound(sound, block=True):
    sound = _prepare_path(sound)

    if SYSTEM == "Linux":
        func = _playsound_gstreamer
    elif SYSTEM == "Windows":
        func = _playsound_winmm
    elif SYSTEM == "Darwin":
        func = _playsound_afplay
    else:
        raise PlaysoundException(f"Platform '{SYSTEM}' is not supported")

    if block:
        func(sound)
    else:
        t = Thread(target=func, args=(sound,)).start()


def _prepare_path(sound):
    path = Path(sound)

    if not path.exists():
        raise PlaysoundException(f"File not found: {sound}")

    return path.absolute().as_posix()


def _playsound_gstreamer(sound):
    """Play a sound using gstreamer (built-in Linux)."""

    if not sound.startswith(("http://", "https://", "file://")):
        path = os.path.abspath(sound)
        if not os.path.exists(path):
            raise PlaysoundException(f"File not found: {path}")
        sound = "file://" + pathname2url(path)

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
        logger.error("Error code: %s", error_code)
    return buffer.value


def _playsound_winmm(sound):
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
