"""
Defines low level functions and structures for the Reduction class
"""

import os
import sys
import shutil
import subprocess
from re import split
from fnmatch import fnmatch
from inspect import stack
from time import time
from itertools import combinations
from collections import namedtuple

# import user specific paths
_theli_home = os.path.join(os.path.expanduser("~"), ".theli")
try:
    sys.path.append(_theli_home)
    from theli_paths import DIRS, CMDTOOLS, CMDSCRIPTS, LOCKFILE, LOGFILE

except ImportError:
    print("\nSetting up system for first usage...")
    # paths read from "progs.ini": folders, binaries, scripts and configuration
    CMDTOOLS = {}  # binaries
    CMDSCRIPTS = {}  # scripts
    DIRS = {}  # folders
    DIRS["HOME"] = os.path.expanduser("~")
    DIRS["PIPEHOME"] = os.path.join(DIRS["HOME"], ".theli")
    DIRS["PY2THELI"] = os.path.join(DIRS["PIPEHOME"], "py2theli")
    with open(os.path.join(DIRS["PIPEHOME"], "scripts", "progs.ini")) as ini:
        # progs.ini is a shell script with variables to replace
        for line in ini:
            if "=" in line and not ("USE_X" in line or line.startswith("if")):
                # remove export statements, drop statements after ";"
                cleaned = line.strip("export").strip().split(";")[0].strip()
                varname, value = cleaned.split("=")
                if value != "" and varname != "LANG":
                    DIRS[varname] = value
    # substitute shell variables in paths
    for key in DIRS:
        DIRS[key] = DIRS[key].replace("~", DIRS["HOME"])
        while "$" in DIRS[key]:
            # split value in '${' + 'variablename' + '} trailing part'
            lead, var = DIRS[key].split("{")
            var, tail = var.split("}")
            tail = tail.strip("/")
            DIRS[key] = os.path.join(DIRS[var], tail)  # path: 'variable/tail'
        DIRS[key] = os.path.normpath(DIRS[key])
    LOCKFILE = os.path.join(DIRS["PY2THELI"], "theli.lock")
    LOGFILE = os.path.join(DIRS["PY2THELI"], "theli.log")
    # separate scripts and binaries from folders
    for key in tuple(DIRS.keys()):
        if key.startswith("P_"):
            CMDTOOLS[key] = DIRS.pop(key)
        if key.startswith("S_"):
            CMDSCRIPTS[key] = DIRS.pop(key)

    # create source files containing DIRS, CMDTOOLS, CMDSCRIPTS, ...
    try:
        with open(os.path.join(_theli_home, "theli_paths.py"), 'w') as f:
            f.write("\"\"\"\nThis file is generated automatically.\n")
            f.write("It contains the folders and paths to the THELI ")
            f.write("installation and package.\n\"\"\"\n\n")
            f.write("DIRS = {\n")
            for key, val in DIRS.items():
                f.write("    '%s': '%s',\n" % (key, val))
            f.write("}\n\n")
            f.write("CMDTOOLS = {\n")
            for key, val in CMDTOOLS.items():
                f.write("    '%s': '%s',\n" % (key, val))
            f.write("}\n\n")
            f.write("CMDSCRIPTS = {\n")
            for key, val in CMDSCRIPTS.items():
                f.write("    '%s': '%s',\n" % (key, val))
            f.write("}\n\n")
            f.write("LOCKFILE = '%s'\n\n" % LOCKFILE)
            f.write("LOGFILE = '%s'\n\n" % LOGFILE)
    except Exception:
        print("WARNING: database file could not be created: " + _paths_file)
        print("continuing...\n")
    # no need to import source file, as DRIS, CMDTOOLS, ... are defined


# common fits file extensions and file names of calibration master frames
FITS_EXTENSIONS = (".fits", ".FITS", ".fit", ".FIT", ".fts", ".FTS")
MASTER_PATTERN = ("BIAS_", "FLAT_", "DARK_")

# all possible image status flags in THELI file names (e.g. in xxxx_1OFCB.fits)
THELI_FLAGS = ("B", "H", "C", "D", "P", ".sub")
# dictionary of all possible THELI file name tags
THELI_TAGS = {"OFC": ("OFC")}
# given a file has tag 'key' then THELI_TAGS[key] lists all possible tags that
# start with 'key'.
for n in range(6):
    # It is assumed that the flags have to appear in the order as THELI_FLAGS
    flags = THELI_FLAGS[:n]
    tags = [""]
    tags.extend(flags)  # all remaining flags
    for i in range(2, 7):
        # all combinations of flags unless we run out of them (i > n)
        tags.extend(list(combinations(flags, i)))
    # it should always start with 'OFC'
    tags = ["OFC" + "".join(tup) for tup in tags]
    # reverse the order for readability
    THELI_TAGS["OFC" + THELI_FLAGS[n]] = tuple(reversed(tags))


