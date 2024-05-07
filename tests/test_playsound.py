import time

from playsound3 import playsound

MP3_3s = "https://samplelib.com/lib/preview/mp3/sample-3s.mp3"
MP3_6s = "https://samplelib.com/lib/preview/mp3/sample-6s.mp3"
WAV_3s = "https://samplelib.com/lib/preview/wav/sample-3s.wav"
WAV_6s = "https://samplelib.com/lib/preview/wav/sample-6s.wav"


def test_dummy():
    pass


def test_with_blocking():
    for sound in [MP3_3s, WAV_3s]:
        t0 = time.time()
        playsound(sound, block=True)
        assert time.time() - t0 >= 3.0
    for sound in [MP3_6s, WAV_6s]:
        t0 = time.time()
        playsound(sound, block=True)
        assert time.time() - t0 >= 6.0


def test_non_blocking():
    t0 = time.time()
    for sound in [MP3_3s, WAV_3s, MP3_6s, WAV_6s]:
        playsound(sound, block=False)
    assert time.time() - t0 < 1.0
