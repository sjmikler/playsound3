import time

from playsound3 import playsound
from playsound3.playsound3 import _prepare_path

mp3_3s = "https://samplelib.com/lib/preview/mp3/sample-3s.mp3"
mp3_6s = "https://samplelib.com/lib/preview/mp3/sample-6s.mp3"
wav_3s = "https://samplelib.com/lib/preview/wav/sample-3s.wav"
wav_6s = "https://samplelib.com/lib/preview/wav/sample-6s.wav"

# Download the files to the local cache
for sound in [mp3_3s, mp3_6s, wav_3s, wav_6s]:
    _prepare_path(sound)


def test_dummy():
    pass


def test_with_blocking_3s():
    for path in [mp3_3s, wav_3s]:
        t0 = time.perf_counter()
        playsound(path, block=True)

        td = time.perf_counter() - t0
        assert td >= 3.0 and td < 4.0


def test_with_blocking_6s():
    for path in [mp3_6s, wav_6s]:
        t0 = time.perf_counter()
        playsound(path, block=True)

        td = time.perf_counter() - t0
        assert td >= 6.0 and td < 7.0


def test_non_blocking():
    t0 = time.perf_counter()
    for path in [mp3_3s, wav_3s, mp3_6s, wav_6s]:
        playsound(path, block=False)

    td = time.perf_counter() - t0
    assert td < 1.0


def test_stopping():
    for path in [mp3_3s, wav_3s, mp3_6s, wav_6s]:
        t0 = time.perf_counter()
        sound = playsound(path, block=False)
        time.sleep(1)
        sound.stop()

        td = time.perf_counter() - t0
        assert td >= 1.0 and td < 1.1