INSTRUMENTS = []  # all instruments available in THELI
# splitting script: "process_split_[instrument@telescope]"
splitting_scripts = [
    os.path.join(DIRS["SCRIPTS"], s)
    for s in os.listdir(DIRS["SCRIPTS"])
    if os.path.isfile(os.path.join(DIRS["SCRIPTS"], s)) and
    s.startswith("process_split_") and
    s != "process_split_tiff.sh"]
# collect names of all available instruments
for fpath in splitting_scripts:
    # remove path, "process_split_" and extension -> instrument name
    instrument = os.path.basename(fpath).split("_", 2)[-1]
    INSTRUMENTS.append(os.path.splitext(instrument)[0])


# find method to read fits file headers:
# try importing astropy.io.fits or pyfits
try:
    from astropy.io import fits as pyfits
    __pyfits_success__ = True
except ImportError:
    try:
        import pyfits
        __pyfits_success__ = True
    except ImportError:
        __pyfits_success__ = False
# define function to read header values: if pyfits import failed, use custom
# function based on command line tool 'defits' (from THELI package)
if __pyfits_success__:
    def get_FITS_header_values(file, keys, extension=-1):
        """Opens FITS image 'file' and checks, if a list of key words ('keys')
        is found in a specified 'extension' of the FITS image. By default all
        extensions are checked, if they contain the key words.
        WARNING: if keys occur in multiple extensions, only the last occurence
        is returned.

        Arguments:
            file [string]:
                valid FITS file path
            keys [string, list of strings]:
                keyword(s) to read from FITS file
            extension [int]:
                FITS extension index (starting from 0) to check, by default -1
                which checks all available extension

        Returns:
            values [list]:
                value belonging to FITS key word in 'keys'
        """
        # list to hold results in order as keys are specified
        values = [None] * len(keys)
        with pyfits.open(file) as fits:
            # if no extension is defined, iterate through all and search
            iter_ext = range(len(fits)) if extension == -1 else [extension]
            for i in iter_ext:
                # check if table contains any of the key words
                for k, key in enumerate(keys):
                    try:
                        values[k] = (fits[i].header[key])
                    except KeyError:
                        continue
        # if any key word did not appear in extension(s), its value is None
        for i, val in enumerate(values):
            if val is None:
                raise KeyError("Keyword '%s' not found." % keys[i])
        return values
else:
    def get_FITS_header_values(file, keys, extension=-1):
        """Opens FITS image 'file' and checks, if a list of key words ('keys')
        is found in a specified 'extension' of the FITS image. By default all
        extensions are checked, if they contain the key words.
        WARNING: if keys occur in multiple extensions, only the last occurence
        is returned.

        Arguments:
            file [string]:
                valid FITS file path
            keys [string, list of strings]:
                keyword(s) to read from FITS file
            extension [int]:
                FITS extension index (starting from 0) to check, by default -1
                which checks all available extension
        Returns:
            values [list]:
                value belonging to FITS key word in 'keys'
        """
        # read the header from the stdout of 'dfits -x [extension]'
        cmdstr = "%s -x %d %s" % (CMDTOOLS["P_DFITS"], extension + 1, file)
        call = subprocess.Popen(cmdstr, shell=True, stdout=subprocess.PIPE)
        stdout = call.communicate()[0].decode("utf-8").splitlines()
        # make list of values from requested keywords
        values = []
        for key in keys:
            # some keywords may be repeated over many lines, join these lines
            subvals = []
            for line in stdout:
                if line.startswith(key):
                    subvals.append(line)
            # if no matching key word is found
            if subvals == []:
                raise KeyError("Keyword '%s' not found." % key)
            values.append("\n".join(subvals))
        # deduce the value type from the string pattern and convert it
        for i in range(len(values)):
            # special keywords like 'HISTORY' need no further processing
            splited = values[i].split("=", 1)
            if len(splited) == 1:
                continue
            # data keywords
            else:
                # some lines defining the image data type contain a comment
                # which follows the value after a slash -> remove comment
                splited = splited[1].split(" / ")[0].strip()
                # strings are enclosed with with white spaces ('string     ')
                if splited.startswith("'") and splited.endswith("'"):
                    values[i] = splited.strip("'").strip()
                # remaining types are either float or int -> convert type
                elif "." in splited:
                    values[i] = float(splited)
                else:
                    values[i] = int(splited)
        return values


