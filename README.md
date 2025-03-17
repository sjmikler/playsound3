> **Version 3.0.0**
>
> New functionalities:
> * stop sounds by calling `sound.stop()`
> * check if sound is still playing with `sound.is_alive()`

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

After installation, playing sounds is simple:

```python
from playsound3 import playsound

# Play sounds from disk
playsound("/path/to/sound/file.mp3")

# or play sounds from the internet.
playsound("http://url/to/sound/file.mp3")

# You can play sounds in the background
sound = playsound("/path/to/sound/file.mp3", block=False)

# and check if they are still playing
if sound.is_alive():
    print("Sound is still playing!")

# and stop them whenever you like.
sound.stop()
```

## Reference

### playsound

```python
def playsound(
    sound: str | Path,
    block: bool = True,
    backend: str | None | SoundBackend | type[SoundBackend] = None,
) -> Sound
```

`sound` (required) \
The audio file you want to play (local or URL).

`block` (optional, default=`True`)\
Determines whether the sound plays synchronously (blocking) or asynchronously (background).

`backend` (optional, default=`None`) \
Specify which audio backend to use.
If `None`, the best backend is determined automatically.

To see a list of backends supported by your system:

```python
from playsound3 import AVAILABLE_BACKENDS, DEFAULT_BACKEND

print(AVAILABLE_BACKENDS)  # for example: ["gstreamer", "ffmpeg", ...]
print(DEFAULT_BACKEND)  # for example: "gstreamer"
```

### Sound

`playsound` returns a `Sound` object for playback control:

| Method        | Description                               |
|---------------|-------------------------------------------|
| `.is_alive()` | Checks if the sound is currently playing. |
| `.wait()`     | Blocks execution until playback finishes. |
| `.stop()`     | Immediately stops playback.               |

## Supported systems

* **Linux**
    * GStreamer
    * ALSA (aplay and mpg123)
* **Windows**
    * WMPlayer
    * winmm.dll
* **macOS**
    * AppKit
    * afplay
* **Multiplatform**
    * FFmpeg

## Fork information

This repository was originally forked from [playsound](https://github.com/TaylorSMarks/playsound) library created by Taylor Marks.
The original library is not maintained anymore and doesn't accept pull requests.
This library is a major rewrite of its original.

Feel free to create an issue or contribute to `playsound3`!
