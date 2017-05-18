"""
This is a python wrapper for the THELI GUI scripts, based
on the THELI package for astronomical image reduction.

"""

import os
import sys
import shutil
import subprocess
from re import split
from fnmatch import fnmatch
from inspect import stack
from time import time, sleep
from itertools import combinations
from collections import namedtuple

# find method to read fits file headers
try:
    from astropy.io import fits as pyfits

    def get_FITS_keys(file, keys, extension=-1):
        values = [None] * len(keys)
        with pyfits.open(file) as fits:
            iter_ext = range(len(fits)) if extension == -1 else [extension]
            for i in iter_ext:
                for k, key in enumerate(keys):
                    try:
                        values[k] = (fits[i].header[key])
                    except KeyError:
                        continue
        for i, val in enumerate(values):
            if val is None:
                raise KeyError("Keyword '%s' not found." % keys[i])
        return values

except ImportError:
    try:
        import pyfits

        def get_FITS_keys(file, keys):
            values = [None] * len(keys)
            with pyfits.open(file) as fits:
                for i in range(len(fits)):
                    for k, key in enumerate(keys):
                        try:
                            values[k] = (fits[i].header[key])
                        except KeyError:
                            continue
            for i, val in enumerate(values):
                if val is None:
                    raise KeyError("Keyword '%s' not found." % keys[i])
            return values

    except ImportError:
        # use dfits from THELI binaries to read full header
        def get_FITS_keys(file, keys, extension=-1):
            # read the headers
            cmdstr = "%s -x %d %s" % (CMDTOOLS["P_DFITS"], extension + 1, file)
            call = subprocess.Popen(cmdstr, shell=True, stdout=subprocess.PIPE)
            stdout = call.communicate()[0].decode("utf-8").splitlines()
            # make list of values from requested keywords
            values = []
            for key in keys:
                # some keywords may be repeated over several lines, join these
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
                # test for endtype keywords, e.g. HISTORY
                splited = values[i].split("=", 1)
                if len(splited) == 1:
                    continue
                # ordinary keywords
                else:
                    splited = splited[1].split(" / ")[0].strip()
                    # strings are enclosed with 'string     ' with white spaces
                    if splited.startswith("'") and splited.endswith("'"):
                        values[i] = splited.strip("'").strip()
                    # remaining types are either float or int
                    elif "." in splited:
                        values[i] = float(splited)
                    else:
                        values[i] = int(splited)
            return values


# test terminal capabilities
try:
    # isatty is not always implemented, #6223.
    assert((sys.platform != 'Pocket PC' and
           (sys.platform != 'win32' or 'ANSICON' in os.environ)) or
           not hasattr(sys.stdout, 'isatty') and sys.stdout.isatty())

    def ascii_styled(string, stylestr):
        """Format the input 'string' using ASCII-escape sequences. The 3-byte
        'stylestr' determines: textstyle, foreground, background-color."""
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

except Exception:
    def ascii_styled(string, stylestr):
        return string


# global parameters
FITS_EXTENSIONS = (".fits", ".FITS", ".fit", ".FIT", ".fts", ".FTS")
MASTER_PATTERN = ("BIAS_", "FLAT_", "DARK_")

# possible THELI tag combinations for input files
THELI_TAGS = {"OFC": ("OFC")}
THELI_FLAGS = ("B", "H", "C", "D", "P", ".sub")
for n in range(6):
    flags = THELI_FLAGS[:n]
    tags = [""]
    tags.extend(flags)
    for i in range(2, 7):
        tags.extend(list(combinations(flags, i)))
    tags = ["OFC" + "".join(tup) for tup in tags]
    THELI_TAGS["OFC" + THELI_FLAGS[n]] = tuple(reversed(tags))
del(flags, tags, n, i)

# paths to theli, the binaries, scripts and the configuration
CMDTOOLS = {}
CMDSCRIPTS = {}
DIRS = {}
DIRS["HOME"] = os.path.expanduser("~")
DIRS["PIPEHOME"] = os.path.join(DIRS["HOME"], ".theli")
# get remaining paths from the GUI initialization script
with open(os.path.join(DIRS["PIPEHOME"], "scripts", "progs.ini")) as ini:
    for line in ini:
        # check, if any of the variables is defined in the current line
        if "=" in line:
            if "USE_X" in line or line.startswith("if"):
                continue
            # remove export statements
            cleaned = line.strip("export").strip().split(";")[0]
            varname, value = cleaned.strip().split("=")
            if value != "":
                DIRS[varname] = value