# This is supposed to test if the terminal supports ANSI escape sequences.
# If not, define fall back function without any effect
try:
    # this might not cover all cases
    assert((sys.platform != 'Pocket PC' and
           (sys.platform != 'win32' or 'ANSICON' in os.environ)) or
           not hasattr(sys.stdout, 'isatty') and sys.stdout.isatty())

    def ascii_styled(string, stylestr):
        """Format the input 'string' using ANSI-escape sequences. The 3-byte
        'stylestr' determines: textstyle, foreground, background-color
        (example: bold red text on default background: 'br-').

        Arguments:
            string [string]:
                string to style with ANSI-escape sequences
            stylestr [string]:
                three byte string to define the style:
                textstyle:
                    - default; b bold; t grayed/transparent; i italic;
                    u underlined
                foreground:
                    - default; k black; r red; g green; y yellow; b blue;
                    m magenta; c cyan; w white
                background:
                    same as foreground
        Returns:
            string [string]:
                input string decorated with ANSI-escape sequences
        """
        # default, bold, greyed, italic, underlined
        attr = {"-": "0", "b": "1", "t": "2", "i": "3", "u": "4"}
        # black, red, green, yellow, blue, magenta, cyan, white, default
        fore = {"k": ";30", "r": ";31", "g": ";32", "y": ";33",
                "b": ";34", "m": ";35", "c": ";36", "w": ";37", "-": ""}
        # black, red, green, yellow, blue, magenta, cyan, white, default
        back = {"k": ";40", "r": ";41", "g": ";42", "y": ";43",
                "b": ";44", "m": ";45", "c": ";46", "w": ";47", "-": ""}
        try:
            head = "\033[%s%s%sm" % (
                attr[stylestr[0]], fore[stylestr[1]], back[stylestr[2]])
            return head + string + "\033[0;0;0m"
        except KeyError:
            raise ValueError("invalid formatter: '%s'" % stylestr)

except AssertionError:
    def ascii_styled(string, stylestr):
        """Return input 'string' if ANSI escape sequences are not supported,
        'stylestr' is dummy variable for compatibility
        """
        return string


def check_system_lock():
    """Test if a lock file is present in the THELI home folder and exit, if so.
    Can be used to permit multiple instances of THELI which would interfer by
    working on the same configuration files.

    Arguments: None, Returns: None
    """
    if os.path.exists(LOCKFILE):
        print()
        print(ascii_styled("ERROR:  ", "br-"),
              "cannot run more than one THELI instance at once\n")
        print("if this is not the case, try deleting")
        print(LOCKFILE, "\n")
        sys.exit(3)


def remove_temp_files():
    """Remove temporary files in THELI home folder from previous reduction.

    Arguments: None, Returns: None
    """
    for tempfile in os.listdir(DIRS["TEMPDIR"]):
        try:
            os.remove(os.path.join(DIRS["TEMPDIR"], tempfile))
        except Exception:
            pass


def get_crossid_radius(pixscale):
    """Estimate a reasonable radius for cross correlating sources in scamp.
    Scales with pixel scale of the chip.

    Arguments:
        pixscale [float]:
            pixel scale of the chip from which radius is calculated
    Returns:
        crossid [float]:
            cross correlation radius for scamp
    """
    if 0.2 <= pixscale < 0.7:
        return 2.0
    elif pixscale >= 0.7:
        return 2.5 * pixscale
    else:
        return 10.0 * pixscale


def list_filters(mainfolder, folder, instrument):
    """Scans a folder for FITS images and tries to extract the filters used
    during observation from the header. For detection in unsplitted (original)
    files, the key words and string conversion have to be implemented manually.

    Arguments:
        mainfolder [string]:
            path to folder containing 'folder'
        folder [string]:
            subfolder of mainfolder, containing FITS images
        instrument [string]:
            THELI identification string of the used instrument
    Returns:
        filters [list]:
            unique list of filters found in the FITS headers

    Note: The current implementation is not very flexible
    """
    if instrument not in INSTRUMENTS:
        raise ValueError("instrument '%s' is not defined" % instrument)
    folder = os.path.join(mainfolder, folder)
    # read the files an collect all present filters
    filters = set()
    for file in os.listdir(folder):
        path = os.path.join(folder, file)
        if os.path.isfile(path) and path.endswith(FITS_EXTENSIONS):
            try:  # splitted image image with standard THELI header
                new_filter = get_FITS_header_values(path, ["FILTER"])[0]
            except KeyError:  # original raw file -> manual implementation
                # ACAM@WHT
                if instrument == "ACAM@WHT":
                    allfilters = get_FITS_header_values(path, ["ACAMFILT"])[0]
                    filter1, filter2 = allfilters.split("+")
                    if filter1 == "CLEAR":
                        new_filter = "+" + filter2
                    else:
                        new_filter = "+" + filter1
                # GMOS-S-HAM@GEMINI
                elif instrument in ("GMOS-S-HAM@GEMINI",
                                    "GMOS-S-HAM_1x1@GEMINI"):
                    filter1, filter2 = get_FITS_header_values(
                        path, ["FILTER1", "FILTER2"])
                    if "open" in filter1:
                        new_filter = filter2
                    else:
                        new_filter = filter1
                # instrument not implemented
                else:
                    raise NotImplementedError(
                        "instrument '%s' has no " % instrument +
                        "implementation of filter keyword")
            filters.add(new_filter)
    # check result
    if len(filters) == 0:
        raise ValueError("Found no FITS-files with valid filter keywords")
    return sorted(filters)


