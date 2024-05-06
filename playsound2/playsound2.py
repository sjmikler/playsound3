import os
import logging
from urllib.request import pathname2url
from platform import system

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM = system()


def playsound(sound, block=False):
    _playsound(sound, block=block)


def _playsound(*args, **kwds):
    raise Exception("Function not initialized yet!")


def _initialize_playsound():
    global _playsound

    system_to_func = {
        "Windows": _playsoundWin,
        "Linux": _playsoundNix,

        # OSX is temporarily not supported
        # "Darwin": _playsoundOSX,
    }

    _playsound = system_to_func.get(SYSTEM, None)
    assert _playsound is not None, f"Unsupported system: {SYSTEM}"


class PlaysoundException(Exception):
    pass


def _canonicalizePath(path):
    """
    Support passing in a pathlib.Path-like object by converting to str.
    """
    import sys

    if sys.version_info[0] >= 3:
        return str(path)
    else:
        # On earlier Python versions, str is a byte string, so attempting to
        # convert a unicode string to str will fail. Leave it alone in this case.
        return path


def _playsoundWin(sound, block):
    """
    Utilizes windll.winmm. Tested and known to work with MP3 and WAVE on
    Windows 7 with Python 2.7. Probably works with more file formats.
    Probably works on Windows XP thru Windows 10. Probably works with all
    versions of Python.

    Inspired by (but not copied from) Michael Gundlach <gundlach@gmail.com>'s mp3play:
    https://github.com/michaelgundlach/mp3play

    I never would have tried using windll.winmm without seeing his code.
    """
    sound = '"' + _canonicalizePath(sound) + '"'

    from ctypes import create_unicode_buffer, windll, wintypes

    windll.winmm.mciSendStringW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.UINT, wintypes.HANDLE]
    windll.winmm.mciGetErrorStringW.argtypes = [wintypes.DWORD, wintypes.LPWSTR, wintypes.UINT]

    def winCommand(*command):
        bufLen = 600
        buf = create_unicode_buffer(bufLen)
        command = " ".join(command)
        errorCode = int(
            windll.winmm.mciSendStringW(command, buf, bufLen - 1, 0)
        )  # use widestring version of the function
        if errorCode:
            errorBuffer = create_unicode_buffer(bufLen)
            windll.winmm.mciGetErrorStringW(
                errorCode, errorBuffer, bufLen - 1
            )  # use widestring version of the function
            exceptionMessage = (
                "\n    Error " + str(errorCode) + " for command:" "\n        " + command + "\n    " + errorBuffer.value
            )
            logger.error(exceptionMessage)
            raise PlaysoundException(exceptionMessage)
        return buf.value

    try:
        logger.debug("Starting")
        winCommand("open {}".format(sound))
        winCommand("play {}{}".format(sound, " wait" if block else ""))
        logger.debug("Returning")
    finally:
        try:
            winCommand("close {}".format(sound))
        except PlaysoundException:
            logger.warning("Failed to close the file: {}".format(sound))
            # If it fails, there's nothing more that can be done...
            pass


def _handlePathOSX(sound):
    sound = _canonicalizePath(sound)

    if "://" not in sound:
        if not sound.startswith("/"):
            sound = os.getcwd() + "/" + sound
        sound = "file://" + sound

    try:
        # Don't double-encode it.
        sound.encode("ascii")
        return sound.replace(" ", "%20")
    except UnicodeEncodeError:
        try:
            from urllib.parse import quote  # Try the Python 3 import first...
        except ImportError:
            from urllib import quote  # Try using the Python 2 import before giving up entirely...

        parts = sound.split("://", 1)
        return parts[0] + "://" + quote(parts[1].encode("utf-8")).replace(" ", "%20")


# def _playsoundOSX(sound, block):
#     """
#     Utilizes AppKit.NSSound. Tested and known to work with MP3 and WAVE on
#     OS X 10.11 with Python 2.7. Probably works with anything QuickTime supports.
#     Probably works on OS X 10.5 and newer. Probably works with all versions of
#     Python.
#
#     Inspired by (but not copied from) Aaron's Stack Overflow answer here:
#     http://stackoverflow.com/a/34568298/901641
#
#     I never would have tried using AppKit.NSSound without seeing his code.
#     """
#     try:
#         from AppKit import NSSound
#     except ImportError:
#         raise ImportError("playsound on OSX requires AppKit. Install PyObjC.")
#
#     from time import sleep
#
#     from Foundation import NSURL
#
#     sound = _handlePathOSX(sound)
#     url = NSURL.URLWithString_(sound)
#     if not url:
#         raise PlaysoundException("Cannot find a sound with filename: " + sound)
#
#     for i in range(5):
#         nssound = NSSound.alloc().initWithContentsOfURL_byReference_(url, True)
#         if nssound:
#             break
#         else:
#             logger.debug("Failed to load sound, although url was good... " + sound)
#     else:
#         raise PlaysoundException("Could not load sound with filename, although URL was good... " + sound)
#     nssound.play()
#
#     if block:
#         sleep(nssound.duration())


def _playsoundNix(sound, block):
    """Play a sound using GStreamer.

    Inspired by this:
    https://gstreamer.freedesktop.org/documentation/tutorials/playback/playbin-usage.html
    """
    sound = _canonicalizePath(sound)

    # pathname2url escapes non-URL-safe characters

    import gi

    gi.require_version("Gst", "1.0")
    from gi.repository import Gst

    Gst.init(None)

    playbin = Gst.ElementFactory.make("playbin", "playbin")
    if sound.startswith(("http://", "https://")):
        playbin.props.uri = sound
    else:
        path = os.path.abspath(sound)
        if not os.path.exists(path):
            raise PlaysoundException("File not found: {}".format(path))
        playbin.props.uri = "file://" + pathname2url(path)

    set_result = playbin.set_state(Gst.State.PLAYING)
    if set_result != Gst.StateChangeReturn.ASYNC:
        raise PlaysoundException("playbin.set_state returned " + repr(set_result))

    # FIXME: use some other bus method than poll() with block=False
    # https://lazka.github.io/pgi-docs/#Gst-1.0/classes/Bus.html
    logger.debug("Starting play")
    if block:
        bus = playbin.get_bus()
        try:
            bus.poll(Gst.MessageType.EOS, Gst.CLOCK_TIME_NONE)
        finally:
            playbin.set_state(Gst.State.NULL)

    logger.debug("Finishing play")


# Initialize the module-level playsound variable after all variables have been initialize
_initialize_playsound()

if __name__ == "__main__":
    playsound("test_media/Damonte.mp3", block=True)
    # playsound("test_media/Damonte.mp3", block=False)
    playsound("test_media/Damonte.mp3", block=True)
