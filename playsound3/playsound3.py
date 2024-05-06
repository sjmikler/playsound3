import os
import logging
from urllib.request import pathname2url
from platform import system
from threading import Thread
import random

logger = logging.getLogger(__name__)

SYSTEM = system()


class PlaysoundException(Exception):
    pass


def playsound(sound, block=False):
    if SYSTEM == "Linux":
        _playsound_gstreamer(sound, block)
    elif SYSTEM == "Windows":
        _playsound_winmm(sound, block)
    else:
        raise PlaysoundException(f"Platform '{SYSTEM}' is not supported")


def _playsound_gstreamer(sound, block):
    """Play a sound using GStreamer.

    Inspired by:
    https://gstreamer.freedesktop.org/documentation/tutorials/playback/playbin-usage.html
    """
    import gi

    # Silences gi warning
    gi.require_version("Gst", "1.0")

    # GStreamer is included in all Linux distributions
    from gi.repository import Gst

    Gst.init(None)

    playbin = Gst.ElementFactory.make("playbin", "playbin")
    if not sound.startswith(("http://", "https://", "file://")):
        path = os.path.abspath(sound)
        if not os.path.exists(path):
            raise PlaysoundException(f"File not found: {path}")
        sound = "file://" + pathname2url(path)
    playbin.props.uri = sound

    logger.debug("gstreamer: starting playing %s", sound)
    set_result = playbin.set_state(Gst.State.PLAYING)
    if set_result != Gst.StateChangeReturn.ASYNC:
        raise PlaysoundException("playbin.set_state returned " + repr(set_result))
    if block:
        bus = playbin.get_bus()
        try:
            bus.poll(Gst.MessageType.EOS, Gst.CLOCK_TIME_NONE)
        finally:
            playbin.set_state(Gst.State.NULL)
    logger.debug("gstreamer: finishing play %s", sound)


def _playsound_winmm(sound, block):
    """Play a sound utilizing windll.winmm

    Inspired by
    https://github.com/michaelgundlach/mp3play
    """
    if block is False:
        thread = Thread(target=_playsound_winmm, args=(sound, True))
        thread.start()
        return
    
    import ctypes
    
    # Load the winmm library
    winmm = ctypes.WinDLL('winmm.dll')
    
    def mciSendString(command):
        buffer = ctypes.create_string_buffer(255)
        error_code = winmm.mciSendStringA(ctypes.c_char_p(command.encode()), buffer, 254, 0)
        if error_code:
            print("Error code:", error_code)
        return buffer.value
    
    # Play a sound
    alias = f"alias"
    mciSendString(f"open \"{sound}\" type mpegvideo alias {alias}")
    mciSendString(f"play {alias} wait")
    mciSendString(f"close {alias}")


if __name__ == "__main__":
    playsound("test_media/Damonte.mp3", block=True)
