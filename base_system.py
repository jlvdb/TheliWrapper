"""
This is a python wrapper for the THELI GUI scripts, based
on the THELI package for astronomical image reduction.

TODO:
 -- implement photometry, header update/restore, const. sky subtraction helper
"""

import os
import sys
import shutil
import subprocess
from re import split
from fnmatch import fnmatch
from inspect import stack
from collections import namedtuple
from itertools import combinations
from time import time, sleep

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
__version__, __version_theli__, __version_gui__ = "0.3", "N/A", "N/A"
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


def checked_call(script, arglist=None, parallel=False, **kwargs):
    # test if the system is locked already
    check_system_lock()
    try:
        # create a lock file, prohibiting the system to run a parallel task
        os.system("touch %s 2>&1" % LOCKFILE)
        # parse kwargs
        verbosity = kwargs["verb"] if "verb" in kwargs else 1
        env = kwargs["env"] if "env" in kwargs else os.environ.copy()
        ignoreerr = kwargs["ignoreerr"] if "ignoreerr" in kwargs else []
        ignoremsg = kwargs["ignoremsg"] if "ignoremsg" in kwargs else []
        # check requested script
        scriptdir = DIRS["SCRIPTS"]
        if not os.path.exists(os.path.join(scriptdir, script)):
            raise FileNotFoundError("script does not exist:", script)
        # assamble command
        if parallel:
            cmdstr = [os.path.join(".", "parallel_manager.sh"), script]
        else:
            cmdstr = [os.path.join(".", script)]
        if arglist is not None:
            cmdstr.extend(arglist)
        # execute command and get log
        call = subprocess.Popen(
            cmdstr, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            shell=False, cwd=scriptdir, env=env)
        if verbosity > 1:
            sys.stdout.write("\n")
            # read bytewise from pipe, buffer till newline, flush to stdout
            stdout = []
            line = b""
            while call.poll() is None:
                out = call.stdout.read(1)
                line += out
                if out == b'\n':
                    strline = line.decode("utf-8")
                    sys.stdout.write(strline)
                    sys.stdout.flush()
                    stdout.append(strline.rstrip())
                    line = b""
            # capture unhandled buffer
            if out != b'\n':
                line += b'\n'
                strline = line.decode("utf-8")
                sys.stdout.write(strline)
                sys.stdout.flush()
                stdout.append(strline.rstrip())
        else:
            stdout = call.communicate()[0].decode("utf-8").splitlines()
            stdout.append("")
    except Exception as e:
        raise e
    else:
        # scan log for errors
        return_code = (0, "")
        warnings = []
        for i, line in enumerate(stdout, 1):
            got_error = any(err in line for err in ERR_KEYS)
            is_false_detection = any(err in line for err in ERR_EXCEPT)
            if got_error and not is_false_detection:
                if not any(ignore in line for ignore in ignoreerr):
                    return_code = (i, line)
                    break
                else:
                    for i, ignore in enumerate(ignoreerr, 1):
                        msg = ignoremsg[i - 1] if len(ignoremsg) >= i else ""
                        warnings.append([ignore, msg])
        # write out log
        caller = stack()[1][3]
        logfile = os.path.join(
            DIRS["PY2THELI"], "logs", "%s.log" % caller)
        with open(logfile, 'w') as log:
            # write header
            log.write("##" * 32 + "\n")
            log.write("##" + "{:^6}".format(caller + ".sh") + "##\n")
            log.write("##" * 32 + "\n\n")
            # write captured log
            for line in stdout:
                log.write(line + '\n')
        if os.path.exists(LOGFILE):
            os.remove(LOGFILE)
        os.symlink(logfile, LOGFILE)
        return return_code, warnings
    finally:
        # remove lock file
        os.system("rm %s 2>&1" % LOCKFILE)


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


