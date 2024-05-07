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
from playsound3 import playsound

playsound("/path/to/sound/file.mp3")

# or use directly on URLs
playsound("http://url/to/sound/file.mp3")
```

## Documentation

The `playsound3` module contains a single function named `playsound`:

```python
def playsound(sound, block=True, backend=None) -> None:
    """Play a sound file using an audio backend availabile in your system.

    Args:
        sound: Path or URL to the sound file. Can be a string or pathlib.Path.
        block: If True, the function will block execution until the sound finishes playing.
               If False, sound will play in a background thread.
        backend: Name of the audio backend to use. Use None for automatic selection.
    """
    ...
```

It requires one argument: `sound` - the path to the file with the sound you'd like to play.
This should be a local file or a URL.
There's an optional second argument: `block` which is set to `True` by default.
Setting it to `False` makes the function run asynchronously.
You can manually specify a backend by passing its name as the third argument.
You can browse available backends by using `playsound3.AVAILABLE_BACKENDS`.
It is recommended to use the default value of `None` to let the library choose the best backend available.

## Supported systems

* **Linux** using one of the below backends, whichever is available:
    * GStreamer
    * FFmpeg
    * aplay for .wav and mpg123 .mp3
* **Windows** using winmm.dll (built-in on Windows)
* **OS X** using afplay utility (built-in on OS X)
