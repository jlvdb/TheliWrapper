"""
Defines the instrument manager for the Reduction class
"""

import os

from .base import DIRS, INSTRUMENTS


class Instrument(object):
    """Manages instruments in THELI by checking, if it is properly implemented
    and loading instrument data.

    Arguments:
        instrument [string]:
            valid THELI instrument string (e.g. ACAM@WHT)
    """

    def __init__(self, instrument):
        super(Instrument, self).__init__()
        # load instrument data
        self.set(instrument)

    def __str__(self):
        string = "instrument: %s (type: %s)\n" % (self.NAME, self.TYPE)
        string += "%d chip(s) of size" % self.NCHIPS
        string += " size %d x %d" % (self.SIZEX, self.SIZEY)
        string += " with pixel scale %.3f" % self.PIXSCALE
        return string

    def set(self, new_instrument):
        """Changes instrument to 'new_instrument' and loads data file."""
        # delete data from previous instrument
        self.NAME = ""
        self.SIZEX = 0
        self.SIZEY = 0
        self.NCHIPS = 0
        self.TYPE = "NONE"
        self.PIXSCALE = 0.0
        # check if new instrument is implemented
        if new_instrument not in INSTRUMENTS:
            raise ValueError(
                "Not in list of implemented instruments: " + new_instrument)
        self.NAME = new_instrument
        # figure out path to the shell style instrument .ini-file
        if_prof = os.path.join(  # professional instruments
            DIRS["SCRIPTS"], "instruments_professional", "%s.ini" % self.NAME)
        if_comm = os.path.join(  # commercial instruments
            DIRS["SCRIPTS"], "instruments_commercial", "%s.ini" % self.NAME)
        if_user = os.path.join(  # user defined instruments
            DIRS["PIPEHOME"], "instruments_user", "%s.ini" % self.NAME)
        if os.path.exists(if_prof):
            inifile = if_prof
        elif os.path.exists(if_comm):
            inifile = if_comm
        elif os.path.exists(if_user):
            inifile = if_user
        else:  # data incomplete
            raise ValueError(
                "Instrument definition file not found: %s.ini" % self.NAME)
        # Read the shell variables of interest from the instrument file:
        # number of chips, x- and y-dimension of first chip (assuming first one
        # is representative for mosaic), type (optical, NIR, MIR), pixel scale
        with open(inifile) as ini:
            for line in ini.readlines():
                # example format for single chip:
                # SIZEX/Y=([1]=2044)
                # example format for mosaic:
                # SIZEX/Y=([1]=2038 [2]=2038 [3]=2038 [4]=2038 [5]=2038 ...)
                if "SIZEX=" in line:
                    n = line.strip().split("=")
                    if len(n) == 3:
                        self.SIZEX = int(n[2].strip("()[]"))
                    else:
                        self.SIZEX = int(n[2].split()[0])  # get first chip
                if "SIZEY=" in line:
                    n = line.strip().split("=")
                    if len(n) == 3:
                        self.SIZEY = int(n[2].strip("()[]"))
                    else:
                        self.SIZEY = int(n[2].split()[0])  # get first chip
                # format: NCHIPS/TYPE/PIXSCALE=X
                if "NCHIPS=" in line:
                    n = line.strip().split("=")
                    self.NCHIPS = int(n[1])
                if "TYPE=" in line:
                    self.TYPE = line.strip().split("=")[1]
                if "PIXSCALE=" in line:
                    self.PIXSCALE = float(line.strip().split("=")[1])
        # type may not be defined: assume optical
        if self.TYPE is None:
            self.TYPE = "OPT"