class Scripts(object):

    @staticmethod
    def sort_rawdata(maindir, **kwargs):
        return checked_call(
            "sort_rawdata.sh",
            [maindir],
            parallel=False, **kwargs)

    @staticmethod
    def process_split(instrument, maindir, imdir, **kwargs):
        return checked_call(
            "process_split_%s.sh" % instrument,
            [maindir, imdir],
            parallel=False, **kwargs)

    @staticmethod
    def createlinks(wdir, scratchdir, chiptoscratch=1, **kwargs):
        return checked_call(
            "createlinks.sh",
            [wdir, scratchdir, str(int(chiptoscratch))],
            parallel=False, **kwargs)

    @staticmethod
    def check_files_para(maindir, imdir, tag, minmode, maxmode, **kwargs):
        return checked_call(
            "check_files_para.sh",
            [maindir, imdir, tag, str(minmode), str(maxmode)],
            parallel=True, **kwargs)

    @staticmethod
    def process_bias_para(maindir, biasdir, **kwargs):
        return checked_call(
            "process_bias_para.sh",
            [maindir, biasdir],
            parallel=True, **kwargs)

    @staticmethod
    def process_dark_para(maindir, darkdir, **kwargs):
        return checked_call(
            "process_dark_para.sh",
            [maindir, darkdir],
            parallel=True, **kwargs)

    @staticmethod
    def process_flat_para(maindir, biasdir, flatdir, **kwargs):
        return checked_call(
            "process_flat_para.sh",
            [maindir, biasdir, flatdir],
            parallel=True, **kwargs)

    @staticmethod
    def subtract_flat_flatoff_para(maindir, flatdir, flatoffdir, **kwargs):
        return checked_call(
            "subtract_flat_flatoff_para.sh",
            [maindir, flatdir, flatoffdir],
            parallel=True, **kwargs)

    @staticmethod
    def create_flat_ratio(maindir, flatdir, **kwargs):
        return checked_call(
            "create_flat_ratio.sh",
            [maindir, flatdir],
            parallel=False, **kwargs)

    @staticmethod
    def create_norm_para(maindir, flatdir, **kwargs):
        return checked_call(
            "create_norm_para.sh",
            [maindir, flatdir],
            parallel=True, **kwargs)

    @staticmethod
    def process_science_para(
            maindir, biasdarkdir, flatdir, sciencedir, **kwargs):
        return checked_call(
            "process_science_para.sh",
            [maindir, biasdarkdir, flatdir, sciencedir],
            parallel=True, **kwargs)

    @staticmethod
    def spread_squence(maindir, sciencedir, tag, ngroups, grouplen, **kwargs):
        return checked_call(
            "spread_sequence.sh",
            [maindir, sciencedir, tag, str(int(ngroups)), str(int(grouplen))],
            parallel=False, **kwargs)

    @staticmethod
    def id_bright_objects(maindir, sciencedir, tag="OFC", **kwargs):
        return checked_call(
            "id_bright_objects.sh",
            [maindir, sciencedir, tag],
            parallel=False, **kwargs)

    @staticmethod
    def process_background_para(
            maindir, sciencedir, skydir="noskydir", **kwargs):
        return checked_call(
            "process_background_para.sh",
            [maindir, sciencedir, skydir],
            parallel=True, **kwargs)

    @staticmethod
    def merge_sequence(maindir, sciencedir, tag, ngroups, **kwargs):
        return checked_call(
            "merge_sequence.sh",
            [maindir, sciencedir, tag, str(int(ngroups))],
            parallel=False, **kwargs)

    @staticmethod
    def process_science_chopnod_para(maindir, sciencedir, tag, pattern="0110",
                                     invert=False, **kwargs):
        invert = 1 if bool(invert) else 0
        if pattern not in ("0110", "1001", "0101", "1010"):
            raise ValueError("invalid chop-nod pattern:", pattern)
        return checked_call(
            "process_science_chopnod_para.sh",
            [maindir, sciencedir, tag, "P" + pattern, invert],
            parallel=True, **kwargs)

    @staticmethod
    def process_collapsecorr_para(maindir, sciencedir, tag, **kwargs):
        # need to revert before rerun
        return checked_call(
            "process_collapsecorr_para.sh",
            [maindir, sciencedir, tag],
            parallel=True, **kwargs)

    @staticmethod
    def create_debloomedimages_para(maindir, sciencedir, tag, threshold,
                                    **kwargs):
        return checked_call(
            "create_debloomedimages_para.sh",
            [maindir, sciencedir, tag, str(float(threshold))],
            parallel=True, **kwargs)

    @staticmethod
    def make_album(instrument, maindir, sciencedir, tag, **kwargs):
        return checked_call(
            "make_album_%s.sh" % instrument,
            [maindir, sciencedir, tag],
            parallel=False, **kwargs)

    @staticmethod
    def create_tiff(maindir, sciencedir, tag, **kwargs):
        return checked_call(
            "create_tiff.sh",
            [maindir, sciencedir, tag],
            parallel=False, **kwargs)

    @staticmethod
    def create_global_weights_para(maindir, flatnormdir, sciencedir, **kwargs):
        return checked_call(
            "create_global_weights_para.sh",
            [maindir, flatnormdir, sciencedir],
            parallel=True, **kwargs)

    @staticmethod
    def transform_ds9_reg(maindir, sciencedir, **kwargs):
        return checked_call(
            "transform_ds9_reg.sh",
            [maindir, sciencedir],
            parallel=False, **kwargs)

    @staticmethod
    def create_weights_para(maindir, sciencedir, tag, **kwargs):
        return checked_call(
            "create_weights_para.sh",
            [maindir, sciencedir, tag],
            parallel=True, **kwargs)

    @staticmethod
    def distribute_sets(maindir, sciencedir, tag, minoverlap, **kwargs):
        return checked_call(
            "distribute_sets.sh",
            [maindir, sciencedir, tag, str(float(minoverlap))],
            parallel=False, **kwargs)

    @staticmethod
    def create_astrorefcat_fromWEB(
            maindir, sciencedir, tag, refcat="SDSS-DR9",
            server="vizier.u-strasbg.fr", **kwargs):
        know_refcats = ("SDSS-DR9", "ISGL", "PPMXL", "USNO-B1", "2MASS",
                        "URATI", "SPM4", "UCAC4", "GSC-2.3", "TYC", "ALLSKY")
        if refcat not in know_refcats:
            raise ValueError(
                "unrecognized reference cataloge identifier:", refcat)
        server = "vizier.u-strasbg.fr" if refcat == "SDSS-DR9" else server
        return checked_call(
            "create_astrorefcat_fromWEB.sh",
            [maindir, sciencedir, tag, refcat, server],
            parallel=False, **kwargs)

    @staticmethod
    def create_astrorefcat_fromIMAGE(impath, dtmin, minarea, sciencedir,
                                     **kwargs):
        catpath = os.path.join(sciencedir, "cat")
        return checked_call(
            "create_astrorefcat_fromIMAGE.sh",
            [impath, str(float(dtmin)), str(float(minarea)), catpath],
            parallel=False, **kwargs)

    @staticmethod
    def create_photorefcat_fromWEB(maindir, sciencedir, tag,
                                   server="vizier.u-strasbg.fr", **kwargs):
        return checked_call(
            "create_photorefcat_fromWEB.sh",
            [maindir, sciencedir, tag, server],
            parallel=False, **kwargs)

    @staticmethod
    def create_astromcats_phot_para(maindir, sciencedir, tag, **kwargs):
        return checked_call(
            "create_astromcats_phot_para.sh",
            [maindir, sciencedir, tag],
            parallel=True, **kwargs)

    @staticmethod
    def create_stdphotom_prepare(maindir, sciencedir, tag, **kwargs):
        return checked_call(
            "create_stdphotom_prepare.sh",
            [maindir, sciencedir, tag],
            parallel=True, **kwargs)

    @staticmethod
    def create_abs_photo_info(maindir, standarddir, sciencedir, tag, **kwargs):
        return checked_call(
            "create_abs_photo_info.sh",
            [maindir, standarddir, sciencedir, tag],
            parallel=False, **kwargs)

    @staticmethod
    def create_photillcorr_corrcat_para(maindir, sciencedir, tag, **kwargs):
        return checked_call(
            "create_photillcorr_corrcat_para.sh",
            [maindir, sciencedir, tag],
            parallel=True, **kwargs)

    @staticmethod
    def create_photillcorr_getZP(maindir, sciencedir, tag, **kwargs):
        return checked_call(
            "create_photillcorr_getZP.sh",
            [maindir, sciencedir, tag],
            parallel=False, **kwargs)

    @staticmethod
    def correct_crval_para(maindir, sciencedir, tag, crval, **kwargs):
        return checked_call(
            "correct_crval_para.sh",
            [maindir, sciencedir, tag, crval],
            parallel=True, **kwargs)

    @staticmethod
    def create_astromcats_para(maindir, sciencedir, tag, **kwargs):
        return checked_call(
            "create_astromcats_para.sh",
            [maindir, sciencedir, tag],
            parallel=True, **kwargs)

    @staticmethod
    def create_scampcats(maindir, sciencedir, tag, **kwargs):
        # needed for multicolorchips
        return checked_call(
            "create_scampcats.sh",
            [maindir, sciencedir, tag],
            parallel=False, **kwargs)

    @staticmethod
    def create_scamp(
            maindir, sciencedir, tag, photometry_mode=False, **kwargs):
        scampmode = "photom" if photometry_mode else ""
        return checked_call(
            "create_scamp.sh",
            [maindir, sciencedir, tag, scampmode],
            parallel=False, **kwargs)

    @staticmethod
    def create_astrometrynet(maindir, sciencedir, tag, **kwargs):
        return checked_call(
            "create_astrometrynet.sh",
            [maindir, sciencedir, tag],
            parallel=True, **kwargs)

    @staticmethod
    def create_astrometrynet_photom(maindir, sciencedir, tag, **kwargs):
        return checked_call(
            "create_astrometrynet_photom.sh",
            [maindir, sciencedir, tag],
            parallel=False, **kwargs)

    @staticmethod
    def create_zeroorderastrom(maindir, sciencedir, tag, integer_shift=False,
                               **kwargs):
        precision = "int" if integer_shift else "float"
        return checked_call(
            "create_zeroorderastrom.sh",
            [maindir, sciencedir, tag, precision],
            parallel=False, **kwargs)

    @staticmethod
    def create_xcorrastrom(maindir, sciencedir, tag, **kwargs):
        return checked_call(
            "create_xcorrastrom.sh",
            [maindir, sciencedir, tag],
            parallel=False, **kwargs)

    @staticmethod
    def create_headerastrom(maindir, sciencedir, tag, **kwargs):
        return checked_call(
            "create_headerastrom.sh",
            [maindir, sciencedir, tag],
            parallel=False, **kwargs)

    @staticmethod
    def create_stats_table(
            maindir, sciencedir, tag, headerdir="headers", **kwargs):
        return checked_call(
            "create_stats_table.sh",
            [maindir, sciencedir, tag, headerdir],
            parallel=False, **kwargs)

    @staticmethod
    def create_absphotom_coadd(maindir, sciencedir, **kwargs):
        return checked_call(
            "create_absphotom_coadd.sh",
            [maindir, sciencedir],
            parallel=False, **kwargs)

    @staticmethod
    def get_constsky_helper(imdir, tag, instrument, ra1, ra2, dec1, dec2,
                            **kwargs):
        return checked_call(
            "get_constsky_helper.sh",
            [imdir, tag, instrument, str(float(ra1)), str(float(ra2)),
             str(float(dec1)), str(float(dec2))],
            parallel=False, **kwargs)

    @staticmethod
    def create_skysubconst_clean(maindir, sciencedir, **kwargs):
        return checked_call(
            "create_skysubconst_clean.sh",
            [maindir, sciencedir],
            parallel=False, **kwargs)

    @staticmethod
    def create_skysubconst_para(maindir, sciencedir, tag, **kwargs):
        return checked_call(
            "create_skysubconst_para.sh",
            [maindir, sciencedir, tag],
            parallel=True, **kwargs)

    @staticmethod
    def create_skysub_para(maindir, sciencedir, tag, **kwargs):
        # $4 and $5 in the script are dubious
        return checked_call(
            "create_skysub_para.sh",
            [maindir, sciencedir, tag],
            parallel=True, **kwargs)

    @staticmethod
    def create_smoothedge_para(maindir, sciencedir, tag, **kwargs):
        return checked_call(
            "create_smoothedge_para.sh",
            [maindir, sciencedir, tag],
            parallel=True, **kwargs)

    @staticmethod
    def prepare_coadd_swarp(maindir, sciencedir, tag, **kwargs):
        return checked_call(
            "prepare_coadd_swarp.sh",
            [maindir, sciencedir, tag],
            parallel=False, **kwargs)

    @staticmethod
    def resample_coadd_swarp_para(maindir, sciencedir, tag, **kwargs):
        return checked_call(
            "resample_coadd_swarp_para.sh",
            [maindir, sciencedir, tag],
            parallel=True, **kwargs)

    @staticmethod
    def resample_filtercosmics(maindir, sciencedir, **kwargs):
        return checked_call(
            "resample_filtercosmics.sh",
            [maindir, sciencedir],
            parallel=False, **kwargs)

    @staticmethod
    def perform_coadd_swarp(maindir, sciencedir, **kwargs):
        return checked_call(
            "perform_coadd_swarp.sh",
            [maindir, sciencedir],
            parallel=False, **kwargs)

    @staticmethod
    def update_coadd_header(maindir, sciencedir, tag, **kwargs):
        return checked_call(
            "update_coadd_header.sh",
            [maindir, sciencedir, tag],
            parallel=False, **kwargs)

    @staticmethod
    def resolvelinks(targetdir, prefix="", pattern="", **kwargs):
        return checked_call(
            "resample_filtercosmics.sh",
            [targetdir, prefix, pattern],
            parallel=False, **kwargs)


