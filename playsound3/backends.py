from __future__ import annotations

import time
import uuid
from threading import Thread
from typing import Any

WAIT_TIME: float = 0.02


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
            raise PlaysoundException("Install 'pywin32' to use the 'wmplayer' backend.") from e

        # Create the Windows Media Player COM object
        wmp = win32com.client.Dispatch(
            "WMPlayer.OCX",
            pythoncom.CoInitialize(),
        )
        wmp.settings.autoStart = True  # Ensure playback starts automatically

        # Set the URL to your MP3 file
        wmp.URL = sound
        wmp.controls.play()  # Start playback

        while wmp.playState != 1 and self._playing:  # playState 1 indicates stopped
            pythoncom.PumpWaitingMessages()  # Process COM events
            time.sleep(WAIT_TIME)

        wmp.controls.stop()
        self._playing = False

    def send_signal(self, sig: int) -> None:
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
        self._playing: bool = True
        self.alias: str | None = None
        self.thread = Thread(target=self._play, args=(sound,), daemon=True)
        self.thread.start()

    def _send_winmm_mci_command(self, command: str) -> str:
        try:
            import ctypes
        except ImportError as e:
            raise PlaysoundException("Install 'ctypes' to use the 'winmm' backend") from e

        winmm = ctypes.WinDLL("winmm.dll")  # type: ignore
        buffer = ctypes.create_unicode_buffer(255)  # Unicode buffer for wide characters
        error_code = winmm.mciSendStringW(ctypes.c_wchar_p(command), buffer, 254, 0)

        if error_code:
            raise RuntimeError(f"winmm was not able to play the file! MCI error code: {error_code}")
        return buffer.value

    def _play(self, sound: str) -> None:
        """Play a sound utilizing windll.winmm."""
        # Select a unique alias for the sound
        self.alias = str(uuid.uuid4())
        self._send_winmm_mci_command(f'open "{sound}" type mpegvideo alias {self.alias}')
        self._send_winmm_mci_command(f"play {self.alias}")

        while self._playing:
            time.sleep(WAIT_TIME)
            status = self._send_winmm_mci_command(f"status {self.alias} mode")
            if status != "playing":
                break

        self._send_winmm_mci_command(f"stop {self.alias}")
        self._send_winmm_mci_command(f"close {self.alias}")
        self._playing = False

    def send_signal(self, sig: int) -> None:
        self._playing = False

    def poll(self) -> int | None:
        """None if sound is playing, integer if not."""
        return None if self._playing else 0

    def wait(self) -> int:
        self.thread.join()
        return 0


class AppkitPopen:
    """Popen-like object for AppKit NSSound backend."""

    def __init__(self, sound: str):
        self._playing: bool = True
        self.thread = Thread(target=self._play, args=(sound,), daemon=True)
        self.thread.start()

    def _play(self, sound: str) -> None:
        try:
            from AppKit import NSSound  # type: ignore
            from Foundation import NSURL  # type: ignore
        except ImportError as e:
            raise PlaysoundException("Install 'PyObjC' to use 'appkit' backend.") from e

        nsurl: Any = NSURL.fileURLWithPath_(sound)
        nssound = NSSound.alloc().initWithContentsOfURL_byReference_(nsurl, True)
        while self._playing and nssound.isPlaying:
            time.sleep(WAIT_TIME)

        nssound.stop()
        self._playing = False

    def send_signal(self, sig: int) -> None:
        self._playing = False

    def poll(self) -> int | None:
        """None if sound is playing, integer if not."""
        return None if self._playing else 0

    def wait(self) -> int:
        self.thread.join()
        return 0
