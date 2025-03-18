import urllib.error

import pytest

from playsound3 import playsound
from playsound3.playsound3 import PlaysoundException

valid = "tests/sounds/sample3s.mp3"


def test_invalid_sound_file():
    with pytest.raises(PlaysoundException):
        playsound("invalid.mp3")


def test_non_existent_file():
    with pytest.raises(PlaysoundException):
        playsound("non_existent.mp3")


def test_invalid_backend():
    with pytest.raises(PlaysoundException):
        playsound(valid, backend="invalid_backend")


def test_playsound_from_url():
    url = "https://wrong-url.com/wrong-audio.mp3"
    with pytest.raises(urllib.error.URLError):
        playsound(url)
