> **Version 3.0.0** \
> New functionality: interrupt sounds by calling `sound.stop()`

# playsound3

[![PyPi version](https://img.shields.io/badge/dynamic/json?label=latest&query=info.version&url=https%3A%2F%2Fpypi.org%2Fpypi%2Fplaysound3%2Fjson)](https://pypi.org/project/playsound3)
[![PyPI license](https://img.shields.io/badge/dynamic/json?label=license&query=info.license&url=https%3A%2F%2Fpypi.org%2Fpypi%2Fplaysound3%2Fjson)](https://pypi.org/project/playsound3)

Cross platform library to play sound files in Python.

## Installation

Install via pip:

```
pip install playsound3
```

## Quick Start

Once installed, you can use the playsound function to play sound files:

```python
import time
from playsound3 import playsound

# Play sounds from disk
playsound("/path/to/sound/file.mp3")

# or play sounds from the internet
sound = playsound("http://url/to/sound/file.mp3")

# You can also play sounds in the background
playsound("/path/to/sound/file.mp3", block=False)

time.sleep(1)
sound.stop()  # And stop them whenever you like

```

## Documentation

The `playsound3` module contains a single function named `playsound`:

```python
def playsound(
    sound: str | Path,
    block: bool = True,
    backend: str | None = None,
) -> Sound:
    """Play a sound file using an audio backend availabile in your system.

    Args:
        sound: Path or URL to the sound file. Can be a string or pathlib.Path.
        block: If True, the function will block execution until the sound finishes playing.
               If False, sound will play in a background thread.
        backend: Name of the audio backend to use. Use None for automatic selection.

    Returns:
        If `block` is True, the function will return None after the sound finishes playing.
        If `block` is False, the function will return the background thread object.

    """
    ...
```

Only one argument is required: `sound`.
This is the path to the file with the sound you'd like to play.
This should be a local file or a URL.

There's an optional second argument: `block` which is `True` by default.
Setting it to `False` will make the sound play in the background.

You can manually specify a backend by passing its name as the third argument.
You can browse available backends by using `playsound3.AVAILABLE_BACKENDS`.
It is recommended to use the default value of `None` to let the library choose the best backend available.

A `Sound` object is returned. It defines two methods:

* `sound.is_alive()` <- returns True if the sound is still playing
* `sound.wait()` <- blocks until the sound finishes playing
* `sound.stop()` <- stops the sound

## Supported systems

* **Linux** using one of the below backends, whichever is available:
    * GStreamer
    * FFmpeg
    * aplay for .wav and mpg123 .mp3
* **Windows** using wmplayer utility (built-in on Windows)
* **macOS** using afplay utility (built-in on macOS)

## Fork information

This repository was originally forked from [playsound](https://github.com/TaylorSMarks/playsound) library created by Taylor Marks. The original library is unfortunately not maintained anymore and doesn't accept pull requests. This library: `playsound3` is a major rewrite of the original, including its own set of tests hosted using GitHub Actions.

Compared to the original, library `playsound3`:

* Drops support for Python 2
* Adheres to the PEP standards
* Offers multiple backends with a fallback mechanism if the default backend is not available
* Supports extra features
* Accepts contributions