def extract_tag(filename):
    """Extract the THELI progess tag from the filename of an image. Tag does
    not contain the chip number in case of a splitted image (example:
    calibrated 1st chip with background model subtracted: image_1OFCB -> OFCB)

    Arguments:
        filename [string]:
            valid path to a FITS image
    Returns
        tag [string]:
            'none' in case of raw image, '' (empty) in case of splitted image,
            'OFC' + any combination of ' BHCDP' for images after calibration,
            additinal '.sub' for a sky subtracted version of that image
    """
    fname, ext = os.path.splitext(os.path.split(filename)[1])
    try:  # tag is separated by an underscore
        base, tag = fname.rsplit("_", 1)
    except ValueError:
        return 'none'  # raw image
    # images that contain underscore could be still raw image
    if all(char.isdigit() for char in tag):
        try:  # splitted images have an entry in the header key word 'HISTORY'
            if "mefsplit" in get_FITS_header_values(filename, ["HISTORY"])[0]:
                return ''  # splitted image
        except Exception:
            return 'none'  # raw image
    # any other: have chip number + tag -> return tag only
    return ''.join([i for i in tag if not i.isdigit()])


def natural_sort(tosort):
    """Natural sort algorithm, treating digits in strings as numbers
    Arguments:
        tosort [list like]:
            list to sort
    Returns:
        sorted [list]:
            sorted list
    """
    def alphanum_key(key):
        return [int(c) if c.isdigit() else c.lower()
                for c in split('([0-9]+)', key)]
    return sorted(tosort, key=alphanum_key)


def sexagesimal_to_degree(sexagesimal_posangle):
    """Converts astronomical coordinate from sexagesimal representation
    (RA: HH:MM:SS, DEC: DD:MM:SS) to degrees (RA, DEC)

    Arguments:
        sexagesimal_posangle [2-dim tuple of strings]:
            tuple (RA, DEC) with coordinates in sexagesimal format
    Returns:
        degrees [2-dim tuple of float]:
            tuple (RA, DEC) with coordinate in degrees
    """
    ra, dec = sexagesimal_posangle
    ra = ra.replace(":", " ").split()
    h, m, s = [float(i) for i in ra]
    ra_deg = divmod((h + m / 60 + s / 3600) / 24 * 360, 360)[1]
    dec = dec.replace(":", " ").split()
    d, m, s = [float(i) for i in dec]
    dec_deg = d + m / 60 + s / 3600, 360
    return (ra_deg, dec_deg)


def degree_to_sexagesimal(degree_posangle):
    """Converts astronomical coordinate from degrees (RA, DEC) to sexagesimal
    representation (RA: HH:MM:SS, DEC: DD:MM:SS)

    Arguments:
        degrees [2-dim tuple of float]:
            tuple (RA, DEC) with coordinate in degrees
    Returns:
        sexagesimal_posangle [2-dim tuple of strings]:
            tuple (RA, DEC) with coordinates in sexagesimal format
    """
    ra, dec = degree_posangle
    h, m = divmod(ra, 15)
    h = divmod(h, 24)[1]
    m, s = divmod(m * 60, 15)
    s = s * 60 / 15
    ra_sex = "%02.0f:%02.0f:%05.2f" % (h, m, s)
    d, m = divmod(dec, 1)
    m, s = divmod(m * 60, 1)
    s = s * 60
    dec_sex = "%+3.0f:%02.0f:%04.1f" % (d, m, s)
    return (ra_sex, dec_sex)


