import time

from playsound3 import AVAILABLE_BACKENDS, playsound

wav = "tests/sounds/звук 音 聲音.wav"


def test_with_blocking():
    for backend in AVAILABLE_BACKENDS:
        print(f"Testing backend: {backend}")

        sound = playsound(wav, block=True, backend=backend)
        assert not sound.is_alive()


def test_non_blocking():
    for backend in AVAILABLE_BACKENDS:
        print(f"Testing backend: {backend}")

        sound = playsound(wav, block=False, backend=backend)
        time.sleep(0.05)
        assert sound.is_alive()

        sound.wait()
        assert not sound.is_alive()
