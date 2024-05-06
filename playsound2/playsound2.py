import os
import logging
from urllib.request import pathname2url
from platform import system

logger = logging.getLogger(__name__)

SYSTEM = system()


class PlaysoundException(Exception):
    pass


def playsound(sound, block=False):
    """Play a sound using GStreamer.

    Inspired by this:
    https://gstreamer.freedesktop.org/documentation/tutorials/playback/playbin-usage.html
    """
    import gi
    gi.require_version('Gst', '1.0')  # Silences gi warning

    from gi.repository import Gst
    Gst.init(None)

    playbin = Gst.ElementFactory.make("playbin", "playbin")
    if not sound.startswith(("http://", "https://", "file://")):
        path = os.path.abspath(sound)
        if not os.path.exists(path):
            raise PlaysoundException(f"File not found: {path}")
        sound = "file://" + pathname2url(path)
    playbin.props.uri = sound

    logger.debug("Starting playing %s", sound)
    set_result = playbin.set_state(Gst.State.PLAYING)
    if set_result != Gst.StateChangeReturn.ASYNC:
        raise PlaysoundException("playbin.set_state returned " + repr(set_result))
    if block:
        bus = playbin.get_bus()
        try:
            bus.poll(Gst.MessageType.EOS, Gst.CLOCK_TIME_NONE)
        finally:
            playbin.set_state(Gst.State.NULL)
    logger.debug("Finishing play %s", sound)


if __name__ == "__main__":
    playsound("test_media/Damonte.mp3", block=True)
    # playsound("test_media/Damonte.mp3", block=False)
    playsound("test_media/Damonte.mp3", block=True)