def get_posangle(headerfolder):
    """Compute the position angle / the image rotation with respect to WCS for
    swarp from a set of header files for the coadded image. If no solution is
    found in the headers -999 is returned.

    Arguments:
        headerfolder [string]:
            valid path to folder, containing scamp header files
    Returns:
        posangle [float]:
            position angle for the correct rotation of the coadded image
    """
    # grap a scamp header file from folder
    for head in os.listdir(headerfolder):
        if head.endswith("head"):
            headerfile = os.path.join(headerfolder, head)
            break
    # use get_posangle from the THELi binaries
    command = ["get_posangle", "-c", "0", "0", "0", "0"]
    with open(headerfile) as head:
        # read the header file and scan for linear projection matrix
        # replace the default "0" in 'command' with the matrix elements 'CDi_j'
        for line in head:
            try:
                var, val = line.split("=", 1)
                val = val.split("/")[0]
            except ValueError:
                continue
            if var.strip() == "CD1_1":
                command[2] = val.strip()
            if var.strip() == "CD1_2":
                command[3] = val.strip()
            if var.strip() == "CD2_1":
                command[4] = val.strip()
            if var.strip() == "CD2_2":
                command[5] = val.strip()
    # grap the output of get_posangle and try to convert it to float
    call = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        shell=False, cwd=DIRS["BIN"])
    stdout = call.communicate()[0].decode("utf-8").splitlines()
    try:
        return float(stdout[0].strip())
    except Exception:
        return -999


def retrieve_object():
    """This function will query a database and try to fetch coordinates from an
    object identifier
    """
    raise NotImplementedError


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


