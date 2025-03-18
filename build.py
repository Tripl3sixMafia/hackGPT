import os
import sys
from PyInstaller import __main__ as pyi

if __name__ == "__main__":
    pyi.run([
        "--onefile",
        "--windowed",
        "--icon=icon.ico",
        "--name=DataSpecter",
        "DataSpecter.py"
    ])