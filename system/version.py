"""
determine software versions
"""

import os

from .base import DIRS


__version_theli__, __version_gui__ = "N/A", "N/A"
versionfile = os.path.join(DIRS["PIPESOFT"], "README")
with open(versionfile) as txt:
    for line in txt:
        if "version" in line:
            for word in line.split():
                if any(char in word for char in "0123456789"):
                    __version_theli__ = word
                    break
            break
versionfile = os.path.join(DIRS["PIPESOFT"], "gui", "CHANGELOG")
with open(versionfile) as txt:
    for line in txt:
        if line.startswith("v"):
            __version_gui__ = line.split()[0].strip("v")
            break

__version__ = "0.3.1"
