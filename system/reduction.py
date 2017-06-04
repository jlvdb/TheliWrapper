"""
Defines the Reduction class that manages the data reduction process
"""

import os
import shutil
from time import sleep

from .base import *
from .instruments import Instrument
from .folder import Folder
from .parameters import Parameters
from .scripts import Scripts
from .version import __version__


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
                 reduce_skydir=False, ncpus=None, verbosity="normal",
                 logdisplay="none", parseparams={}):
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
        if instrument in INSTRUMENTS:
            self.instrument = Instrument(instrument)
            self.theli_env['INSTRUMENT'] = instrument
            self.nchips = self.instrument.NCHIPS
        else:
            print(self)
            self.display_error("instrument '%s' not implemented" % instrument)
            sys.exit(1)
        # specify number of threads to use and adjust maximum parallel frames
        self.set_cpus(ncpus)
        self.get_npara_max()
        # update the parameters file
        self.params = Parameters(parseparams)  # parse any default parameters
        pixscale = self.instrument.PIXSCALE
        crossid_rad = get_crossid_radius(pixscale)
        main_params = {'PROJECTNAME': title,
                       'NPARA': str(self.ncpus),
                       'NFRAMES': str(self.nframes),
                       'V_COADD_PIXSCALE': str(pixscale),
                       'V_SCAMP_CROSSIDRADIUS': str(crossid_rad)}
        # get the filters of files present in the science folder
        try:
            self.filters = list_filters(
                self.maindir, self.sciencedir.path, self.instrument.NAME)
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
        # how the log file should be displayed in case of an error
        if logdisplay not in ("none", "nano", "gedit", "kate", "emacs"):
            print(self)
            self.display_error(
                "unsupported text file display '%s'" % logdisplay)
            sys.exit(1)
        self.logdisplay = logdisplay
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
                "Instrument:", self.instrument.NAME, pad=PAD)
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

    def set_cpus(self, cpus):
        if cpus is None:
            self.ncpus = os.cpu_count()
        elif type(cpus) is int:
            self.ncpus = max(1, min(os.cpu_count(), cpus))
        else:
            self.ncpus = 1

    def get_npara_max(self):
        imsize = self.instrument.SIZEX * self.instrument.SIZEY * 4
        RAM = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
        self.nframes = int(0.4 * RAM / imsize / self.ncpus)

    def update_env(self, **kwargs):
        for key in kwargs:
            self.theli_env[key] = kwargs[key]

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

    def check_filters(self, datafolder, check_flat=False):
        # check, if only one filter is used in data folder
        if datafolder is not None:
            data_filters = datafolder.filters()
            if len(data_filters) > 1:
                self.display_error(
                    "Found observations with more than one filter in " +
                    datafolder.abs)
        # usefull for calibration
        if check_flat:
            flat_filters = self.flatdir.filters()
            # check, if only one filter is used in data folder
            if len(flat_filters) > 1:
                self.display_error(
                    "Found observations with more than one filter in flat "
                    "folder")
            # check if data folder filters match the flat fields
            if flat_filters != data_filters:
                self.display_error(
                    "The filters of the flat fields do not match the filters "
                    "in " + datafolder.abs)
            # do the same checks for the flat-off data if given
            if self.flatoffdir is not None:
                flatoff_filters = self.flatoffdir.filters()
                if len(flatoff_filters) > 1:
                    self.display_error(
                        "Found observations with more than one filter in flat-"
                        "off folder")
                if flatoff_filters != flat_filters:
                    self.display_error(
                        "The filters of the off-flat fields do not match the "
                        "flat field filters.")

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
            # display log file
            if self.logdisplay != "none":
                sys.stdout.write("displaying the log ")
                sys.stdout.flush()
                sleep(1)
                for i in range(3):
                    sys.stdout.write(".")
                    sys.stdout.flush()
                    sleep(1)
                sys.stdout.write("\n")
                sys.stdout.flush()
                if self.logdisplay == "nano":
                    if os.isatty(sys.stdout.fileno()):
                        command = ["nano", "+%d" % code[0], LOGFILE]
                    else:
                        self.display_error(
                            "cannot use 'nano' in this terminal")
                elif self.logdisplay == "gedit":
                    command = ["gedit", "+%d" % code[0], LOGFILE,
                               "/dev/null", "2>&1"]
                elif self.logdisplay == "kate":
                    command = ["kate", '-l', str(code[0]), LOGFILE,
                               "/dev/null", "2>&1"]
                elif self.logdisplay == "emacs":
                    command = ["emacs", "+%d" % code[0], LOGFILE,
                               "/dev/null", "2>&1"]
                try:
                    subprocess.call(command)
                except FileNotFoundError:
                    self.display_error(
                        "cannot stat text display '%s'" % self.logdisplay)
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
                self.instrument.NAME, self.maindir, folder.path,
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
        if self.instrument.TYPE != "NIR":
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
                if input_count < 3 and not apply_skydir:
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
        if self.instrument.TYPE != "NIR":
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
        if self.instrument.TYPE != "MIR":
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
        if self.instrument.TYPE != "OPT":
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
                        self.instrument.NAME, self.maindir, folder.path, tag,
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
        # BUG: this is not intended: if many science folders have a shared
        # WEIGHTS folder, the global weight will always be reused, if the
        # reduction steps are not done all at once
        found_output_files = False  # self.sciencedir.check_global_weight()
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
        # create a reference time spam of if old version of catalogue exists
        refcatpath = os.path.join(
            self.sciencedir.abs, "cat", "ds9cat", "theli_mystd.reg")
        try:
            refcat_timestamp = os.path.getctime(refcatpath)
        except Exception:
            refcat_timestamp = None
        # image reference
        if refcat == "Image":
            job_message = job_message + " (image)"
            # set up sextractor
            if imagepath is None:
                self.display_header(job_message)
                self.display_error("reference image path not specified")
                sys.exit(1)
            imagepath = os.path.abspath(imagepath)
            if not os.path.exists(imagepath):
                self.display_header(job_message)
                self.display_error(
                    "image for reference catalog creation does not exist: " +
                    imagepath)
                sys.exit(1)
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
                imagepath, dt, dmin, self.sciencedir.abs,
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
                if "Temporary failure in name resolution" in code[0][1]:
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
        # if reference catalogue does not cover the imaging area, no file
        # is created or the existing file does not change -> check time stemp
        if refcat_timestamp is not None:
            if refcat_timestamp == os.path.getctime(refcatpath):
                self.display_error(
                    "no sources returned, try a different catalogue")
                sys.exit(1)
        # exit if the returned source count is not sufficient
        try:
            with open(refcatpath) as cat:
                for numstars, line in enumerate(cat, -1):
                    pass
            if int(self.params.get("V_AP_LOWNUM")) >= numstars:
                self.display_error("recieved insufficient number of sources")
                sys.exit(1)
            else:
                ending = "detected" if refcat == "Image" else "retrieved"
                self.display_message(
                    "%d reference sources %s" % (numstars, ending))
        except Exception:
            self.display_error(
                    "no sources returned, try a different catalogue")
            sys.exit(1)
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
            # count average detections per exposure / mosaic
            catpath = os.path.join(folder.abs, "cat", "ds9cat")
            exposures = {}  # make list of chip belongig to exposure
            for file in os.listdir(catpath):
                if "theli" in file:  # ingore downloaded reference catalogue
                    continue
                base, tag = file.rsplit("_", 1)
                if base not in exposures:
                    exposures[base] = []
                exposures[base].append(tag)
            # sum the detections in all chips and average them
            chipcounts = []
            for exposure, chips in exposures.items():
                counts = 0  # objects per exposure / mosaic
                for chip in chips:
                    regfile = os.path.join(catpath, "%s_%s" % (exposure, chip))
                    # count lines of files (minus header line)
                    with open(regfile) as cat:
                        for i, lines in enumerate(cat):
                            pass
                    counts += i
                chipcounts.append(counts)
            # compute average detections
            detections = sum(chipcounts) // len(chipcounts)
            self.display_message("%d sources detected (avg.)" % detections)
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
