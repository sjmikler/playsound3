from codecs import open
from inspect import getsource
from os.path import abspath, dirname, join

from setuptools import setup

here = abspath(dirname(getsource(lambda: 0)))

with open(join(here, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="playsound",
    version="1.3.0",
    description=long_description.splitlines()[2][1:-1],
    long_description=long_description,
    url="https://github.com/sjmikler/playsound2",
    author="Szymon Mikler",
    author_email="sjmikler@gmail.com",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Sound/Audio :: MIDI",
        "Topic :: Multimedia :: Sound/Audio :: Players",
        "Topic :: Multimedia :: Sound/Audio :: Players :: MP3",
    ],
    keywords="sound playsound music wave wav mp3 media song play audio",
    py_modules=["playsound"],
)
