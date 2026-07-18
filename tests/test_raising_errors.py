import importlib
import tempfile
import urllib.error
from pathlib import Path

import pytest

from playsound3 import playsound
from playsound3.playsound3 import PlaysoundException

playsound_module = importlib.import_module("playsound3.playsound3")

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


def test_url_query_is_not_used_as_file_suffix(monkeypatch, tmp_path):
    real_named_temporary_file = tempfile.NamedTemporaryFile
    monkeypatch.setattr(
        playsound_module.tempfile,
        "NamedTemporaryFile",
        lambda **kwargs: real_named_temporary_file(dir=tmp_path, **kwargs),
    )
    monkeypatch.setattr(
        playsound_module,
        "_download_sound_from_web",
        lambda _link, destination: destination.write_bytes(b"audio"),
    )

    url = "https://example.com/sample.mp3?token=secret"
    downloaded_path = Path(playsound_module._prepare_path(url))

    assert downloaded_path.suffix == ".mp3"
    playsound_module._DOWNLOAD_CACHE.pop(url)
    downloaded_path.unlink()


def test_failed_download_removes_temporary_file(monkeypatch, tmp_path):
    real_named_temporary_file = tempfile.NamedTemporaryFile
    monkeypatch.setattr(
        playsound_module.tempfile,
        "NamedTemporaryFile",
        lambda **kwargs: real_named_temporary_file(dir=tmp_path, **kwargs),
    )

    def fail_download(_link, _destination):
        raise urllib.error.URLError("download failed")

    monkeypatch.setattr(playsound_module, "_download_sound_from_web", fail_download)

    with pytest.raises(urllib.error.URLError):
        playsound_module._prepare_path("https://example.com/sample.mp3")

    assert list(tmp_path.iterdir()) == []
