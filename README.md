> This repository was initially forked from [TaylorSMarks/playsound](https://github.com/TaylorSMarks/playsound/blob/master/playsound.py)

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
```

## Documentation

The playsound module contains only one thing - the function (also named) playsound:

```python
def playsound(sound: os.PathLike, block: bool = True) -> None:
    """Play a sound file using an audio player availabile on your system.

    Args:
        sound: Path to the sound file.
        block: If True, the function will block execution until the sound finishes playing.
    """
```

It requires one argument - the path to the file with the sound you'd like to play. This may be a local file, or a URL.
There's an optional second argument, block, which is set to True by default. Setting it to False makes the function run asynchronously.

## Supported systems

* Linux, using GStreamer (built-in on Linux distributions)
* Windows, using windll.winmm (built-in on Windows)
* OS X using afplay utility (built-in OS X)
