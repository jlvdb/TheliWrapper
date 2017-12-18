"""
determine software versions from data program files
"""

import os

from .base import DIRS


__version_theli__ = "N/A"
# read THELI version from README file
versionfile = os.path.join(DIRS["PIPESOFT"], "README")
with open(versionfile) as txt:
    for line in txt:
        if "version" in line:
            # select word containing digits
            for word in line.split():
                if any(char.isdigit() for char in word):
                    __version_theli__ = word.strip()
                    break
            break

__version_gui__ = "N/A"
# read GUI script verion from the most recent change log entry
versionfile = os.path.join(DIRS["PIPESOFT"], "gui", "CHANGELOG")
with open(versionfile) as txt:
    for line in txt:
        # version line starts with vX.XX...
        if line.startswith("v"):
            __version_gui__ = line.split()[0].strip("v")
            break

__version__ = "1.0"