class Folder(object):
    """Class with convenice functions to monitor the content and reduction
    progress of the THELI data folders. Uses file index to reduce redundant
    storage access. The index is only updated, if a minimum time interval has
    passed, or the function which calls the class method changes.

    Arguments:
        path [string]:
            path to the folder that is monitored
    """

    _fits_index = {}  # database of FITS files in the folder
    _update_time = 0  # time stamp of last update
    _update_delay = 0.05  # minimum time in seconds between two updates
    _last_call = "<module>"  # default calling function at initialization

    def __init__(self, path):
        super(Folder, self).__init__()
        self.abs = os.path.abspath(path)
        self.parent, self.path = os.path.split(self.abs)
        self._update_index()  # generate initial FITS index

    def _update_index(self, force=False):
        """Update the internal index if a minimum time interval has passed or
        the calling external function changed.

        Arguments:
            force [bool]:
                forces updating the index
        """
        # get external calling function
        callstack = stack()
        for i in range(1, len(callstack)):
            caller = callstack[i][3]
            # go back in stack till caller is no class member any more
            # ignore expressions in stack like <module> or <genexprgen>
            if not hasattr(self, caller) and caller[0] != "<":
                break
        # test if folder was scanned recently
        timediff = time() - self._update_time
        if timediff > self._update_delay or caller != self._last_call:
            # get all FITS files that are not master frames (BIAS, DARK, FLAT)
            files = [os.path.join(self.abs, f) for f in os.listdir(self.abs)
                     if os.path.isfile(os.path.join(self.abs, f)) and
                     f.endswith(FITS_EXTENSIONS) and
                     not f.startswith(MASTER_PATTERN)]
            # index: key: file name, value: THELI image tag
            _new_index = {}
            for f in files:
                if f in self._fits_index:  # copy existing ones to new index
                    _new_index[f] = self._fits_index[f]
                else:  # add new files, if they are not sky subtraction models
                    newtag = extract_tag(f)
                    if not newtag.endswith(".sky"):
                        _new_index[f] = newtag
            self._fits_index = _new_index
            # register last update time and calling function
            self._last_call = caller
            self._update_time = time()

    def __str__(self):
        return self.abs

    def __eq__(self, other):
        return self.abs == other

    def folders(self):
        """Return list of contained folders"""
        content = [os.path.join(self.abs, c) for c in os.listdir(self.abs)]
        return [c for c in content if os.path.isdir(c)]

    def fits(self, tag='*', ignore_sub=False):
        """Update index and return a list of files that have tags matching the
        tag pattern. Supports shell style globbing.

        Arguments:
            tag [string]:
                shell style pattern to filter the files
                (e.g. OFCB, OFC?D, OFC*)
            ignore_sub [bool]:
                do not list files that contain '.sub' in their tag
        Returns:
            filtered [list]:
                filtered list of FITS files
        """
        self._update_index()
        filtered = []
        for f, filetag in self._fits_index.items():
            if ignore_sub and filetag.endswith(".sub"):
                continue
            # match file tag against the pattern
            elif fnmatch(filetag, tag):
                filtered.append(f)  # append file name
        return filtered

    def fits_count(self, tag='*', ignore_sub=True):
        """Counts the number of FITS files matching the 'tag' pattern.

        Arguments:
            tag [string]:
                shell style pattern to filter the files
                (e.g. OFCB, OFC?D, OFC*)
            ignore_sub [bool]:
                do not list files that contain '.sub' in their tag
        Returns:
            count [int]:
                count of FITS files matching 'tag' pattern
        """
        fitsfiles = self.fits(tag, ignore_sub)
        count = 0
        for file in fitsfiles:
            # for a raw file, increase counter always (see extract_tag)
            if self._fits_index[file] == "none":
                count += 1
            # splitted files are only counted, if first chip of mosaic is found
            else:
                base, tag = file.rsplit("_", 1)
                if ''.join([i for i in tag if i.isdigit()]) == "1":
                    count += 1
        return count

    def tags(self, ignore_sub=False):
        """Update index and return all file tags found in folder.

        Arguments:
            ignore_sub [bool]:
                do not list files that contain '.sub' in their tag
        Returns:
            tags [set]:
                set of file tags in folder
        """
        self._update_index()
        tags = set()
        for f, tag in self._fits_index.items():
            if not (ignore_sub and tag.endswith("sub")):
                tags.add(tag)
        return tags

    def contains(self, entry):
        """Test if folder contains file oder folder 'entry'."""
        return any(fnmatch(f, entry) for f in os.listdir(self.abs))

    def contains_tag(self, tag):
        """Test if folder contains an image with file tag 'tag'."""
        return any(fnmatch(t, tag) for t in self.tags())

    def contains_master(self):
        """Test if folder contains any master bias, dark or flat frame."""
        fits = [f for f in os.listdir(self.abs)
                if os.path.isfile(os.path.join(self.abs, f)) and
                f.endswith(FITS_EXTENSIONS)]
        return any(f.startswith(MASTER_PATTERN) for f in fits)

    def search_flatnorm(self):
        """Test if the parent folder has a subfolder containing a normalized
        flat field."""
        flatnormdir = self.abs + "_norm"
        # check flatnorm folder
        if not os.path.exists(flatnormdir):
            return False
        # check flatnorm files
        fits = [f for f in os.listdir(flatnormdir)
                if os.path.isfile(os.path.join(flatnormdir, f)) and
                f.endswith(FITS_EXTENSIONS)]
        return any(f.startswith(MASTER_PATTERN) for f in fits)

    def contains_preview(self):
        """Test if the folder contains subfolder 'BINNED_TIFF' with binned
        image previews, each matching a file in the folder by name."""
        # check preview folder
        if not self.contains("BINNED_TIFF"):
            return False
        tifffiles = [os.path.join(self.abs, "BINNED_TIFF", t)
                     for t in os.listdir(os.path.join(self.abs, "BINNED_TIFF"))
                     if t.endswith(".tif")]
        # match each tiff image with a fits image in the parent folder
        for i, tifffile in enumerate(tifffiles):
            fitsfile = os.path.join(
                self.abs,
                os.path.split(tifffile.split("binned")[0] + ".fits")[1])
            if not os.path.exists(fitsfile):
                return False
            if (os.path.getctime(tifffile) - os.path.getctime(fitsfile)) < 0:
                return False
        return True

    def contains_refcatfiles(self):
        """Test if a reference catalogue for the data is present (ds9 and
        skycat format)."""
        # check ds9 file
        try:
            content = os.listdir(os.path.join(self.abs, "cat", "ds9cat"))
            found_ds9cat = any(c == "theli_mystd.reg" for c in content)
        except FileNotFoundError:
            found_ds9cat = False
        # check skycat file
        try:
            content = os.listdir(os.path.join(self.abs, "cat", "skycat"))
            found_skycat = any(c == "theli_mystd.skycat" for c in content)
        except FileNotFoundError:
            found_skycat = False
        return found_ds9cat and found_skycat

    def contains_catfiles(self):
        """Check if catalogues extracted from the images are (ds9 and skycat
        format)."""
        cat_files = []
        # check ds9 files
        try:
            content = os.listdir(os.path.join(self.abs, "cat", "ds9cat"))
            cat_files.extend([f for f in content if f.endswith(".reg")])
        except FileNotFoundError:
            pass
        # check skycat files
        try:
            content = os.listdir(os.path.join(self.abs, "cat", "skycat"))
            cat_files.extend([f for f in content if f.endswith(".skycat")])
        except FileNotFoundError:
            pass
        # must at least have one ds9 and one skycat file
        return len(cat_files) > 2

    def contains_astrometry(self):
        """Check if folder contains astrometric header files."""
        try:
            content = os.listdir(os.path.join(self.abs, "headers_scamp"))
            header_files = [f for f in content if f.endswith(".head")]
        except FileNotFoundError:
            header_files = []
        return len(header_files) > 0

    def contains_coadds(self, filterkey=""):
        """Check if folder contains coadded images.

        Arguments:
            filterkey [string]:
                instead of checking for any coadded image, look for a specific
                filter
        """
        if filterkey == "":
            coadds = [c for c in os.listdir(self.abs) if c.startswith("coadd")]
            for coadd in coadds:
                if os.path.exists(os.path.join(self.abs, coadd, "coadd.fits")):
                    return True
                else:
                    return False
            return False
        else:
            return os.path.exists(
                os.path.join(self.abs, "coadd_" + filterkey, "coadd.fits"))

    def check_global_weight(self):
        """Check if global weights (stored in parent/WEIGHTS) exist and have a
        newer time stamp than the image files in the folder."""
        # check weight folder presence
        weightfolder = os.path.join(os.path.split(self.abs)[0], "WEIGHTS")
        if not os.path.exists(weightfolder):
            return False
        # get the time stamp of the latest modified image in folder
        fitstime = max(os.path.getctime(fits)
                       for fits in self.fits(ignore_sub=True))
        # select global files and compare time stamps
        good_globals = []
        for weight in os.listdir(weightfolder):
            if "_dummy_" in weight:
                continue
            elif fnmatch(weight, "globalweight*[0-9].fits"):
                weight = os.path.join(weightfolder, weight)
                if (os.path.getctime(weight) - fitstime) < 0:
                    return False  # this file is outdated
            else:
                good_globals.append(weight)
        return len(good_globals) > 0  # test passed

    def check_weight(self):
        """Check if weight filess (stored in parent/WEIGHTS) exist and have a
        newer time stamp than the image files in the folder."""
        # check weight folder presence
        weightfolder = os.path.join(os.path.split(self.abs)[0], "WEIGHTS")
        if not os.path.exists(weightfolder):
            return False
        fitsfiles = self.fits(ignore_sub=True)
        # select weight images and check time stamps
        for fitsfile in fitsfiles:
            weight = os.path.join(  # expected weight name from FITS image
                weightfolder, ".weight".join(
                    os.path.splitext(os.path.split(fitsfile)[1])))
            # match weight image with a fits image
            if not os.path.exists(weight):
                return False  # no weight file exists for this image
            if (os.path.getctime(weight) - os.path.getctime(fitsfile)) < 0:
                return False  # this file is outdated
        return True  # test passed

    def count_groups(self):
        """Count the groups produced by sequence splitting."""
        n = 0
        while os.path.exists("%s_S%d" % (self.abs, n + 1)):
            n += 1
        return n

    def delete(self, target):
        """Delete a folder or file 'target' from the folder if no instance of
        THELI is running."""
        check_system_lock()  # exit to prevent data loss
        for entry in os.listdir(self.abs):
            if fnmatch(target, entry):
                delete = os.path.join(self.abs, os.path.join(self.abs, entry))
                if os.path.isdir(delete):  # delete folder
                    shutil.rmtree(delete)
                elif os.path.isfile(delete):  # delete file
                    os.remove(delete)

    def delete_tag(self, tag, ignore_sub=False):
        """Delete any FITS file that matches 'tag' if no instance of THELI is
        running."""
        check_system_lock()  # exit it prevent data loss
        for file in self.fits(tag, ignore_sub):
            os.remove(os.path.join(self.abs, file))

    def delete_master(self):
        """Delete any master bias/dark/flat frame in the folder if no
        instance of THELI is running."""
        check_system_lock()  # exit to prevent data loss
        # identify master frames
        master = [os.path.join(self.abs, f) for f in os.listdir(self.abs)
                  if os.path.isfile(os.path.join(self.abs, f)) and
                  f.endswith(FITS_EXTENSIONS) and
                  f.startswith(MASTER_PATTERN)]
        for m in master:
            os.remove(m)

    def restore(self):
        """restore the original (raw) FITS files in the folder and delete all
        other content if no instance of THELI is running."""
        check_system_lock()  # exit to prevent data loss
        content = os.listdir(self.abs)
        # assume folder is in initial state, if 'ORIGINALS' folder not present
        if "ORIGINALS" in content:
            for c in content:
                if c != "ORIGINALS":
                    self.delete(c)
            self.lift_content("ORIGINALS")

    def lift_content(self, subfolder):
        """Move the content of 'subfolder' to the its parent (folder) and
        delete the subfolder if no instance of THELI is running."""
        check_system_lock()  # exit to prevent data loss
        if self.contains(subfolder):
            subfolder = os.path.join(self.abs, subfolder)
            for entry in os.listdir(subfolder):
                shutil.move(  # move content to parent
                    os.path.join(subfolder, entry),
                    os.path.join(self.abs, entry))
            shutil.rmtree(subfolder)  # remove subfolder

    def move_tag(self, tag, dest, ignore_sub=False):
        """Move any FITS file that matches 'tag' to sufolder 'dest' if no
        instance of THELI is running.

        Arguments:
            tag [string]:
                shell style pattern to filter the files
                (e.g. OFCB, OFC?D, OFC*)
            dest [string]:
                destination subfolder to move files to
            ignore_sub [bool]:
                ignore files that contain '.sub' in their tag
        Returns:
            None
        """
        check_system_lock()  # exit to prevent data loss
        destfolder = os.path.join(self.abs, dest)
        if not os.path.exists(destfolder):
            os.mkdir(destfolder)
        for file in self.fits(tag, ignore_sub):
            try:
                os.rename(  # move file to destination
                    os.path.join(self.abs, file),
                    os.path.join(destfolder, file))
            except OSError:
                continue