DIRS["PY2THELI"] = os.path.join(DIRS["PIPEHOME"], "py2theli")
# substitute shell variables in paths
for key in DIRS:
    DIRS[key] = DIRS[key].replace("~", DIRS["HOME"])
    while "$" in DIRS[key]:
        lead, var = DIRS[key].split("{")
        var, tail = var.split("}")  # var is the variable name
        tail = tail.strip("/")
        DIRS[key] = os.path.join(DIRS[var], tail)  # path: 'variable/tail'
    DIRS[key] = os.path.normpath(DIRS[key])
LOCKFILE = os.path.join(DIRS["PY2THELI"], "theli.lock")
LOGFILE = os.path.join(DIRS["PY2THELI"], "theli.log")
# separate types
for key in tuple(DIRS.keys()):
    if key == "LANG":
        DIRS.pop(key)
    if key.startswith("P_"):
        CMDTOOLS[key] = DIRS.pop(key)
    if key.startswith("S_"):
        CMDSCRIPTS[key] = DIRS.pop(key)

# collect instrument data, each instrument should have a splitting script
INSTRUMENTS = {}
splitting_scripts = [
    os.path.join(DIRS["SCRIPTS"], s) for s in os.listdir(DIRS["SCRIPTS"])
    if os.path.isfile(os.path.join(DIRS["SCRIPTS"], s)) and
    s.startswith("process_split_")]
available_instruments = []
for fpath in splitting_scripts:
    # remove path, "process_split_" and extension -> instrument name
    instrument = os.path.basename(fpath).split("_", 2)[-1]
    instrument = os.path.splitext(instrument)[0]
    # remove other scripts that made it into the list
    if instrument[0].isupper():
        available_instruments.append(instrument)
# check the instrument definition files
chipprops = namedtuple(
    'chipprops', ['SIZEX', 'SIZEY', 'NCHIPS', 'TYPE', 'PIXSCALE'])
for instrument in available_instruments:
    # instrument data can be in different locations, depending on tpye in GUI
    if_comm = os.path.join(
        DIRS["SCRIPTS"], "instruments_commercial", "%s.ini" % instrument)
    if_prof = os.path.join(
        DIRS["SCRIPTS"], "instruments_professional", "%s.ini" % instrument)
    if_user = os.path.join(
        DIRS["PIPEHOME"], "instruments_user", "%s.ini" % instrument)
    if os.path.exists(if_comm):
        inifile = if_comm
    elif os.path.exists(if_prof):
        inifile = if_prof
    else:
        # data possibly incomplete -> remove instrument from final list
        continue
    with open(inifile) as ini:
        content = ini.readlines()
    data = {}
    # read the shell variables of interest from the instrument file
    for line in content:
        if "SIZEX=" in line:
            n = line.strip().split("=")
            if len(n) == 3:
                data["SIZEX"] = int(n[2].strip("()[]"))
            else:
                data["SIZEX"] = int(n[2].split()[0])
        if "SIZEY=" in line:
            n = line.strip().split("=")
            if len(n) == 3:
                data["SIZEY"] = int(n[2].strip("()[]"))
            else:
                data["SIZEY"] = int(n[2].split()[0])
        if "NCHIPS=" in line:
            n = line.strip().split("=")
            data["NCHIPS"] = int(n[1])
        if "TYPE=" in line:
            data["TYPE"] = line.strip().split("=")[1]
        if "PIXSCALE=" in line:
            data["PIXSCALE"] = float(line.strip().split("=")[1])
    if "TYPE" not in data:  # assume optical
        data["TYPE"] = "OPT"
    if len(data) == len(chipprops._fields):
        INSTRUMENTS[instrument] = chipprops(
            data["SIZEX"], data["SIZEY"], data["NCHIPS"], data["TYPE"],
            data["PIXSCALE"])

ERR_KEYS = ["*Error*"]  # additional errors
ERR_EXCEPT = []
# get keywords for errors and exceptions in logfile from Theli GUI source file
theliform_path = os.path.join(DIRS["PIPESOFT"], "gui", "theliform.ui.h")
with open(theliform_path) as cc:
    for line in cc.readlines():
        line = line.strip()
        if line.startswith("errorlist"):
            statement = line.split('"', 1)[1].rsplit('"', 1)[0]
            ERR_KEYS.append(statement.replace('\\"', '"'))
        if line.startswith("falseerrorlist"):
            statement = line.split('"', 1)[1].rsplit('"', 1)[0]
            ERR_EXCEPT.append(statement.replace('\\"', '"'))
