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
        print(f"Testing backend: {backend}")

        for path in [loc_mp3_3s, web_mp3_3s, web_wav_3s]:
            print(f"Testing sound: {path}")

            t0 = time.perf_counter()
            sound = playsound(path, block=True, backend=backend)

            td = time.perf_counter() - t0
            assert td >= 3.0 and td < 3.5
            assert not sound.is_alive()


def test_non_blocking():
    for backend in AVAILABLE_BACKENDS:
        print(f"Testing backend: {backend}")

        t0 = time.perf_counter()
        for path in [loc_mp3_3s, web_mp3_3s, web_wav_3s]:
            print(f"Testing sound: {path}")
            sound = playsound(path, block=False, backend=backend)

            td = time.perf_counter() - t0
            assert td < 0.5
            assert sound.is_alive()

            sound.wait()
            assert not sound.is_alive()


def test_stopping_1s():
    for backend in AVAILABLE_BACKENDS:
        print(f"Testing backend: {backend}")

        for path in [loc_mp3_3s, web_mp3_3s, web_wav_3s]:
            print(f"Testing sound: {path}")

            t0 = time.perf_counter()
            sound = playsound(path, block=False, backend=backend)
            assert sound.is_alive()

            time.sleep(1)
            sound.stop()

            time.sleep(0.05)
            assert not sound.is_alive()

            td = time.perf_counter() - t0
            assert td >= 1.0 and td < 1.5


def test_stopping_2s():
    for backend in AVAILABLE_BACKENDS:
        print(f"Testing backend: {backend}")

        for path in [loc_mp3_3s, web_mp3_3s, web_wav_3s]:
            print(f"Testing sound: {path}")

            t0 = time.perf_counter()
            sound = playsound(path, block=False, backend=backend)
            assert sound.is_alive()

            time.sleep(2)
            sound.stop()

            time.sleep(0.05)
            assert not sound.is_alive()

            td = time.perf_counter() - t0
            assert td >= 2.0 and td < 2.5