class Parameters(object):
    """Controlls the THELI configuration files for easy reading, writing and
    restoring default values.

    Arguments:
        preparse [dict]:
            parameter dict (key: variable name, value: value) to initialize
            configureation files.
    """

    # keep the three configuration files in memory as a list
    # each list element is a line of the files
    param_sets = {"param_set1.ini": [],
                  "param_set2.ini": [],
                  "param_set3.ini": []}

    def __init__(self, preparse={}):
        super(Parameters, self).__init__()
        if type(preparse) is not dict:
            raise ValueError("preparse must be of type 'dict'")
        self.reset()  # use default (minimal) configuration file
        if len(preparse) == 0:
            self.set(preparse)

    def _modify_parameter_file(self, file_line_list, replace_dict):
        """Update THELI-parameters files.

        Arguments:
            file_line_list [list]:
                line list of a parameter file to update
            replace_dict [dict]:
                key (=variable name) and values to update in the parameter file
        Returns:
            file_line_list [list]:
                updated version of the input
            replace_dict [dict]:
                updated version of the input, from which each successfully
                updated parameter is removed
        """
        if len(replace_dict) == 0:  # nothing to do
            return file_line_list, {}
        for i in range(len(file_line_list)):
            # test every line if it contains any of the parameters to update
            for key in replace_dict:
                if file_line_list[i].startswith(key + "="):
                    # if line begins with parameter name (key), replace line
                    val = replace_dict[key]
                    val = str(val) if type(val) != str else val
                    file_line_list[i] = ("%s=%s\n") % (key, val)
                    # remove the parameter from the input dictionary
                    replace_dict.pop(key)
                    break
        # if all parameters were matched, replace_dict is empty
        return file_line_list, replace_dict

    def reset(self):
        """Restore default THELI-parameter files from default version in HOME
        folder"""
        # read backup of system specific values -> pack as dictionary
        sysdefault = {}
        with open(os.path.join(DIRS["PY2THELI"], "sys.default")) as d:
            for line in d.readlines():
                if "=" in line:
                    key, val = line.split("=", 1)
                    sysdefault[key] = val.strip()
        # read defaults and write new parameter files
        for n in (1, 2, 3):
            fname = "param_set%d.ini" % n
            with open(os.path.join(DIRS["PY2THELI"], fname + ".default")) as f:
                # first file contains system dependent lines, treat separately
                if n == 1:
                    # default file 1 and insert system defaults
                    self.param_sets[fname], remainder = \
                        self._modify_parameter_file(f.readlines(), sysdefault)
                # copy content of default file 2 and 3
                else:
                    self.param_sets[fname] = f.readlines()
            # write new files to disk
            with open(os.path.join(DIRS["PIPEHOME"], fname), 'w') as f:
                for line in self.param_sets[fname]:
                    f.write(line)

    def get(self, key):
        """Scan the configuration files for variable name 'key' and return
        its value."""
        for file in self.param_sets:
            for line in self.param_sets[file]:
                if line.startswith(key):
                    return line.split("=", 1)[1].strip()
        raise ValueError("found no parameter matching keyword '%s'" % key)

    def set(self, replace):
        """Update given parameters and write changes to THELI-configuration
        files to disk.

        Arguments:
            replace_dict [dict]:
                key (=variable name) and values to update in the parameter file
        Returns:
            None
        """
        # test if the system is locked already
        check_system_lock()  # if yes exit to not change the parameter settings
        if replace == {}:  # nothing to do
            return
        for fname, fcontent in self.param_sets.items():
            # apply changes and write to disk
            fcontent, replace = self._modify_parameter_file(fcontent, replace)
            with open(os.path.join(DIRS["PIPEHOME"], fname), 'w') as f:
                for line in fcontent:
                    f.write(line)
        # check if all parameters were matched to variable names
        if replace != {}:
            remaining_keys = ""
            for key in replace:
                remaining_keys += " '%s'" % key
            raise KeyError(
                "could not match these parameters:" + remaining_keys)