if len(ERR_KEYS) == 1 or len(ERR_EXCEPT) == 0:
    raise RuntimeError("could find error statements in %s" % theliform_path)


# determine software versions
__version_theli__, __version_gui__, __version__ = "N/A", "N/A", "0.3"
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


def check_system_lock():
    # test if the system is locked already, prevents parallel instances
    # messing up the configuration files
    if os.path.exists(LOCKFILE):
        print()
        print(ascii_styled("ERROR:  ", "br-"),
              "cannot run more than one THELI instance at once\n")
        print("if this is not the case, try deleting")
        print(LOCKFILE, "\n")
        sys.exit(3)


def remove_temp_files():
    # remove temporary files as they might belong to a different project
    for tempfile in os.listdir(DIRS["TEMPDIR"]):
        try:
            os.remove(os.path.join(DIRS["TEMPDIR"], tempfile))
        except Exception:
            pass


def get_crossid_radius(pixscale):
    if 0.2 <= pixscale < 0.7:
        return 2.0
    elif pixscale >= 0.7:
        return 2.5 * pixscale
    else:
        return 10.0 * pixscale


def list_filters(mainfolder, folder, instrument):
    # in the unsplitted files, the filter keyword is not standard, treat
    # instruments differently
    # this function is not very nice, as all instruments must be implemented
    # manually, maybe the coadd->config source code helps
    if instrument not in INSTRUMENTS:
        raise ValueError("instrument '%s' is not defined" % instrument)
    folder = os.path.join(mainfolder, folder)
    # read the files an collect all present filters
    filters = set()
    for file in os.listdir(folder):
        path = os.path.join(folder, file)
        if os.path.isfile(path) and path.endswith(FITS_EXTENSIONS):
            # ACAM@WHT
            if instrument == "ACAM@WHT":
                try:
                    allfilters = get_FITS_keys(path, ["ACAMFILT"])[0]
                    filter1, filter2 = allfilters.split("+")
                    if filter1 == "CLEAR":
                        new_filter = "+" + filter2
                    else:
                        new_filter = "+" + filter1
                except KeyError:
                    new_filter = get_FITS_keys(path, ["FILTER"])[0]
            # GMOS-S-HAM@GEMINI
            elif instrument in ("GMOS-S-HAM@GEMINI", "GMOS-S-HAM_1x1@GEMINI"):
                try:
                    filter1, filter2 = get_FITS_keys(
                        path, ["FILTER1", "FILTER2"])
                    if "open" in filter1:
                        new_filter = filter2
                    else:
                        new_filter = filter1
                except KeyError:
                    new_filter = get_FITS_keys(path, ["FILTER"])[0]
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
    # original -> None, splitted -> '', else -> tag without chip number
    fname, ext = os.path.splitext(os.path.split(filename)[1])
    split = fname.rsplit("_", 1)
    if len(split) == 1:
        return 'none'  # original unsplitted file
    if all(char.isdigit() for char in split[1]):
        try:
            if "mefsplit" in get_FITS_keys(filename, ["HISTORY"])[0]:
                return ''  # splitted image
        except Exception:
            # raise exception as e
            return 'none'  # original unsplitted file
    # have tag with chip number and flags -> return flags only
    return ''.join([i for i in split[1] if not i.isdigit()])


def natural_sort(tosort):
    def alphanum_key(key):
        return [int(c) if c.isdigit() else c.lower()
                for c in split('([0-9]+)', key)]
    return sorted(tosort, key=alphanum_key)


def sexagesimal_to_degree(sexagesimal_posangle):
    ra, dec = sexagesimal_posangle
    ra = ra.replace(":", " ").split()
    h, m, s = [float(i) for i in ra]
    ra_deg = divmod((h + m / 60 + s / 3600) / 24 * 360, 360)[1]
    dec = dec.replace(":", " ").split()
    d, m, s = [float(i) for i in dec]
    dec_deg = d + m / 60 + s / 3600, 360
    return (ra_deg, dec_deg)


