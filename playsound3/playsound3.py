import os
import logging
from urllib.request import pathname2url
from platform import system

logger = logging.getLogger(__name__)

SYSTEM = system()


class PlaysoundException(Exception):
    pass


def playsound(sound, block=False):
    if SYSTEM == "Linux":
        _playsound_gstreamer(sound, block)
    elif SYSTEM == "Windows":
        _playsound_windll(sound, block)
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


def _playsound_windll(sound, block):
    """Play a sound utilizing windll.winmm

    Inspired by
    https://github.com/michaelgundlach/mp3play
    """
    from ctypes import create_unicode_buffer, windll, wintypes

    windll.winmm.mciSendStringW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.UINT, wintypes.HANDLE]
    windll.winmm.mciGetErrorStringW.argtypes = [wintypes.DWORD, wintypes.LPWSTR, wintypes.UINT]

    def winCommand(*command):
        bufLen = 600
        buf = create_unicode_buffer(bufLen)
        command = " ".join(command)

        # use widestring version of the function
        errorCode = int(windll.winmm.mciSendStringW(command, buf, bufLen - 1, 0))
        if errorCode:
            errorBuffer = create_unicode_buffer(bufLen)

            # use widestring version of the function
            windll.winmm.mciGetErrorStringW(errorCode, errorBuffer, bufLen - 1)
            raise PlaysoundException(f"Error {errorCode} for command {command}, {errorBuffer.value}")
        return buf.value

    try:
        logger.debug("windll: starting playing %s", sound)
        winCommand(f"open {sound}")
        wait_cmd = " wait" if block else ""
        winCommand(f"play {sound}{wait_cmd}")
        logger.debug("windll: finished playing %s", sound)
    finally:
        try:
            winCommand(f"close {sound}")
        except PlaysoundException:
            logger.warning("Failed to close the file: %s", sound)
            # If it fails, there's nothing more that can be done...
            pass


if __name__ == "__main__":
    playsound("test_media/Damonte.mp3", block=True)
