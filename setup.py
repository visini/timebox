import os
from setuptools import setup

VERSION = "0.0.1"
if "VERSION" in os.environ:
    VERSION = os.getenv("VERSION")


APP_NAME = "App"
if "APP_NAME" in os.environ:
    APP_NAME = os.getenv("APP_NAME")


APP = ["main.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": True,
    "iconfile": "icon.icns",
    "plist": {
        "CFBundleShortVersionString": VERSION,
        "LSUIElement": True,
    },
    "packages": ["rumps", "paramiko", "cffi"],
}

setup(
    app=APP,
    name=APP_NAME,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