def degree_to_sexagesimal(degree_posangle):
    # tested
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
    for head in os.listdir(headerfolder):
        if head.endswith("head"):
            headerfile = os.path.join(headerfolder, head)
    command = ["get_posangle", "-c", "0", "0", "0", "0"]
    with open(headerfile) as head:
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
    call = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        shell=False, cwd=DIRS["BIN"])
    stdout = call.communicate()[0].decode("utf-8").splitlines()
    try:
        return float(stdout[0].strip())
    except Exception:
        return -999


def retrieve_object():
    raise NotImplementedError


class Folder(object):

    _fits_index = {}
    _update_time = 0
    _update_delay = 0.05
    _last_call = "<module>"

    def __init__(self, path):
        super(Folder, self).__init__()
        self.abs = os.path.abspath(path)
        self.parent, self.path = os.path.split(self.abs)
        self._update_index()

    def _update_index(self, force=False):
        # initiate scan if different function/reduction step triggered update
        callstack = stack()
        for i in range(1, len(callstack)):
            caller = callstack[i][3]
            # ignore expressions in stack like <module> or <genexprgen>
            if not hasattr(self, caller) and caller[0] != "<":
                break
        # test if folder was scanned recently
        timediff = time() - self._update_time
        if timediff > self._update_delay or caller != self._last_call:
            if not hasattr(self, "_fits_index"):
                self._fits_index = {}
            # get all fits files that are not master frames
            files = [os.path.join(self.abs, f) for f in os.listdir(self.abs)
                     if os.path.isfile(os.path.join(self.abs, f)) and
                     f.endswith(FITS_EXTENSIONS) and
                     not f.startswith(MASTER_PATTERN)]
            # update map: name -> tag (remove missing entries, add new ones)
            _new_index = {}
            for f in files:
                if f in self._fits_index:
                    _new_index[f] = self._fits_index[f]
                else:
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
        content = [os.path.join(self.abs, c) for c in os.listdir(self.abs)]
        return [c for c in content if os.path.isdir(c)]

    def fits(self, tag='*', ignore_sub=False):
        self._update_index()
        filtered = []
        for f, filetag in self._fits_index.items():
            if ignore_sub and filetag.endswith(".sub"):
                continue
            elif fnmatch(filetag, tag):
                filtered.append(f)
        return filtered

    def fits_count(self, tag='*', ignore_sub=True):
        """this does not distinguish between files with different tags"""
        fitsfiles = self.fits(tag, ignore_sub)
        count = 0
        for file in fitsfiles:
            if self._fits_index[file] == "none":
                count += 1
            else:
                base, tag = file.rsplit("_", 1)
                if ''.join([i for i in tag if i.isdigit()]) == "1":
                    count += 1
        return count

    def tags(self, ignore_sub=False):
        self._update_index()
        tags = set()
        for f, tag in self._fits_index.items():
            if not (ignore_sub and tag.endswith("sub")):
                tags.add(tag)
        return tags

    def contains(self, entry):
        return any(fnmatch(f, entry) for f in os.listdir(self.abs))

    def contains_tag(self, tag):
        return any(fnmatch(t, tag) for t in self.tags())

    def contains_master(self):
        fits = [f for f in os.listdir(self.abs)
                if os.path.isfile(os.path.join(self.abs, f)) and
                f.endswith(FITS_EXTENSIONS)]
        return any(f.startswith(MASTER_PATTERN) for f in fits)

    def search_flatnorm(self):
        flatnormdir = self.abs + "_norm"
        if not os.path.exists(flatnormdir):
            return False
        fits = [f for f in os.listdir(flatnormdir)
                if os.path.isfile(os.path.join(flatnormdir, f)) and
                f.endswith(FITS_EXTENSIONS)]
        return any(f.startswith(MASTER_PATTERN) for f in fits)

    def contains_preview(self):
        if not self.contains("BINNED_TIFF"):
            return False
        tifffiles = [os.path.join(self.abs, "BINNED_TIFF", t)
                     for t in os.listdir(os.path.join(self.abs, "BINNED_TIFF"))
                     if t.endswith(".tif")]
        for i, tifffile in enumerate(tifffiles):
            # match each tiff image with a fits image in the parent folder
            fitsfile = os.path.join(
                self.abs,
                os.path.split(tifffile.split("binned")[0] + ".fits")[1])
            if not os.path.exists(fitsfile):
                return False
            if (os.path.getctime(tifffile) - os.path.getctime(fitsfile)) < 0:
                return False
        return True

    def contains_refcatfiles(self):
        try:
            content = os.listdir(os.path.join(self.abs, "cat", "ds9cat"))
            found_ds9cat = any(c == "theli_mystd.reg" for c in content)
        except FileNotFoundError:
            found_ds9cat = False
        try:
            content = os.listdir(os.path.join(self.abs, "cat", "skycat"))
            found_skycat = any(c == "theli_mystd.skycat" for c in content)
        except FileNotFoundError:
            found_skycat = False
        return found_ds9cat and found_skycat

    def contains_catfiles(self):
        """check if output of 'extract sources' (THELI routines) is
        present"""
        cat_files = []
        try:
            content = os.listdir(os.path.join(self.abs, "cat", "ds9cat"))
            cat_files.extend([f for f in content if f.endswith(".reg")])
        except FileNotFoundError:
            pass
        try:
            content = os.listdir(os.path.join(self.abs, "cat", "skycat"))
            cat_files.extend([f for f in content if f.endswith(".skycat")])
        except FileNotFoundError:
            pass
        return len(cat_files) > 2

    def contains_astrometry(self):
        try:
            content = os.listdir(os.path.join(self.abs, "headers_scamp"))
            header_files = [f for f in content if f.endswith(".head")]
        except FileNotFoundError:
            header_files = []
        return len(header_files) > 0

    def contains_coadds(self, filterkey=""):
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
        weightfolder = os.path.join(os.path.split(self.abs)[0], "WEIGHTS")
        if not os.path.exists(weightfolder):
            return False
        fitstime = max(os.path.getctime(fits)
                       for fits in self.fits(ignore_sub=True))
        good_globals = []
        for weight in os.listdir(weightfolder):
            if "_dummy_" in weight:
                continue
            elif fnmatch(weight, "globalweight*[0-9].fits"):
                weight = os.path.join(weightfolder, weight)
                if (os.path.getctime(weight) - fitstime) < 0:
                    return False
            else:
                good_globals.append(weight)
        return len(good_globals) > 0

    def check_weight(self):
        weightfolder = os.path.join(os.path.split(self.abs)[0], "WEIGHTS")
        if not os.path.exists(weightfolder):
            return False
        fitsfiles = self.fits(ignore_sub=True)
        for fitsfile in fitsfiles:
            weight = os.path.join(
                weightfolder,
                ".weight".join(os.path.splitext(os.path.split(fitsfile)[1])))
            # match weight image with a fits image
            if not os.path.exists(weight):
                return False
            if (os.path.getctime(weight) - os.path.getctime(fitsfile)) < 0:
                return False
        return True

    def count_groups(self):
        n = 0
        while os.path.exists("%s_S%d" % (self.abs, n + 1)):
            n += 1
        return n

    def delete(self, target):
        """delete entry 'target' from folder"""
        # test if the system is locked already
        check_system_lock()
        for entry in os.listdir(self.abs):
            if fnmatch(target, entry):
                delete = os.path.join(self.abs, os.path.join(self.abs, entry))
                if os.path.isdir(delete):
                    shutil.rmtree(delete)
                elif os.path.isfile(delete):
                    os.remove(delete)

    def delete_tag(self, tag, ignore_sub=False):
        """delete any FITS file that matches 'tag'"""
        # test if the system is locked already
        check_system_lock()
        for file in self.fits(tag, ignore_sub):
            try:
                os.remove(os.path.join(self.abs, file))
            except OSError:
                continue

    def delete_master(self):
        """delete any master bias/dark/flat frame in the folder"""
        # test if the system is locked already
        check_system_lock()
        master = [os.path.join(self.abs, f) for f in os.listdir(self.abs)
                  if os.path.isfile(os.path.join(self.abs, f)) and
                  f.endswith(FITS_EXTENSIONS) and
                  f.startswith(MASTER_PATTERN)]
        for m in master:
            os.remove(m)

    def restore(self):
        """restore the original (raw) FITS files in the folder and delete all
        other content"""
        # test if the system is locked already
        check_system_lock()
        content = os.listdir(self.abs)
        if "ORIGINALS" in content:
            for c in content:
                if c != "ORIGINALS":
                    self.delete(c)
            self.lift_content("ORIGINALS")

    def lift_content(self, subfolder):
        """move the content of a subfolder to the parent and delete it"""
        # test if the system is locked already
        check_system_lock()
        if self.contains(subfolder):
            subfolder = os.path.join(self.abs, subfolder)
            for entry in os.listdir(subfolder):
                shutil.move(
                    os.path.join(subfolder, entry),
                    os.path.join(self.abs, entry))
            shutil.rmtree(subfolder)

    def move_tag(self, tag, dest, ignore_sub=False):
        """move any FITS file that matches 'tag' to sufolder 'dest'"""
        # test if the system is locked already
        check_system_lock()
        destfolder = os.path.join(self.abs, dest)
        if not os.path.exists(destfolder):
            os.mkdir(destfolder)
        for file in self.fits(tag, ignore_sub):
            try:
                os.remove(os.path.join(self.abs, file))
            except OSError:
                continue
            try:
                os.rename(
                    os.path.join(self.abs, file),
                    os.path.join(destfolder, file))
            except OSError:
                continue