class Reduction(object):

    title = "unnamed"
    maindir = None
    sciencedir = None
    biasdir = None
    darkdir = None
    flatdir = None
    flatoffdir = None
    skydir = None
    stddir = None

    def __init__(self, instrument, maindir, title="auto",
                 biasdir=None, darkdir=None, flatdir=None, flatoffdir=None,
                 sciencedir=None, skydir=None, stddir=None,
                 reduce_skydir=False, ncpus="max", verbosity="normal",
                 parseparams={}):
        super(Reduction, self).__init__()
        # set the main folder
        self.maindir = os.path.abspath(maindir)
        if not os.path.isdir(maindir):
            self.display_error("main folder invalid:", self.maindir)
            sys.exit(1)
        maindir_subfs = tuple(d for d in os.listdir(self.maindir)
                              if os.path.isdir(os.path.join(self.maindir, d)))
        # set data folders (must be subfolders of main folder)
        folders = {'biasdir': 'bias folder', 'darkdir': 'dark folder',
                   'flatdir': 'flat folder', 'flatoffdir': 'flat (off) folder',
                   'sciencedir': 'science folder', 'skydir': 'sky folder',
                   'stddir': 'standard folder'}
        for folder, name in folders.items():
            input_folder = locals()[folder]
            if input_folder is None:
                continue
            # just interested in the folder name
            input_folder = os.path.normpath(input_folder)
            input_base, input_folder = os.path.split(input_folder)
            if input_base != '' and not self.maindir.endswith(input_base):
                print(self)
                self.display_error(
                    "%s: root folder differs from main folder: %s" %
                    (name, input_base))
                sys.exit(1)
            # test folder presence
            abspath = os.path.join(self.maindir, input_folder)
            if not os.path.exists(abspath):
                print(self)
                self.display_error(
                    "%s: not found: %s" % (name, abspath))
                sys.exit(1)
            # register a Folder instance
            setattr(self, folder, Folder(abspath))
        # set title
        if title == "auto":
            if self.sciencedir is not None:
                self.title = self.sciencedir.path
            else:
                self.title = "unnamed"
        else:
            self.title = title
        # set the environment and the instrument
        self.theli_env = os.environ.copy()
        if instrument in INSTRUMENTS.keys():
            self.instrument = instrument
            self.theli_env['INSTRUMENT'] = instrument
            self.nchips = INSTRUMENTS[self.instrument].NCHIPS
        else:
            print(self)
            self.display_error("instrument '%s' not recognized" % instrument)
            sys.exit(1)
        # specify number of threads to use and adjust maximum parallel frames
        self.set_cpus(ncpus)
        self.get_npara_max()
        # update the parameters file
        self.params = Parameters(parseparams)  # parse any default parameters
        pixscale = INSTRUMENTS[self.instrument].PIXSCALE
        crossid_rad = get_crossid_radius(pixscale)
        main_params = {'PROJECTNAME': title,
                       'NPARA': str(self.ncpus),
                       'NFRAMES': str(self.nframes),
                       'V_COADD_PIXSCALE': str(pixscale),
                       'V_SCAMP_CROSSIDRADIUS': str(crossid_rad)}
        # get the filters of files present in the science folder
        try:
            self.filters = list_filters(
                self.maindir, self.sciencedir.path, self.instrument)
            self.active_filter = self.filters[0]
            main_params['V_COADD_FILTER'] = self.active_filter
            main_params['V_COADD_IDENT'] = self.active_filter
        except ValueError:
            print(self)
            self.display_error("found no valid FITS files in science folder")
            sys.exit(1)
        except AttributeError:
            pass
        self.params.set(main_params)
        # empty temp folder
        remove_temp_files()
        # determine verbosity level
        self.verbosity = 1
        if verbosity in ("quiet", "normal", "full"):
            verb_modes = {"quiet": 0, "normal": 1, "full": 2}
            self.verbosity = verb_modes[verbosity]
        if self.verbosity > 0:
            self.display_message(self)
        # check if the sky folder should be fully reduced
        self.reduce_skydir = reduce_skydir
        if reduce_skydir:
            self.display_warning(
                "full sky folder processing not fully supported yet")
        # fix GUI issues
        #################
        # 'debloom' renamed to 'fitsdebloom' in THELI executable folders
        if not os.path.exists(os.path.join(DIRS["BIN"], "debloom")):
            try:
                os.symlink(
                    os.path.join(DIRS["BIN"], "fitsdebloom"),
                    os.path.join(DIRS["BIN"], "debloom"))
            except PermissionError:
                self.display_warning(
                    "Linking error correction: do not have the permission "
                    "to create links in '%s'\n" % DIRS["BIN"])

    def __str__(self):
        # print most important project parameters
        PAD = 20
        WIDTH = shutil.get_terminal_size((60, 24))[0]
        string = "\n"
        if self.title == "unnamed":
            string += ascii_styled("#" * WIDTH, "bb-")
        else:
            string += ascii_styled(
                "#" * (PAD - 2) + "  %s  " % self.title, "bb-")
            string += ascii_styled(
                "#" * (WIDTH - (PAD + 2) - len(self.title)), "bb-")
        string += "\n"
        if hasattr(self, "params"):
            string += "{:{pad}}version {:}".format(
                "Session info:", __version__, pad=PAD)
            if hasattr(self, "nframes") and hasattr(self, "ncpus"):
                string += ", {:}/{:} CPU(s), {:} FRAMES".format(
                    self.ncpus, os.cpu_count(), self.nframes)
            string += "\n"
        if hasattr(self, "instrument"):
            string += "{:{pad}}{:}\n".format(
                "Instrument:", self.instrument, pad=PAD)
        if self.maindir is not None:
            string += "{:{pad}}{:}\n".format(
                "Main folder:", self.maindir, pad=PAD)
        if self.biasdir is not None:
            string += "{:{pad}}{:}\n".format(
                "Bias folder:", self.biasdir.path, pad=PAD)
        if self.darkdir is not None:
            string += "{:{pad}}{:}\n".format(
                "Dark folder:", self.darkdir.path, pad=PAD)
        if self.flatdir is not None:
            string += "{:{pad}}{:}\n".format(
                "Flat folder:", self.flatdir.path, pad=PAD)
        if self.flatoffdir is not None:
            string += "{:{pad}}{:}\n".format(
                "Flat (off) folder:", self.flatoffdir.path, pad=PAD)
        if self.sciencedir is not None:
            string += "{:{pad}}{:}\n".format(
                "Science folder:", self.sciencedir.path, pad=PAD)
        if self.skydir is not None:
            string += "{:{pad}}{:}\n".format(
                "Sky folder:", self.skydir.path, pad=PAD)
        if self.stddir is not None:
            string += "{:{pad}}{:}\n".format(
                "Standard folder:", self.stddir.path, pad=PAD)
        if hasattr(self, "filters"):
            string += "{:{pad}}{:}\n".format(
                "Filter(s):", " / ".join(self.filters), pad=PAD)
        return string

    def change_filter(self, newfilter):
        # given name
        if type(newfilter) == str:
            if newfilter not in self.filters:
                self.error("'%s' not found in data" % newfilter)
        # given index
        else:
            if newfilter >= len(self.filters):
                self.error("index %d out range in filter list" % newfilter)
            newfilter = self.filters[newfilter]
        self.params.set({'V_COADD_IDENT': newfilter,
                         'V_COADD_FILTER': newfilter})
        self.active_filter = newfilter

    def update_env(self, **kwargs):
        for key in kwargs:
            self.theli_env[key] = kwargs[key]

    def set_cpus(self, cpus):
        if cpus == "max":
            self.ncpus = os.cpu_count()
        elif type(cpus) is int:
            self.ncpus = max(1, min(os.cpu_count(), cpus))
        else:
            self.ncpus = 1

    def get_npara_max(self):
        chipprop = INSTRUMENTS[self.instrument]
        imsize = chipprop.SIZEX * chipprop.SIZEY * 4
        RAM = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
        self.nframes = int(0.4 * RAM / imsize / self.ncpus)

    def display_header(self, message):
        if self.verbosity > 0:
            print(ascii_styled("> " + message, "bb-"))

    def display_message(self, message):
        if self.verbosity > 0:
            print(message)

    def display_separator(self):
        if self.verbosity > 0:
            print()

    def display_success(self, message, prefix="SKIPPED:"):
        if self.verbosity > 0:
            if prefix is not None:
                print(ascii_styled(prefix, "-g-"), message)
            else:
                print(message)

    def display_warning(self, message):
        if self.verbosity > 0:
            print(ascii_styled("WARNING:", "-y-"), message)

    def display_error(self, message, critical=True):
        if critical:
            print()
            stylestr = "br-"
        else:
            stylestr = "-r-"
        print(ascii_styled("ERROR:  ", stylestr), message)
        if critical:
            print()

    def check_return_code(self, code):
        code, warnings = code
        for warning in warnings:
            if warning[1] == '':
                self.display_warning(
                    "ignored error in line %s of log" % warning[0])
            else:
                self.display_warning(warning[1])
        if code[0] > 0:
            self.display_error(
                "found in line %d of log:\n         %s" %
                (code[0], LOGFILE))
            sys.stdout.write("displaying the log ")
            sys.stdout.flush()
            sleep(1)
            for i in range(3):
                sys.stdout.write(".")
                sys.stdout.flush()
                sleep(1)
            sys.stdout.write("\n")
            sys.stdout.flush()
            # try different text editors to display log file
            view_commands = []
            if os.isatty(sys.stdout.fileno()):
                view_commands.append(["nano", "+%d" % code[0], LOGFILE])
            view_commands.extend([
                ["gedit", "+%d" % code[0], LOGFILE, "/dev/null", "2>&1"],
                ["kate", '-l', str(code[0]), LOGFILE, "/dev/null", "2>&1"],
                ["emacs", "+%d" % code[0], LOGFILE, "/dev/null", "2>&1"]])
            for command in view_commands:
                try:
                    subprocess.call(command)
                    break
                except FileNotFoundError:
                    continue
            sys.exit(2)

    # ################## processing steps ##################

    def sort_data_using_FITS_key(self, params={}):
        """
        need any checks here?
        """
        self.params.set(params)
        self.display_header("Sorting raw data")
        code = Scripts.sort_rawdata(
            self.maindir,
            env=self.theli_env, verb=self.verbosity)
        self.check_return_code(code)
        self.display_separator()

    def split_FITS_correct_header(self, params={}):
        self.params.set(params)
        correct_xtalk = (
            self.params.get("V_PRE_XTALK_NOR_CHECKED") != '0' or
            self.params.get("V_PRE_XTALK_ROW_CHECKED") != '0' or
            self.params.get("V_PRE_XTALK_MULTI_CHECKED") != '0')
        foldervars = ['biasdir', 'darkdir', 'flatdir', 'flatoffdir',
                      'sciencedir', 'skydir', 'stddir']
        IDs = [' (bias)', ' (dark)', ' (flat)', ' (flat off)',
               ' (science)', ' (sky)', ' (standard)']
        for foldervar, ID in zip(foldervars, IDs):
            job_message = "Splitting FITS, correcting headers" + ID
            # folder verification
            folder = getattr(self, foldervar)
            if folder is None:
                continue
            filetags = folder.tags(ignore_sub=True)
            found_original_files = folder.contains_tag('none')
            found_split_files = folder.contains_tag('')
            found_split_dir = folder.contains("SPLIT_IMAGES")
            found_masterframe = folder.contains_master()
            # data verification
            if len(filetags) > 1:
                self.display_header(job_message)
                self.display_error("found multiple progress stages")
                sys.exit(1)
            if found_masterframe:
                self.display_header(job_message)
                self.display_success("master %s found" % ID[2:-1])
                continue
            if found_split_files or found_split_dir:
                self.display_header(job_message)
                self.display_success("split images found")
                continue
            if not found_original_files:
                self.display_header(job_message)
                self.display_error("no original images found")
                sys.exit(1)
            # run jobs
            # split images
            self.display_header(job_message)
            code = Scripts.process_split(
                self.instrument, self.maindir, folder.path,
                env=self.theli_env, verb=self.verbosity)
            self.check_return_code(code)
            if correct_xtalk:
                # optional: cross talk correction
                self.display_header("Correcting for crosstalk")
                raise NotImplementedError(
                    "Cross talk correction not implented yet")
        self.display_separator()

    def create_links(self, chip, target, params={}):
        self.params.set(params)
        job_message = "Creating links"
        try:
            chip = int(chip)
        except Exception:
            self.display_header(job_message)
            self.display_error("invalid chip specification:", chip)
            sys.exit(1)
        target = os.path.abspath(target)
        if not os.path.exists(target):
            try:
                os.mkdir(target)
            except Exception:
                self.display_header(job_message)
                self.display_error(
                    "could not create target folder '%s'" % target)
                sys.exit(1)
        foldervars = ['biasdir', 'darkdir', 'flatdir', 'flatoffdir',
                      'sciencedir', 'skydir', 'stddir']
        IDs = [' (bias)', ' (dark)', ' (flat)', ' (flat off)',
               ' (science)', ' (sky)', ' (standard)']
        for foldervar, ID in zip(foldervars, IDs):
            self.display_header(job_message + ID)
            folder = getattr(self, foldervar)
            code = Scripts.createlinks(
                folder.abs, target, chip,
                env=self.theli_env, verb=self.verbosity)
            self.check_return_code(code)
        self.display_separator()

    def process_biases(self, minmode=None, maxmode=None, redo=False,
                       params={}):
        self.params.set(params)
        job_message = "Processsing BIASes"
        # folder verification
        if self.biasdir is None:
            self.display_header(job_message)
            self.display_error("bias folder not specified")
            sys.exit(1)
        filetags = self.biasdir.tags(ignore_sub=True)
        found_split_files = self.biasdir.contains_tag('')
        found_masterbias = self.biasdir.contains_master()
        split_count = self.biasdir.fits_count()
        # data verification
        if len(filetags) > 1:
            self.display_header(job_message)
            self.display_error("found multiple progress stages")
            sys.exit(1)
        if not redo and found_masterbias:
            self.display_header(job_message)
            self.display_success("master bias found")
            self.display_separator()
            return
        if redo and found_masterbias and not found_split_files:
            self.display_header(job_message)
            self.display_warning("no split images found - skipping redo")
            self.display_separator()
            return
        if not found_split_files:
            self.display_header(job_message)
            self.display_error("no split images found")
            sys.exit(1)
        if split_count < 3:
            self.display_header(job_message)
            self.display_warning(
                "need at least 3 exposures - skipping redo")
            sys.exit(1)
        # run jobs
        if redo:
            self.biasdir.delete_master()
        if minmode is not None and maxmode is not None:
            # optional: brightness level check
            self.display_header("Checking brightness levels")
            code = Scripts.check_files_para(
                self.maindir, self.biasdir.path, "empty", minmode, maxmode,
                env=self.theli_env, verb=self.verbosity)
            self.check_return_code(code)
        # compute master bias
        self.display_header(job_message)
        code = Scripts.process_bias_para(
            self.maindir, self.biasdir.path,
            env=self.theli_env, verb=self.verbosity)
        self.check_return_code(code)
        self.display_separator()

    def process_darks(self, minmode=None, maxmode=None, redo=False, params={}):
        self.params.set(params)
        job_message = "Processsing DARKs"
        # folder verification
        if self.darkdir is None:
            self.display_header(job_message)
            self.display_error("dark folder not specified")
            sys.exit(1)
        filetags = self.darkdir.tags(ignore_sub=True)
        found_split_files = self.darkdir.contains_tag('')
        found_masterdark = self.darkdir.contains_master()
        split_count = self.biasdir.fits_count()
        # data verification
        if len(filetags) > 1:
            self.display_header(job_message)
            self.display_error("found multiple progress stages")
            sys.exit(1)
        if not redo and found_masterdark:
            self.display_header(job_message)
            self.display_success("master dark found")
            self.display_separator()
            return
        if redo and found_masterdark and not found_split_files:
            self.display_header(job_message)
            self.display_warning("no split images found - skipping redo")
            self.display_separator()
            return
        if not found_split_files:
            self.display_header(job_message)
            self.display_error("no split images found")
            sys.exit(1)
        if split_count < 3:
            self.display_header(job_message)
            self.display_warning(
                "need at least 3 exposures - skipping redo")
            sys.exit(1)
        # run jobs
        if redo:
            self.darkdir.delete_master()
        if minmode is not None and maxmode is not None:
            # optional: brightness level check
            self.display_header("Checking brightness levels")
            code = Scripts.check_files_para(
                self.maindir, self.biasdir.path, "empty", minmode, maxmode,
                env=self.theli_env, verb=self.verbosity)
            self.check_return_code(code)
        # compute master dark
        self.display_header(job_message)
        code = Scripts.process_dark_para(
            self.maindir, self.darkdir.path,
            env=self.theli_env, verb=self.verbosity)
        self.check_return_code(code)
        self.display_separator()

    def process_flats(self, minmode=None, maxmode=None, redo=False, params={}):
        self.params.set(params)
        # folder verification
        job_message = "Processsing FLATs"
        if self.flatdir is None:
            self.display_header(job_message)
            self.display_error("flat folder not specified")
            sys.exit(1)
        apply_bias = self.params.get("V_DO_BIAS") == "Y"
        if apply_bias:
            if self.biasdir is None:
                self.display_header(job_message)
                self.display_error("bias folder not specified")
                sys.exit(1)
            if not self.biasdir.contains_master():
                self.display_header(job_message)
                self.display_error("master bias not found")
                sys.exit(1)
        # queue data folders (optinal: have flatoff-dir)
        folders = [self.flatdir]
        IDs = [""]
        any_master_updated = False
        if self.flatoffdir is not None:
            folders.append(self.flatoffdir)
            IDs.append(" (off)")
        if len(IDs) > 1:
            IDs[0] = " (science)"
        for folder, ID in zip(folders, IDs):
            filetags = folder.tags(ignore_sub=True)
            found_split_files = folder.contains_tag('')
            found_masterflat = folder.contains_master()
            # check flat norm explicitly
            if ID == "":
                found_normflat = folder.search_flatnorm()
                found_masterflat = found_masterflat & found_normflat
            split_count = self.biasdir.fits_count()
            # data verification
            if len(filetags) > 1:
                self.display_header(job_message + ID)
                self.display_error("found multiple progress stages")
                sys.exit(1)
            if not redo and found_masterflat:
                self.display_header(job_message + ID)
                self.display_success("master flat found")
                continue
            if redo and found_masterflat and not found_split_files:
                self.display_header(job_message + ID)
                self.display_warning("no split images found - skipping redo")
                continue
            if not found_split_files:
                self.display_header(job_message + ID)
                self.display_error("no split images found")
                sys.exit(1)
            if split_count < 3:
                self.display_header(job_message + ID)
                self.display_warning(
                    "need at least 3 exposures - skipping redo")
                sys.exit(1)
            # run jobs
            if redo:
                folder.delete_master()
            if ID == "" and (minmode is not None and maxmode is not None):
                # optional: brightness level check (flat only)
                self.display_header("Checking brightness levels")
                code = Scripts.check_files_para(
                    self.maindir, self.biasdir.path, "empty", minmode, maxmode,
                    env=self.theli_env, verb=self.verbosity)
                self.check_return_code(code)
            # compute master flats (optional with flatoff)
            self.display_header(job_message + ID)
            code = Scripts.process_flat_para(
                self.maindir, self.biasdir.path, folder.path,
                env=self.theli_env, verb=self.verbosity)
            self.check_return_code(code)
            any_master_updated = True
        # if any master frame has been modified
        if any_master_updated:
            # optional: subtract flatoff from flat
            if self.flatoffdir is not None:
                self.display_header("Subtracting dark flat from bright flat")
                code = Scripts.subtract_flat_flatoff_para(
                    self.maindir, self.flatdir.path, self.flatoffdir.path,
                    self._ckwargs)
                self.check_return_code(code)
            # measure gain ratio
            self.display_header("Measuring gain ratios")
            code = Scripts.create_flat_ratio(
                self.maindir, self.flatdir.path,
                env=self.theli_env, verb=self.verbosity)
            self.check_return_code(code)
            # normalize flat
            self.display_header("Normalising FLAT")
            code = Scripts.create_norm_para(
                self.maindir, self.flatdir.path,
                env=self.theli_env, verb=self.verbosity)
            self.check_return_code(code)
        self.display_separator()

    def calibrate_data(self, usedark=False, minmode=None, maxmode=None,
                       redo=False, params={}):
        self.params.set(params)
        # folder verification
        job_message = "Calibrating data"
        if self.sciencedir is None:
            self.display_header(job_message)
            self.display_error("science folder not specified")
            sys.exit(1)
        apply_flat = self.params.get("V_DO_FLAT") == "Y"
        if apply_flat:
            if self.flatdir is None:
                self.display_header(job_message)
                self.display_error("flat folder not specified")
                sys.exit(1)
            if not self.flatdir.contains_master():
                self.display_header(job_message)
                self.display_error("master flat not found")
                sys.exit(1)
        biasdarkdir = self.darkdir if usedark else self.biasdir
        ID_biasdark = "dark" if usedark else "bias"
        apply_biasdark = self.params.get("V_DO_BIAS") == "Y"
        if apply_biasdark:
            if biasdarkdir is None:
                self.display_header(job_message)
                self.display_error("%s folder not specified" % ID_biasdark)
                sys.exit(1)
            if not biasdarkdir.contains_master():
                self.display_header(job_message)
                self.display_error("master %s not found" % ID_biasdark)
                sys.exit(1)
        # queue data folders (optinal: have flatoff-dir)
        folders = [self.sciencedir]
        IDs = [""]
        if self.skydir is not None:
            folders.append(self.skydir)
            IDs.append(" (sky)")
        if self.stddir is not None:
            folders.append(self.stddir)
            IDs.append(" (standard)")
        if len(IDs) > 1:
            IDs[0] = " (science)"
        for folder, ID in zip(folders, IDs):
            filetags = folder.tags(ignore_sub=True)
            # found_split_folder = folder.contains("SPLIT_IMAGES")
            found_split_files = folder.contains_tag('')
            found_OFC_folder = folder.contains("OFC_IMAGES")
            found_OFC_files = folder.contains_tag('OFC')
            # data verification
            if len(filetags) > 1:
                self.display_header(job_message + ID)
                self.display_error("found multiple progress stages")
                sys.exit(1)
            if not redo and (found_OFC_files or found_OFC_folder):
                self.display_header(job_message + ID)
                self.display_success("OFC images found")
                continue
            if redo and (found_OFC_files or found_OFC_folder) and \
                    not found_split_files:
                self.display_header(job_message + ID)
                self.display_warning("no split images found - skipping redo")
                continue
            if not found_split_files:
                self.display_header(job_message + ID)
                self.display_error("no split images found")
                sys.exit(1)
            # run jobs
            if redo:
                folder.move_tag("OF*", "OFC_IMAGES", ignore_sub=True)
                folder.lift_content("SPLIT_IMAGES")
            if ID == "" and (minmode is not None and maxmode is not None):
                # optional: brightness level check (science only)
                self.display_header("Checking brightness levels" + ID)
                code = Scripts.check_files_para(
                    self.maindir, folder.path, "empty", minmode, maxmode,
                    env=self.theli_env, verb=self.verbosity)
                self.check_return_code(code)
            # calibrate data
            self.display_header(job_message + ID)
            code = Scripts.process_science_para(
                self.maindir, biasdarkdir.path, self.flatdir.path, folder.path,
                env=self.theli_env, verb=self.verbosity)
            self.check_return_code(code)
        self.display_separator()

    def spread_sequence(self, ngroups, grouplen, params={}):
        self.params.set(params)
        job_message = "Grouping images"
        if INSTRUMENTS[self.instrument].TYPE != "NIR":
            self.display_header(job_message)
            self.display_error(
                "method only avaliable for NIR instruments", critical=False)
            self.display_separator()
            return
        # queue data folders
        if self.sciencedir is None:
            self.display_header(job_message)
            self.display_error("science folder not specified")
            sys.exit(1)
        folders = [self.sciencedir]
        IDs = [""]
        if self.stddir is not None:
            folders.append(self.stddir)
            IDs.append(" (sky)")
        if self.stddir is not None:
            folders.append(self.stddir)
            IDs.append(" (standard)")
        if len(IDs) > 1:
            IDs[0] = " (science)"
        for folder, ID in zip(folders, IDs):
            filetags = folder.tags(ignore_sub=True)
            found_OFC_files = folder.contains_tag('OFC')
            found_OFC_files = folder.contains_tag('OFC')
            found_sequence = os.path.exists(folder.abs + "_S1")
            # data verification
            if len(filetags) > 1:
                self.display_header(job_message + ID)
                self.display_error("found multiple progress stages")
                sys.exit(1)
            if found_sequence:
                count_sequence = folder.count_groups()
                self.display_header(job_message + ID)
                if count_sequence != ngroups:
                    self.display_error(
                        "found %d sequences, but %d are requested" %
                        (count_sequence, ngroups))
                    sys.exit(1)
                else:
                    self.display_success("found %d sequences" % count_sequence)
                    continue
            if not found_OFC_files:
                self.display_header(job_message + ID)
                self.display_error("no OFC images found")
                sys.exit(1)
            # run jobs
            tag = filetags.pop()
            self.display_header(job_message + ID)
            code = Scripts.spread_squence(
                self.maindir, folder.path, tag, ngroups, grouplen,
                env=self.theli_env, verb=self.verbosity)
            self.check_return_code(code)
        self.display_separator()

    def background_model_correction(self, redo=False, params={}):
        self.params.set(params)
        # folder verification
        job_message = "Background modeling"
        apply_skydir = self.skydir is not None
        apply_bright_star_filter = self.params.get("V_BACK_MAGLIMIT") != ""
        # queue data folders
        if self.sciencedir is None:
            self.display_header(job_message)
            self.display_error("science folder not specified")
            sys.exit(1)
        folders = [self.sciencedir]
        IDs = [""]
        if self.stddir is not None:
            folders.append(self.stddir)
            IDs.append(" (standard)")
        if len(IDs) > 1:
            IDs[0] = " (science)"
        for folder, ID in zip(folders, IDs):
            # make new iterator to account for possible sequences in NIR
            sequence = [Folder("%s_S%d" % (folder.abs, n + 1))
                        for n in range(folder.count_groups())]
            if len(sequence) == 0:
                sequence.append(folder)
            # loop over sequence folder(s)
            for n, seq in enumerate(sequence, 1):
                ID = " (science)" if ID == "" and len(sequence) > 1 else ""
                if len(sequence) > 1:
                    ID = " (%s %d)" % (ID[2:-1], n)
                filetags = seq.tags(ignore_sub=True)
                # found_input_folder = any(
                #     seq.contains(t + "_IMAGES") for t in THELI_TAGS["OFCB"])
                found_input_files = any(
                    seq.contains_tag(t) for t in THELI_TAGS["OFCB"])
                found_output_folder = any(
                    seq.contains(t + "B_IMAGES") for t in THELI_TAGS["OFCB"])
                found_output_files = any(
                    seq.contains_tag(t + "B") for t in THELI_TAGS["OFCB"])
                input_count = seq.fits_count()
                # data verification
                if len(filetags) > 1:
                    self.display_header(job_message + ID)
                    self.display_error("found multiple progress stages")
                    sys.exit(1)
                if not redo and (found_output_files or found_output_folder):
                    self.display_header(job_message + ID)
                    self.display_success("OFCB images found")
                    continue
                if redo and (found_output_files or found_output_folder) and \
                        not found_input_files:
                    self.display_header(job_message + ID)
                    self.display_warning("no OFC images found - skipping redo")
                    continue
                if not found_input_files:
                    self.display_header(job_message + ID)
                    self.display_error("no OFC images found")
                    sys.exit(1)
                if input_count < 3:
                    self.display_header(job_message + ID)
                    self.display_error(
                        "need at least 3 exposures", critical=False)
                    continue
                # run jobs
                tag = filetags.pop()
                if redo:
                    seq.move_tag(tag, tag + "_IMAGES", ignore_sub=True)
                    for foldertag in THELI_TAGS["OFCB"]:
                        if seq.contains(foldertag + "_IMAGES"):
                            seq.lift_content("")
                            break
                if ID == "" and apply_bright_star_filter:
                    # optional: remove chips with bright stars
                    self.display_header("Identifying chips with bright stars")
                    use_folder = (self.skydir.path if apply_skydir
                                  else self.sciencedir.path)
                    code = Scripts.id_bright_objects(
                        self.maindir, use_folder, tag,
                        env=self.theli_env, verb=self.verbosity)
                    self.return_code_check(code)
                # create background model
                self.display_header(job_message + ID)
                skydir = (self.skydir.path
                          if apply_skydir and ID == ""
                          else "noskydir")
                code = Scripts.process_background_para(
                    self.maindir, seq.path, skydir,
                    env=self.theli_env, verb=self.verbosity)
                self.check_return_code(code)
        self.display_separator()

    def merge_sequence(self, params={}):
        self.params.set(params)
        job_message = "Collecting images"
        if INSTRUMENTS[self.instrument].TYPE != "NIR":
            self.display_header(job_message)
            self.display_error(
                "method only avaliable for NIR instruments", critical=False)
            self.display_separator()
            return
        # queue data folders
        if self.sciencedir is None:
            self.display_header(job_message)
            self.display_error("science folder not specified")
            sys.exit(1)
        folders = [self.sciencedir]
        IDs = [""]
        if self.stddir is not None:
            folders.append(self.stddir)
            IDs.append(" (sky)")
        if self.stddir is not None:
            folders.append(self.stddir)
            IDs.append(" (standard)")
        if len(IDs) > 1:
            IDs[0] = " (science)"
        for folder, ID in zip(folders, IDs):
            filetags = folder.tags(ignore_sub=True)
            # found_OFC_files = folder.contains_tag('OFC')
            found_sequence = os.path.exists(folder.abs + "_S1")
            # data verification
            if len(filetags) > 1:
                self.display_header(job_message + ID)
                self.display_error("found multiple progress stages")
                sys.exit(1)
            if not found_sequence:
                self.display_header(job_message + ID)
                self.display_error("no sequence found")
                sys.exit(1)
            # run jobs
            tag = filetags.pop()
            ngroups = folder.count_groups()
            code = Scripts.process_science_para(
                self.maindir, folder.path, tag, ngroups,
                env=self.theli_env, verb=self.verbosity)
            self.check_return_code(code)
        self.display_separator()

    def chop_nod_skysub(self, pattern="0110", revert=False, redo=False,
                        params={}):
        self.params.set(params)
        job_message = "Subtracting sky by chop-nod"
        if INSTRUMENTS[self.instrument].TYPE != "MIR":
            self.display_header(job_message)
            self.error(
                "method only avaliable for MIR instruments", critical=False)
            self.display_separator()
            return
        # queue data folders
        if self.sciencedir is None:
            self.display_header(job_message)
            self.display_error("science folder not specified")
            sys.exit(1)
        folders = [self.sciencedir]
        IDs = [""]
        if self.skydir is not None and self.reduce_skydir:
            folders.append(self.skydir)
            IDs.append(" (sky)")
        if self.stddir is not None:
            folders.append(self.stddir)
            IDs.append(" (standard)")
        if len(IDs) > 1:
            IDs[0] = " (science)"
        for folder, ID in zip(folders, IDs):
            filetags = folder.tags(ignore_sub=True)
            # found_input_folder = any(
            #     folder.contains(t + "_IMAGES") for t in THELI_TAGS["OFCH"])
            found_input_files = any(
                folder.contains_tag(t) for t in THELI_TAGS["OFCH"])
            found_output_folder = any(
                folder.contains(t + "H_IMAGES") for t in THELI_TAGS["OFCH"])
            found_output_files = any(
                folder.contains_tag(t + "H") for t in THELI_TAGS["OFCH"])
            # data verification
            if len(filetags) > 1:
                self.display_header(job_message + ID)
                self.display_error("found multiple progress stages")
                sys.exit(1)
            if not redo and (found_output_files or found_output_folder):
                self.display_header(job_message + ID)
                self.display_success("OFC(B)H images found")
                continue
            if redo and (found_output_files or found_output_folder) and \
                    not found_input_files:
                self.display_header(job_message + ID)
                self.display_warning(
                    "no OFC(B) images found - skipping redo")
                continue
            if not found_input_files:
                self.display_header(job_message + ID)
                self.display_error("no OFC(B) images found")
                sys.exit(1)
            # run jobs
            tag = filetags.pop()
            if redo:
                folder.move_tag(tag, tag + "_IMAGES", ignore_sub=True)
                for foldertag in THELI_TAGS["OFCH"]:
                    if folder.contains(foldertag + "_IMAGES"):
                        folder.lift_content("")
                        break
            # create background model
            self.display_header(job_message + ID)
            if pattern not in ("0110", "1001", "0101", "1010"):
                self.display_error("invalid chop-nod pattern:", pattern)
            code = Scripts.process_science_chopnod_para(
                self.maindir, folder.path, tag, pattern, revert,
                env=self.theli_env, verb=self.verbosity)
            self.check_return_code(code)
        self.display_separator()

    def collapse_correction(self, redo=False, params={}):
        self.params.set(params)
        job_message = "Collapse correction"
        # queue data folders
        if self.sciencedir is None:
            self.display_header(job_message)
            self.display_error("science folder not specified")
            sys.exit(1)
        folders = [self.sciencedir]
        IDs = [""]
        if self.skydir is not None and self.reduce_skydir:
            folders.append(self.skydir)
            IDs.append(" (sky)")
        if self.stddir is not None:
            folders.append(self.stddir)
            IDs.append(" (standard)")
        if len(IDs) > 1:
            IDs[0] = " (science)"
        for folder, ID in zip(folders, IDs):
            filetags = folder.tags(ignore_sub=True)
            # found_input_folder = any(
            #     folder.contains(t + "_IMAGES") for t in THELI_TAGS["OFCC"])
            found_input_files = any(
                folder.contains_tag(t) for t in THELI_TAGS["OFCC"])
            found_output_folder = any(
                folder.contains(t + "C_IMAGES") for t in THELI_TAGS["OFCC"])
            found_output_files = any(
                folder.contains_tag(t + "C") for t in THELI_TAGS["OFCC"])
            # data verification
            if len(filetags) > 1:
                self.display_header(job_message + ID)
                self.display_error("found multiple progress stages")
                sys.exit(1)
            if not redo and (found_output_files or found_output_folder):
                self.display_header(job_message + ID)
                self.display_success("OFC(BH)C images found")
                continue
            if redo and (found_output_files or found_output_folder) and \
                    not found_input_files:
                self.display_header(job_message + ID)
                self.display_warning(
                    "no OFC(BH) images found - skipping redo")
                continue
            if not found_input_files:
                self.display_header(job_message + ID)
                self.display_error("no OFC(BH) images found")
                sys.exit(1)
            # run jobs
            tag = filetags.pop()
            if redo:
                folder.move_tag(tag, tag + "_IMAGES", ignore_sub=True)
                for foldertag in THELI_TAGS["OFCC"]:
                    if folder.contains(foldertag + "_IMAGES"):
                        folder.lift_content("")
                        break
            # create background model
            self.display_header(job_message + ID)
            code = Scripts.process_collapsecorr_para(
                self.maindir, folder.path, tag,
                env=self.theli_env, verb=self.verbosity)
            self.check_return_code(code)
        self.display_separator()

    def debloom_images(self, saturation=55000, redo=False, params={}):
        self.params.set(params)
        job_message = "Deblooming images"
        if INSTRUMENTS[self.instrument].TYPE != "OPT":
            self.message(job_message)
            self.error(
                "method only avaliable for optical instruments",
                critical=False)
            self.display_separator()
        # queue data folders
        if self.sciencedir is None:
            self.display_header(job_message)
            self.display_error("science folder not specified")
            sys.exit(1)
        folders = [self.sciencedir]
        IDs = [""]
        if self.skydir is not None and self.reduce_skydir:
            folders.append(self.skydir)
            IDs.append(" (sky)")
        if self.stddir is not None:
            folders.append(self.stddir)
            IDs.append(" (standard)")
        if len(IDs) > 1:
            IDs[0] = " (science)"
        for folder, ID in zip(folders, IDs):
            filetags = folder.tags(ignore_sub=True)
            # found_input_folder = any(
            #     folder.contains(t + "_IMAGES") for t in THELI_TAGS["OFCD"])
            found_input_files = any(
                folder.contains_tag(t) for t in THELI_TAGS["OFCD"])
            found_output_folder = any(
                folder.contains(t + "D_IMAGES") for t in THELI_TAGS["OFCD"])
            found_output_files = any(
                folder.contains_tag(t + "D") for t in THELI_TAGS["OFCD"])
            # data verification
            if len(filetags) > 1:
                self.display_header(job_message + ID)
                self.display_error("found multiple progress stages")
                sys.exit(1)
            if not redo and (found_output_files or found_output_folder):
                self.display_header(job_message + ID)
                self.display_success("OFC(BHC)D images found")
                continue
            if redo and (found_output_files or found_output_folder) and \
                    not found_input_files:
                self.display_header(job_message + ID)
                self.display_warning(
                    "no OFC(BHC) images found - skipping redo")
                continue
            if not found_input_files:
                self.display_header(job_message + ID)
                self.display_error("no OFC(BHC) images found")
                sys.exit(1)
            # run jobs
            tag = filetags.pop()
            if redo:
                folder.move_tag(tag, tag + "_IMAGES", ignore_sub=True)
                for foldertag in THELI_TAGS["OFCD"]:
                    if folder.contains(foldertag + "_IMAGES"):
                        folder.lift_content("")
                        break
            # debloom imags
            self.display_header(job_message + ID)
            code = Scripts.create_debloomedimages_para(
                self.maindir, folder.path, tag, saturation,
                env=self.theli_env, verb=self.verbosity)
            self.check_return_code(code)
        self.display_separator()

    def create_binned_preview(self, redo=False, params={}):
        self.params.set(params)
        job_message = "Creating tiff preview"
        # queue data folders (optinal: have standard-dir)
        if self.sciencedir is None:
            self.display_header(job_message)
            self.display_error("science folder not specified")
            sys.exit(1)
        folders = [self.sciencedir]
        IDs = [""]
        if self.skydir is not None and self.reduce_skydir:
            folders.append(self.skydir)
            IDs.append(" (sky)")
        if self.stddir is not None:
            folders.append(self.stddir)
            IDs.append(" (standard)")
        if len(IDs) > 1:
            IDs[0] = " (science)"
        for folder, ID in zip(folders, IDs):
            filetags = folder.tags(ignore_sub=True)
            found_output_files = folder.contains_preview()
            # data verification
            if len(filetags) < 1:
                self.display_header(job_message + ID)
                self.display_error("no images found")
                sys.exit(1)
            if not redo and found_output_files:
                self.display_header(job_message + ID)
                self.display_success("preview images found")
                continue
            for tag in filetags:
                # run jobs
                if redo:
                    folder.delete("BINNED_FITS")
                    folder.delete("BINNED_TIFF")
                tagID = " [%s]" % tag if len(filetags) > 1 else ""
                if self.nchips > 1:
                    # from multichip cameras: create fits preview
                    self.display_header("Creating fits preview" + ID + tagID)
                    code = Scripts.make_album(
                        self.instrument, self.maindir, folder.path, tag,
                        env=self.theli_env, verb=self.verbosity)
                    self.check_return_code(code)
                self.display_header(job_message + ID + tagID)
                code = Scripts.create_tiff(
                    self.maindir, folder.path, tag,
                    env=self.theli_env, verb=self.verbosity)
                self.check_return_code(code)
        self.display_separator()

    def create_global_weights(self, redo=False, params={}):
        self.params.set(params)
        # folder verification
        job_message = "Creating global WEIGHTs"
        if self.sciencedir is None:
            self.display_header(job_message)
            self.display_error("science folder not specified")
            sys.exit(1)
        use_flat = self.params.get("V_GLOBW_UNIFORMWEIGHT") == "FALSE"
        if use_flat:
            if self.flatdir is None:
                self.display_header(job_message)
                self.display_error("flat folder not specified")
                sys.exit(1)
            if not self.flatdir.contains_master():
                self.display_header(job_message)
                self.display_error("master flat not found")
                sys.exit(1)
        found_output_files = self.sciencedir.check_global_weight()
        # data verification
        if not redo and found_output_files:
            self.display_header(job_message)
            self.display_success("global weight maps found")
            self.display_separator()
            return
        # run jobs
        self.display_header(job_message)
        flatnormdir = str(self.flatdir.path) + "_norm"
        code = Scripts.create_global_weights_para(
            self.maindir, flatnormdir, self.sciencedir.path,
            env=self.theli_env, verb=self.verbosity)
        self.check_return_code(code)
        self.display_separator()

    def create_weights(self, redo=False, params={}):
        self.params.set(params)
        job_message = "Creating WEIGHTs"
        # queue data folders
        if self.sciencedir is None:
            self.display_header(job_message)
            self.display_error("science folder not specified")
            sys.exit(1)
        folders = [self.sciencedir]
        IDs = [""]
        if self.skydir is not None and self.reduce_skydir:
            folders.append(self.skydir)
            IDs.append(" (sky)")
        if self.stddir is not None:
            folders.append(self.stddir)
            IDs.append(" (standard)")
        if len(IDs) > 1:
            IDs[0] = " (science)"
        for folder, ID in zip(folders, IDs):
            filetags = folder.tags(ignore_sub=True)
            found_output_files = folder.check_weight()
            # data verification
            if not redo and found_output_files:
                self.display_header(job_message)
                self.display_success("weight maps found")
                continue
            # run jobs
            for tag in filetags:
                tagID = " [%s]" % tag if len(filetags) > 1 else ""
                self.display_header("Transforming DS9 masks" + ID + tagID)
                code = Scripts.transform_ds9_reg(
                    self.maindir, self.sciencedir.path,
                    env=self.theli_env, verb=self.verbosity)
                self.check_return_code(code)
                self.display_header(job_message + ID + tagID)
                code = Scripts.create_weights_para(
                    self.maindir, self.sciencedir.path, tag,
                    env=self.theli_env, verb=self.verbosity)
                self.check_return_code(code)
        self.display_separator()

    def distribute_target_sets(self, minoverlap, params={}):
        self.params.set(params)
        job_message = "Separating different target fields"
        # queue data folders
        if self.sciencedir is None:
            self.display_header(job_message)
            self.display_error("science folder not specified")
            sys.exit(1)
        folders = [self.sciencedir]
        IDs = [""]
        if self.skydir is not None and self.reduce_skydir:
            folders.append(self.skydir)
            IDs.append(" (sky)")
        if self.stddir is not None:
            folders.append(self.stddir)
            IDs.append(" (standard)")
        if len(IDs) > 1:
            IDs[0] = " (science)"
        for folder, ID in zip(folders, IDs):
            filetags = folder.tags(ignore_sub=True)
            # data verification
            if len(filetags) > 1:
                self.display_header(job_message + ID)
                self.display_error("found multiple progress stages")
                sys.exit(1)
            if len(filetags) < 1:
                self.display_header(job_message + ID)
                self.display_error("no images found")
                sys.exit(1)
            # run jobs
            tag = filetags.pop()
            self.display_header(job_message + ID)
            code = Scripts.distribute_sets(
                self.maindir, self.sciencedir.path, tag, minoverlap,
                env=self.theli_env, verb=self.verbosity)
            self.check_return_code(code)
        self.display_separator()

    def get_reference_catalog(
            self, refcat="SDSS-DR9", server="vizier.u-strasbg.fr",
            imagepath=None, dt=-1, dmin=-1, redo=False, params={}):
        """
        implement SKY
        - how to solve the problem in case of image reference (diff pointing)
        """
        self.params.set(params)
        job_message = "Creating astrometric reference catalog"
        if self.sciencedir is None:
            self.display_header(job_message)
            self.display_error("science folder not specified")
            sys.exit(1)
        # data verification
        filetags = self.sciencedir.tags(ignore_sub=True)
        found_refcat = self.sciencedir.contains_refcatfiles()
        if len(filetags) > 1:
            self.display_header(job_message)
            self.display_error("found multiple progress stages")
            sys.exit(1)
        if not redo and found_refcat:
            self.display_header(job_message)
            self.display_success("reference catalogue found")
            self.display_separator()
            return
        tag = filetags.pop()
        # image reference
        if refcat == "Image":
            job_message = job_message + " (image)"
            # set up sextractor
            if imagepath is None:
                self.display_header(job_message)
                self.display_error("reference image path not specified")
            imagepath = os.path.abspath(server)
            if not os.path.exists(imagepath):
                self.display_header(job_message)
                self.display_error(
                    "image for reference catalog creation does not exist")
            # run jobs
            self.display_header(job_message)
            message = []
            if dt <= 0:
                message.append("dt")
            if dmin <= 0:
                message.append("dmin")
            if len(message) > 0:
                self.display_warning(
                    "parameters " + ", ".join(message) +
                    " not set, use defaults")
            code = Scripts.create_astrorefcat_fromIMAGE(
                imagepath, dt, dmin, self.sciencedir.path,
                env=self.theli_env, verb=self.verbosity)
            self.check_return_code(code)
        # web reference
        else:
            job_message = job_message + " (web)"
            # set up web source
            known_servers = ("vizier.u-strasbg.fr", "vizier.cfa.harvard.edu",
                             "vizier.hia.nrc.ca", "vizier.nao.ac.jp",
                             "vizier.iucaa.ernet.in", "vizier.ast.cam.ac.uk",
                             "data.bao.ac.cn", "www.ukirt.jach.hawaii.edu",
                             "vizier.inasan.ru")
            known_refcats = ("SDSS-DR9", "ISGL", "PPMXL", "USNO-B1", "2MASS",
                             "URATI", "SPM4", "UCAC4", "GSC-2.3", "TYC")
            if refcat not in known_refcats:
                self.display_header(job_message)
                self.display_error(
                    "catalog '%s' not in list of registered catalogs" % refcat)
                sys.exit(1)
            if server not in known_servers:
                self.display_header(job_message)
                self.display_error(
                    "server '%s' not in list of registered servers" % server)
                sys.exit(1)
            # run jobs
            self.display_header(job_message)
            if refcat == "SDSS-DR9" and server != "vizier.u-strasbg.fr":
                server = "vizier.u-strasbg.fr"
                self.display_warning(
                    "switching to '%s' for catalog 'SDSS-DR9'" % server)
            if imagepath is not None or dt > 0 or dmin > 0:
                self.display_warning(
                    "imagepath, dt, dmin have no effect on web catalog")
            # 10 retries (with increasing waiting interval) if not connecting
            for i in range(11):
                code = Scripts.create_astrorefcat_fromWEB(
                    self.maindir, self.sciencedir.path, tag, refcat, server,
                    env=self.theli_env, verb=self.verbosity)
                # handle connection error
                if "Temporary failure in name resolution" in code[1]:
                    if i == 0:
                        sys.stdout.write(ascii_styled("WARNING: ", "-y-"))
                        sys.stdout.write("retry connecting to server ")
                        sys.stdout.flush()
                    elif i == 10:
                        print()
                        self.display_error(
                            "connecting to '%s' failed " % server +
                            "after 10 retries")
                        sys.exit(1)
                    else:
                        sys.stdout.write(".")
                        sys.stdout.flush()
                    # wait before reconnecting
                    sleep(5 + 50 * (i / 10))
                else:
                    if i > 0:
                        print()
                    break
            self.check_return_code(code)
        refcatpath = os.path.join(
            self.sciencedir.abs, "cat", "ds9cat", "theli_mystd.reg")
        with open(refcatpath) as cat:
            for numstars, line in enumerate(cat, -1):
                pass
        if int(self.params.get("V_AP_LOWNUM")) >= numstars:
            self.display_error("recieved insufficient number of sources")
            sys.exit(1)
        else:
            self.display_message("%d reference sources retrieved" % numstars)
        self.display_separator()

    def absolute_photometry_indirect(self, params={}):
        """
        # does not care for astrometry method

        # scripts
        # do ONLY THE LAST again for SKY:

        ./parallel_manager.sh create_astromcats_phot_para.sh
            /home/janluca/THELI_TRAINING/ACAM/ STANDARD OFCBCD
        if (command.find("create_astromcats_phot_para.sh") != -1)
        reply.append("Detecting sources for abs photometry ...");

            # if multichip
            ./create_scampcats.sh
                /home/janluca/THELI_TRAINING/ACAM/ STANDARD OFCBCD
            [...]

        ./create_scamp.sh
            /home/janluca/THELI_TRAINING/ACAM/ STANDARD OFCBCD photom
        [...]

        ./parallel_manager.sh create_stdphotom_prepare.sh
            /home/janluca/THELI_TRAINING/ACAM/ STANDARD OFCBCD
        if (command.find("create_stdphotom_prepare.sh") != -1)
        reply.append("Preparing photometry catalogs ...");

        ./create_abs_photo_info.sh
            /home/janluca/THELI_TRAINING/ACAM/ STANDARD SCIENCE OFCBCD
        if (command.find("create_abs_photo_info.sh") != -1)
        reply.append("Estimating indirect absolute zeropoints ...");
        """
        self.params.set(params)
        raise NotImplementedError()

    def absolute_photometry_direct(self, params={}):
        """
        # does not care for astrometry method

        Filename extension: After doing direct photometric calibration with
        FITTING METHOD = ZP for each chip, images have the character
        P appended to their filename extension

        # scripts
        # do the same again for SKY:

        ./create_photorefcat_fromWEB.sh
            /home/janluca/THELI_TRAINING/ACAM/ SCIENCE OFCBCD [dropdown - serv]
        [...]

        ./create_astrorefcat_fromWEB.sh
            /home/janluca/THELI_TRAINING/ACAM/ SCIENCE OFCBCD
                [dropdown - cat] [dropdown - serv]
        [...]

        ./parallel_manager.sh create_astromcats_phot_para.sh
            /home/janluca/THELI_TRAINING/ACAM/ SCIENCE OFCBCD
        if (command.find("create_astromcats_phot_para.sh") != -1)
        reply.append("Detecting sources for abs photometry ...");

            # if multichip
            ./create_scampcats.sh
                /home/janluca/THELI_TRAINING/ACAM/ SCIENCE OFCBCD
            [...]

        ./create_scamp.sh /home/janluca/THELI_TRAINING/ACAM/ SCIENCE OFCBCD
        [...]

        ./parallel_manager.sh
            create_photillcorr_corrcat_para.sh /home/janluca/THELI
                TRAINING/ACAM/ SCIENCE OFCBCD
        if (command.find("create_photillcorr_corrcat_para.sh") != -1)
        reply.append("Correcting astrometry in catalogs ...");

        ./create_photillcorr_getZP.sh
            /home/janluca/THELI_TRAINING/ACAM/ SCIENCE OFCBCD
        if (command.find("create_photillcorr_getZP.sh") != -1)
        reply.append("Estimating direct absolute zeropoints ...");
        """
        self.params.set(params)
        raise NotImplementedError()

    def create_source_cat(self, redo=False, params={}):
        """
        # THIS IS A PROBLEM FOR SKY AND STANDARD (different pointing)
        # use in create_source_cat, if refRA/DEC not "from header"
        ./parallel_manager.sh correct_crval_para.sh
            /home/janluca/THELI_TRAINING/ACAM/ SCIENCE OFCBCD
        if (command.find("correct_crval_para.sh") != -1)
        reply.append("Adjusting CRVAL1/2 key in header ...");
        """
        self.params.set(params)
        job_message = "Detecting sources"
        # queue data folders
        if self.sciencedir is None:
            self.display_header(job_message)
            self.display_error("science folder not specified")
            sys.exit(1)
        folders = [self.sciencedir]
        IDs = [""]
        if self.skydir is not None and self.reduce_skydir:
            folders.append(self.skydir)
            IDs.append(" (sky)")
        if len(IDs) > 1:
            IDs[0] = " (science)"
        for folder, ID in zip(folders, IDs):
            filetags = folder.tags(ignore_sub=True)
            found_cat = folder.contains_catfiles()
            # data verification
            if len(filetags) > 1:
                self.display_header(job_message + ID)
                self.display_error("found multiple progress stages")
                sys.exit(1)
            if not redo and found_cat:
                self.display_header(job_message + ID)
                self.display_success("image catalogues found")
                continue
            # run jobs
            for tag in filetags:
                tagID = " [%s]" % tag if len(filetags) > 1 else ""
                self.display_header(job_message + ID + tagID)
                code = Scripts.create_astromcats_para(
                    self.maindir, self.sciencedir.path, tag,
                    env=self.theli_env, verb=self.verbosity)
                self.check_return_code(code)
                if self.nchips > 1:
                    self.display_header(
                        "Merging multi-chip object catalogs" + ID + tagID)
                    code = Scripts.create_scampcats(
                        self.maindir, self.sciencedir.path, tag,
                        env=self.theli_env, verb=self.verbosity)
                    self.check_return_code(code)
        self.display_separator()

    def astro_and_photometry(self, method="scamp", ignore_scamp_segfault=False,
                             redo=False, params={}):
        """
        reload refcat from web if we have sky processing as well
        """
        self.params.set(params)
        job_message = "Calculating astrometric solution"
        known_methods = (
            "scamp", "astrometry.net", "shift (float)", "shift (int)",
            "xcoor", "header")
        if method not in known_methods:
            self.display_header(job_message)
            self.display_error(
                "method '%s' not in list of registered methods" % method)
            sys.exit(1)
        # queue data folders
        if self.sciencedir is None:
            self.display_header(job_message)
            self.display_error("science folder not specified")
            sys.exit(1)
        folders = [self.sciencedir]
        IDs = [""]
        if self.skydir is not None and self.reduce_skydir:
            folders.append(self.skydir)
            IDs.append(" (sky)")
        if len(IDs) > 1:
            IDs[0] = " (science)"
        for folder, ID in zip(folders, IDs):
            filetags = folder.tags(ignore_sub=True)
            found_headers = folder.contains_astrometry()
            # data verification
            if len(filetags) > 1:
                self.display_header(job_message + ID)
                self.display_error("found multiple progress stages")
                sys.exit(1)
            if not redo and found_headers:
                self.display_header(job_message + ID)
                self.display_success("astrometric headers found")
                continue
            # run jobs
            for tag in filetags:
                tagID = " [%s]" % tag if len(filetags) > 1 else ""
                if method == "scamp":
                    self.display_header(job_message + ID + tagID)
                    code = Scripts.create_scamp(
                        self.maindir, self.sciencedir.path, tag, False,
                        env=self.theli_env, verb=self.verbosity,
                        ignoreerr=["Segmentation fault"],
                        ignoremsg=["ignored segmentation fault in scamp"])
                    self.check_return_code(code)
                elif method == "astrometry.net":
                    self.display_header(job_message + ID + tagID)
                    code = Scripts.create_astrometrynet(
                        self.maindir, self.sciencedir.path, tag,
                        env=self.theli_env, verb=self.verbosity)
                    self.check_return_code(code)
                    self.display_header(
                        "Calculating photometric solution" + ID + tagID)
                    code = Scripts.create_astrometrynet_photom(
                        self.maindir, self.sciencedir.path, tag,
                        env=self.theli_env, verb=self.verbosity)
                    self.check_return_code(code)
                elif method.startswith("shift"):
                    integer_shift = True if method.endswith("(int)") else False
                    self.display_header(job_message + ID + tagID)
                    code = Scripts.create_zeroorderastrom(
                        self.maindir, self.sciencedir.path, tag, integer_shift,
                        env=self.theli_env, verb=self.verbosity)
                    self.check_return_code(code)
                elif method == "xcorr":
                    self.display_header(job_message + ID + tagID)
                    code = Scripts.create_xcorrastrom(
                        self.maindir, self.sciencedir.path, tag,
                        env=self.theli_env, verb=self.verbosity)
                    self.check_return_code(code)
                elif method == "header":
                    self.display_header(job_message + ID + tagID)
                    code = Scripts.create_headerastrom(
                        self.maindir, self.sciencedir.path, tag,
                        env=self.theli_env, verb=self.verbosity)
                    self.check_return_code(code)
                self.display_header("Collecting image statistics" + ID + tagID)
                code = Scripts.create_stats_table(
                    self.maindir, self.sciencedir.path, tag, "headers",
                    env=self.theli_env, verb=self.verbosity)
                self.check_return_code(code)
                self.display_header(
                    "Collecting information for coaddition" + ID + tagID)
                code = Scripts.create_absphotom_coadd(
                    self.maindir, self.sciencedir.path,
                    env=self.theli_env, verb=self.verbosity)
                self.check_return_code(code)
        self.display_separator()

    def astrometry_update_header(self, params={}):
        """
        see: void theliForm::update_zeroheader
        """
        self.params.set(params)
        raise NotImplementedError()

    def astrometry_restore_header(self, params={}):
        """
        see: void theliForm::restore_header
        """
        self.params.set(params)
        raise NotImplementedError()

    def sky_subtraction_helper(self, params={}):
        """
        for subtracting a constant sky
        THELI/gui/manualsky.ui.h
        305 :  execstr.append("./get_constsky_helper.sh ");
        """
        self.params.set(params)
        raise NotImplementedError()

    def sky_subtraction(self, use_constant_model=False, redo=False, params={}):
        self.params.set(params)
        job_message = "Subtracting the sky"
        # queue data folders
        if self.sciencedir is None:
            self.display_header(job_message)
            self.display_error("science folder not specified")
            sys.exit(1)
        folders = [self.sciencedir]
        IDs = [""]
        if self.skydir is not None and self.reduce_skydir:
            folders.append(self.skydir)
            IDs.append(" (sky)")
        if len(IDs) > 1:
            IDs[0] = " (science)"
        for folder, ID in zip(folders, IDs):
            filetags = folder.tags(ignore_sub=True)
            found_input_files = any(
                folder.contains_tag(t) for t in THELI_TAGS["OFC.sub"])
            found_output_files = any(
                folder.contains_tag(t + ".sub") for t in THELI_TAGS["OFC.sub"])
            # data verification
            if len(filetags) > 1:
                self.display_header(job_message + ID)
                self.display_error("found multiple progress stages")
                sys.exit(1)
            if not redo and found_output_files:
                self.display_header(job_message + ID)
                self.display_success("OFC(BHCP).sub images found")
                continue
            if redo and found_output_files and not found_input_files:
                self.display_header(job_message + ID)
                self.display_warning(
                    "no OFC(BHCP) images found - skipping redo")
                continue
            if not found_input_files:
                self.display_header(job_message + ID)
                self.display_error("no OFC(BHCP) images found")
                sys.exit(1)
            # run jobs
            for tag in filetags:
                tagID = " [%s]" % tag if len(filetags) > 1 else ""
                if redo:
                    folder.delete_tag("*.sub")
                # constant background model
                if use_constant_model:
                    self.display_header(
                        "Preparing sky subtraction" + ID + tagID)
                    code = Scripts.create_skysubconst_clean(
                        self.maindir, self.sciencedir.path,
                        env=self.theli_env, verb=self.verbosity)
                    self.check_return_code(code)
                    self.display_header(job_message + ID + tagID)
                    code = Scripts.create_skysubconst_para(
                        self.maindir, self.sciencedir.path, tag,
                        env=self.theli_env, verb=self.verbosity)
                    self.check_return_code(code)
                # variable background model
                else:
                    self.display_header(job_message + ID + tagID)
                    code = Scripts.create_skysub_para(
                        self.maindir, self.sciencedir.path, tag,
                        env=self.theli_env, verb=self.verbosity)
                    self.check_return_code(code)
        self.display_separator()

    def coaddition(self, posangle_from_image=False, redo=False, params={}):
        self.params.set(params)
        job_message = "Coadding images"
        do_edge_smoothing = self.params.get("V_COADD_SMOOTHEDGE") != ""
        do_cosmics_filtering = self.params.get("V_COADD_FILTERTHRESHOLD") != ""
        # queue data folders
        if self.sciencedir is None:
            self.display_header(job_message)
            self.display_error("science folder not specified")
            sys.exit(1)
        folders = [self.sciencedir]
        IDs = [""]
        if self.skydir is not None and self.reduce_skydir:
            folders.append(self.skydir)
            IDs.append(" (sky)")
        if len(IDs) > 1:
            IDs[0] = " (science)"
        for folder, ID in zip(folders, IDs):
            filetags = folder.tags(ignore_sub=True)
            found_input_files = any(
                folder.contains_tag(t) for t in THELI_TAGS["OFC.sub"])
            found_weights = folder.check_weight()
            found_headers = folder.contains("headers")
            found_output_files = folder.contains_coadds()
            # data verification
            if len(filetags) > 1:
                self.display_header(job_message + ID)
                self.display_error("found multiple progress stages")
                sys.exit(1)
            if not redo and found_output_files:
                self.display_header(job_message + ID)
                self.display_success("coadd images found")
                continue
            if redo and found_output_files and not found_input_files:
                self.display_header(job_message + ID)
                self.display_warning(
                    "no OFC(BHCP) images found - skipping redo")
                continue
            if redo and found_output_files and not found_weights:
                self.display_header(job_message + ID)
                self.display_warning(
                    "no weight maps found - skipping redo")
                continue
            if redo and found_output_files and not found_headers:
                self.display_header(job_message + ID)
                self.display_warning(
                    "no astrometric header files found - skipping redo")
                continue
            if not found_input_files:
                self.display_header(job_message + ID)
                self.display_error("no OFC(BHCP) images found")
                sys.exit(1)
            if not found_weights:
                self.display_header(job_message + ID)
                self.display_error("no weight maps found")
                sys.exit(1)
            if not found_headers:
                self.display_header(job_message + ID)
                self.display_error("no astrometric header files found")
                self.exit(1)
            # run jobs
            tag = filetags.pop()
            if redo:
                filterstr = self.params.get("V_COADD_IDENT")
                if filterstr == "(null)":
                    filterstr = "null"
                folder.delete("coadd_" + filterstr)
            if do_edge_smoothing:
                # smooth chip edges
                self.display_header("Coaddition: smoothing overlap" + ID)
                code = Scripts.create_smoothedge_para(
                    self.maindir, self.sciencedir.path, tag,
                    env=self.theli_env, verb=self.verbosity)
                self.check_return_code(code)
            # resampling
            subtag = tag + ".sub" if folder.contains_tag(tag + ".sub") else tag
            self.display_header("Coaddition: initialising" + ID)
            if posangle_from_image:
                # get position angle of image
                angle = get_posangle(os.path.join(folder.abs, "headers"))
                if angle == -999:
                    self.display_warning(
                        "sky position angle could not be obtained")
                    angle = 0
                self.params.set({"V_COADD_SKYPOSANGLE": str(angle)})
            code = Scripts.prepare_coadd_swarp(
                self.maindir, self.sciencedir.path, subtag,
                env=self.theli_env, verb=self.verbosity)
            self.check_return_code(code)
            self.display_header("Coaddition: resampling images" + ID)
            code = Scripts.resample_coadd_swarp_para(
                self.maindir, self.sciencedir.path, subtag,
                env=self.theli_env, verb=self.verbosity)
            self.check_return_code(code)
            if do_cosmics_filtering:
                # filter outliers
                self.display_header("Coaddition: rejecting outliers" + ID)
                code = Scripts.resample_filtercosmics(
                    self.maindir, self.sciencedir.path,
                    env=self.theli_env, verb=self.verbosity)
                self.check_return_code(code)
            # coaddition
            self.display_header("Coaddition: coadding images" + ID)
            code = Scripts.perform_coadd_swarp(
                self.maindir, self.sciencedir.path,
                env=self.theli_env, verb=self.verbosity)
            self.check_return_code(code)
            self.display_header("Coaddition: updating header" + ID)
            code = Scripts.update_coadd_header(
                self.maindir, self.sciencedir.path, tag,
                env=self.theli_env, verb=self.verbosity)
            self.check_return_code(code)
        self.display_separator()

    def resolve_links(self, params={}):
        # if (command.find("resolvelinks.sh") != -1)
        # reply.append("Resolving link structure ...");
        self.params.set(params)
        raise NotImplementedError()
