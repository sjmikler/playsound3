from __future__ import annotations

import logging
import sys
import time
import uuid
from threading import Thread

logger = logging.getLogger(__name__)


class PlaysoundException(Exception):
    pass


class WmplayerPopen:
    """Popen-like object for Wmplayer backend."""

    def __init__(self, sound: str):
        self._playing: bool = True
        self.thread = Thread(target=self._play, args=(sound,), daemon=True)
        self.thread.start()

    def _play(self, sound: str) -> None:
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

            if not self._playing:
                logger.debug("wmplayer: stop play %s", sound)
                wmp.controls.stop()
                break

        self._playing = False
        logger.debug("wmplayer: finish play %s", sound)

    def send_signal(self, _sig: int) -> None:
        self._playing = False

    def poll(self) -> int | None:
        """None if sound is playing, integer if not."""
        return None if self._playing else 0

    def wait(self) -> int:
        self.thread.join()
        return 0


class WinmmPopen:
    """Popen-like object for Winmm backend."""

    def __init__(self, sound: str):
        self.alias: str | None = None
        self.thread = Thread(target=self._play, args=(sound,), daemon=True)
        self.thread.start()

    def _send_winmm_mci_command(self, command: str) -> None:
        try:
            import ctypes
        except ImportError as e:
            raise PlaysoundException("ctypes required to use the 'winmm' backend") from e

        if sys.platform != "win32":
            raise RuntimeError("WinMM is only available on Windows systems.")
        winmm = ctypes.WinDLL("winmm.dll")
        buffer = ctypes.create_unicode_buffer(255)  # Unicode buffer for wide characters
        error_code = winmm.mciSendStringW(ctypes.c_wchar_p(command), buffer, 254, 0)  # Use mciSendStringW

        if error_code:
            logger.error("MCI error code: %s", error_code)
            raise RuntimeError("WinMM was not able to play the file!")

    def _playsound_mci_winmm(self, sound: str) -> None:
        """Play a sound utilizing windll.winmm."""
        if sys.platform != "win32":
            raise RuntimeError("WinMM is only available on Windows systems.")
        # Select a unique alias for the sound
        self.alias = str(uuid.uuid4())
        logger.debug("winmm: starting playing %s", sound)
        self._send_winmm_mci_command(f'open "{sound}" type mpegvideo alias {self.alias}')
        self._send_winmm_mci_command(f"play {self.alias} wait")
        # _send_winmm_mci_command(f"close {alias}")
        logger.debug("winmm: finishing play %s", sound)

    def _play(self, sound: str) -> None:
        logger.debug("MCI: start play %s", sound)
        self._playsound_mci_winmm(sound)
        logger.debug("wmplayer: finish play %s", sound)

    def send_signal(self, _sig: int) -> None:
        """Stop the currently playing sound."""
        if self.alias is None:
            return
        self._send_winmm_mci_command(f"stop {self.alias}")  # Stop playback
        self._send_winmm_mci_command(f"close {self.alias}")  # Close the audio file
        print(f"winmm: Stopped playing {self.alias}")
        self.alias = None  # Reset the alias

    def poll(self) -> int | None:
        """None if sound is playing, integer if not."""
        return 0 if self.alias is None else None

    def wait(self) -> int:
        self.thread.join()
        return 0