class Parameters(object):
    # keep parameter files for quicker modifications
    param_sets = {"param_set1.ini": [],
                  "param_set2.ini": [],
                  "param_set3.ini": []}

    def __init__(self, preparse):
        super(Parameters, self).__init__()
        """restore default parameters on initialization"""
        self.reset()
        self.set(preparse)

    def _modify_parameter_file(self, file_line_list, replace_dict):
        """Modify Theli-parameters of the param_set.ini that are kept in memory
        (file_line_list). Changes are parsed as
        replace_dict[PARAMETER] = VALUE."""
        if len(replace_dict) == 0:
            return file_line_list, {}
        for i in range(len(file_line_list)):
            for key in replace_dict:
                if file_line_list[i].startswith(key + "="):
                    # if line begins with parameter name (key), replace line
                    val = replace_dict[key]
                    val = str(val) if type(val) != str else val
                    file_line_list[i] = ("%s=%s\n") % (key, val)
                    # remove the parameter from the input dictionary
                    replace_dict.pop(key)
                    break
        # return replace_dict to check, if all parameters were matched
        return file_line_list, replace_dict

    def reset(self):
        """Restore default Theli-parameter files from backup"""
        # read backup of system specific values -> pack as dictionary
        sysdefault = {}
        with open(os.path.join(DIRS["PY2THELI"], "sys.default")) as d:
            for line in d.readlines():
                if "=" in line:
                    key, val = line.split("=", 1)  # split: param-name, value
                    sysdefault[key] = val.strip()
        # read defaults and write new parameter files
        for n in (1, 2, 3):
            fname = "param_set%d.ini" % n
            with open(os.path.join(DIRS["PY2THELI"], fname + ".default")) as f:
                # first file contains system dependent lines, treat separately
                if n == 1:
                    # insert system defaults
                    self.param_sets[fname], remainder = \
                        self._modify_parameter_file(f.readlines(), sysdefault)
                # for file 2 and 3 just replace with backup file content
                else:
                    self.param_sets[fname] = f.readlines()
            with open(os.path.join(DIRS["PIPEHOME"], fname), 'w') as f:
                for line in self.param_sets[fname]:
                    f.write(line)

    def get(self, key):
        for file in self.param_sets:
            for line in self.param_sets[file]:
                if line.startswith(key):
                    return line.split("=", 1)[1].strip()
        raise ValueError("found no parameter matching keyword '%s'" % key)

    def set(self, replace):
        """Wrapper for 'modify_lines_from_dict'. Write changes to theli-
        parameter file. Check, if any unmatched parameter is left"""
        # test if the system is locked already
        check_system_lock()
        if replace == {}:
            return
        for fname, fcontent in self.param_sets.items():
            # apply changes
            fcontent, replace = self._modify_parameter_file(fcontent, replace)
            with open(os.path.join(DIRS["PIPEHOME"], fname), 'w') as f:
                for line in fcontent:
                    f.write(line)
        # issue warning, if any parameter (key) is left
        if replace != {}:
            remain_keys = ""
            for key in replace:
                remain_keys += " '%s'" % key

            raise KeyError("could not match all parameters:" + remain_keys)

    # def preset(self, instrument):
    #     """Set instrument specific default parameters"""
    #     self.reset()
    #     if instrument not in INSTRUMENTS:
    #         raise ValueError("instrument '%s' is not defined" % instrument)
    #     try:
    #         self.set(deepcopy(self.param_presets[instrument]))
    #     except KeyError:
    #         pass
