import os
import time

from playsound3 import AVAILABLE_BACKENDS, playsound
from playsound3.playsound3 import _prepare_path

loc_mp3_3s = "tests/sounds/sample3s.mp3"
loc_flc_3s = "tests/sounds/sample3s.flac"
web_wav_3s = "https://samplelib.com/lib/preview/wav/sample-3s.wav"

# Download web files to the local cache
for url in [web_wav_3s]:
    _prepare_path(url)


def get_supported_sounds(backend):
    not_supporting_flac = ["alsa", "winmm"]

    if backend in not_supporting_flac:
        return [loc_mp3_3s, web_wav_3s]
    else:
        return [loc_mp3_3s, loc_flc_3s, web_wav_3s]


CI = os.environ.get("CI", False)


def test_blocking_1():
    for backend in AVAILABLE_BACKENDS:
        for path in get_supported_sounds(backend):
            t0 = time.perf_counter()
            sound = playsound(path, block=True, backend=backend)

            td = time.perf_counter() - t0
            assert not sound.is_alive(), f"backend={backend}, path={path}"
            assert td >= 3.0, f"backend={backend}, path={path}"
            assert CI or td < 5.0, f"backend={backend}, path={path}"


def test_waiting_1():
    for backend in AVAILABLE_BACKENDS:
        for path in get_supported_sounds(backend):
            t0 = time.perf_counter()
            sound = playsound(path, block=False, backend=backend)
            assert sound.is_alive(), f"backend={backend}, path={path}"

            sound.wait()
            td = time.perf_counter() - t0
            assert not sound.is_alive(), f"backend={backend}, path={path}"
            assert td >= 3.0, f"backend={backend}, path={path}"
            assert CI or td < 5.0, f"backend={backend}, path={path}"


def test_waiting_2():
    for backend in AVAILABLE_BACKENDS:
        for path in get_supported_sounds(backend):
            sound = playsound(path, block=False, backend=backend)
            assert sound.is_alive(), f"backend={backend}, path={path}"

            time.sleep(5)
            assert not sound.is_alive(), f"backend={backend}, path={path}"


def test_stopping_1():
    for backend in AVAILABLE_BACKENDS:
        for path in get_supported_sounds(backend):
            t0 = time.perf_counter()
            sound = playsound(path, block=False, backend=backend)
            assert sound.is_alive(), f"backend={backend}, path={path}"

            time.sleep(1)
            sound.stop()
            td = time.perf_counter() - t0

            time.sleep(0.05)
            assert not sound.is_alive(), f"backend={backend}, path={path}"
            assert td >= 0.95 and td < 2.0, f"backend={backend}, path={path}"

            # Stopping again should be a no-op
            sound.stop()
            assert not sound.is_alive(), f"backend={backend}, path={path}"


def test_parallel_1():
    for backend in AVAILABLE_BACKENDS:
        for path in get_supported_sounds(backend):
            t0 = time.perf_counter()
            sounds = [playsound(path, block=False, backend=backend) for _ in range(3)]
            time.sleep(0.05)
            for sound in sounds:
                assert sound.is_alive(), f"backend={backend}"
            time.sleep(1)

            sounds[1].stop()
            time.sleep(0.05)
            assert sounds[0].is_alive(), f"backend={backend}"
            assert sounds[2].is_alive(), f"backend={backend}"
            assert not sounds[1].is_alive(), f"backend={backend}"
            time.sleep(1)

            assert sounds[0].is_alive(), f"backend={backend}"
            assert sounds[2].is_alive(), f"backend={backend}"
            sounds[0].stop()
            sounds[2].stop()
            td = time.perf_counter() - t0

            time.sleep(0.05)
            for sound in sounds:
                assert not sound.is_alive(), f"backend={backend}"
            assert td >= 2.0 and td < 3.0, f"backend={backend}"


def test_parallel_2():
    N_PARALLEL = 10  # Careful - this might be loud!

    for backend in AVAILABLE_BACKENDS:
        for path in get_supported_sounds(backend):
            sounds = [playsound(path, block=False, backend=backend) for _ in range(N_PARALLEL)]

            time.sleep(1)
            for sound in sounds:
                assert sound.is_alive(), f"backend={backend}, path={path}"
            for sound in sounds:
                sound.stop()

            time.sleep(0.05)
            for sound in sounds:
                assert not sound.is_alive(), f"backend={backend}, path={path}"


def test_parallel_3():
    for backend in AVAILABLE_BACKENDS:
        sounds = [playsound(path, block=False, backend=backend) for path in get_supported_sounds(backend)]

        time.sleep(1)
        for sound in sounds:
            assert sound.is_alive(), f"backend={backend}"
        for sound in sounds:
            sound.stop()

        time.sleep(0.05)
        for sound in sounds:
            assert not sound.is_alive(), f"backend={backend}"
