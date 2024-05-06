from setuptools import setup
from pathlib import Path


def package_relative_path(path):
    return Path(__file__).parent / path


long_description = package_relative_path("README.md").read_text(encoding="UTF-8")

setup(
    name="playsound2",
    version="2.0.0-alpha",
    description=long_description,
    long_description=long_description,
    url="https://github.com/sjmikler/playsound2",
    author="Szymon Mikler",
    author_email="sjmikler@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Sound/Audio :: MIDI",
        "Topic :: Multimedia :: Sound/Audio :: Players",
        "Topic :: Multimedia :: Sound/Audio :: Players :: MP3",
    ],
    keywords="sound playsound music wave wav mp3 media song play audio",
    packages=["playsound2"],
    python_requires=">=3.7",
    install_requires=[
        "pygobject; platform_system=='Linux'",
    ],
)
