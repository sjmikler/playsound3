import time

from playsound3 import AVAILABLE_BACKENDS, playsound
from playsound3.playsound3 import _prepare_path

loc_mp3_3s = "tests/sounds/sample3s.mp3"
web_mp3_3s = "https://samplelib.com/lib/preview/mp3/sample-3s.mp3"
web_wav_3s = "https://samplelib.com/lib/preview/wav/sample-3s.wav"


# Download the files to the local cache
for url in [web_mp3_3s, web_wav_3s]:
    _prepare_path(url)


def test_with_blocking_3s():
    for backend in AVAILABLE_BACKENDS:
        for path in [loc_mp3_3s, web_mp3_3s, web_wav_3s]:
            t0 = time.perf_counter()
            sound = playsound(path, block=True, backend=backend)

            td = time.perf_counter() - t0
            assert not sound.is_alive(), f"backend={backend}, path={path}"
            assert td >= 3.0 and td < 5.0, f"backend={backend}, path={path}"


def test_non_blocking():
    for backend in AVAILABLE_BACKENDS:
        for path in [loc_mp3_3s, web_mp3_3s, web_wav_3s]:
            t0 = time.perf_counter()
            sound = playsound(path, block=False, backend=backend)
            assert sound.is_alive(), f"backend={backend}, path={path}"

            sound.wait()
            td = time.perf_counter() - t0
            assert not sound.is_alive(), f"backend={backend}, path={path}"
            assert td >= 3.0 and td < 5.0, f"backend={backend}, path={path}"


def test_stopping_1s():
    for backend in AVAILABLE_BACKENDS:
        for path in [loc_mp3_3s, web_mp3_3s, web_wav_3s]:
            t0 = time.perf_counter()
            sound = playsound(path, block=False, backend=backend)
            assert sound.is_alive(), f"backend={backend}, path={path}"

            time.sleep(1)
            sound.stop()
            td = time.perf_counter() - t0

            time.sleep(0.05)
            assert not sound.is_alive(), f"backend={backend}, path={path}"
            assert td >= 1.0 and td < 2.0, f"backend={backend}, path={path}"


def test_multiple():
    for backend in AVAILABLE_BACKENDS:
        t0 = time.perf_counter()
        sounds = [
            playsound(loc_mp3_3s, block=False, backend=backend),
            playsound(web_mp3_3s, block=False, backend=backend),
            playsound(web_wav_3s, block=False, backend=backend),
        ]
        for sound in sounds:
            assert sound.is_alive(), f"backend={backend}"
        time.sleep(1)

        for sound in sounds:
            assert sound.is_alive(), f"backend={backend}"
            sound.stop()
        td = time.perf_counter() - t0

        time.sleep(0.05)
        for sound in sounds:
            assert not sound.is_alive(), f"backend={backend}"
        assert td >= 1.0 and td < 2.0, f"backend={backend}"
