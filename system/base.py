"""
Defines low level functions for the Reduction class
"""

import os
import sys
import subprocess
from re import split
from itertools import combinations

try:
    # import user specific paths
    _theli_home = os.path.join(os.path.expanduser("~"), ".theli")
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
    DIRS["LOGFOLDER"] = os.path.join(DIRS["PIPEHOME"], "script_logs")
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
    LOCKFILE = os.path.join(DIRS["PIPEHOME"], "theli.lock")
    LOGFILE = os.path.join(DIRS["PIPEHOME"], "theli_last.log")
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
    finally:
        # create log folder
        if not os.path.exists(os.path.join(DIRS["PIPEHOME"], "script_logs")):
            os.mkdir(os.path.join(DIRS["PIPEHOME"], "script_logs"))

from .version import __version_gui__


# common fits file extensions and file names of calibration master frames
FITS_EXTENSIONS = (".fits", ".FITS", ".fit", ".FIT", ".fts", ".FTS")

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
    def get_FITS_header_values(file, keys, extension=-1, exists=False):
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
            exists [bool]:
                check key existence only

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
                    if exists:
                        if key not in fits[i].header:
                            raise KeyError()
                    else:
                        try:
                            values[k] = (fits[i].header[key])
                        except KeyError:
                            continue
        if exists:
            return True
        else:
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
            exists [bool]:
                check key existence only

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
        if exists:
            return True
        else:
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
                    # strings are enclosed with with white spaces ('string   ')
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
        # single chip cameras
        try:  # splitted images have an entry in the header key word 'HISTORY'
            if "mefsplit" in get_FITS_header_values(filename, ["HISTORY"])[0]:
                return ''  # splitted image
        except Exception:
            # for mosaics: files get splitted by chip
            try:
                get_FITS_header_values(filename, ["ORIGFILE"], exists=True)
                return ''  # splitted image
            except Exception as e:
                raise e
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
