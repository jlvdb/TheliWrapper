"""
Provides a low level wrapper for the THELI GUI shell scripts that scannes their
output for known error messages
"""

import os
import sys
import subprocess
from inspect import stack

from .base import DIRS, LOCKFILE, LOGFILE, check_system_lock


ERR_KEYS = ["*Error*"]  # error keywords
ERR_EXCEPT = []  # keywords that are identified as error, but are not
# get keywords for errors and exceptions in logfile from Theli GUI source file
theliform_path = os.path.join(DIRS["PIPESOFT"], "gui", "theliform.ui.h")
with open(theliform_path) as cc:
    for line in cc.readlines():
        line = line.strip()
        # extract the strings from the c source file
        if line.startswith("errorlist"):
            statement = line.split('"', 1)[1].rsplit('"', 1)[0]
            ERR_KEYS.append(statement.replace('\\"', '"'))
        if line.startswith("falseerrorlist"):
            statement = line.split('"', 1)[1].rsplit('"', 1)[0]
            ERR_EXCEPT.append(statement.replace('\\"', '"'))
if len(ERR_KEYS) == 1 or len(ERR_EXCEPT) == 0:
    raise RuntimeError("could find error statements in %s" % theliform_path)


def checked_call(script, arglist=None, parallel=False, **kwargs):
    """Set up shell environment, call GUI script, capture log and scan it for
    possible errors.

    Arguments:
        script [string]:
            name of script to call
        arglist [list of strings]:
            list of arguments parsed to script
        parallel [bool]:
            weather script is run parallel using 'parallel_manager.sh'
        verb [ing]:
            verbosity level: 0: no output, 1: warnings messages, 2: full log
        env [dict]:
            dictionary of environment variables (see os.environ)
        ignoreerr [list of strings]:
            error keywords to ignore in log
        ignoremsg [list of strings]:
            message to display, if an error is ignored in log
    Returns:
        return_code [2-dim tuple]:
            line number and line text in which error occured, if no error
            occured, return (0, "")
        warnings [list of 2-dim tuple]:
            for each ignored error it contains a tuple with line and message
            to disply for an ignored error
    """
    check_system_lock()  # test if any other instance is running
    try:
        # create a lock file, prohibiting the system to run a parallel task
        os.system("touch %s 2>&1" % LOCKFILE)
        # parse kwargs: verbosity, environment, errors to ignore
        verbosity = kwargs["verb"] if "verb" in kwargs else 1
        env = kwargs["env"] if "env" in kwargs else os.environ.copy()
        ignoreerr = kwargs["ignoreerr"] if "ignoreerr" in kwargs else []
        ignoremsg = kwargs["ignoremsg"] if "ignoremsg" in kwargs else []
        # check requested script presence
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
        # highest verbosity level, dump all logs to stdout and log files
        if verbosity > 1:
            sys.stdout.write("\n")
            # read bytewise from pipe, buffer till newline, flush to stdout
            stdout = []
            line = b""
            while call.poll() is None:
                out = call.stdout.read(1)
                line += out
                if out == b'\n':  # if newline, flush line to stdout
                    strline = line.decode("utf-8")
                    sys.stdout.write(strline)
                    sys.stdout.flush()
                    stdout.append(strline.rstrip())
                    line = b""
            # capture remaining buffer
            if out != b'\n':
                line += b'\n'
                strline = line.decode("utf-8")
                sys.stdout.write(strline)
                sys.stdout.flush()
                stdout.append(strline.rstrip())
        else:  # capture log only
            stdout = call.communicate()[0].decode("utf-8").splitlines()
            stdout.append("")
    except Exception as e:
        raise e
    else:
        # scan log for errors
        return_code = (0, "")
        warnings = []
        for i, line in enumerate(stdout, 1):
            # check if line contains error message
            got_error = any(err in line for err in ERR_KEYS)
            is_false_detection = any(err in line for err in ERR_EXCEPT)
            # check if the error should explicitly be ignored
            if got_error and not is_false_detection:
                # error is valid
                if not any(ignore in line for ignore in ignoreerr):
                    return_code = (i, line)
                    break
                # error will be handled as warning
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


class Scripts(object):
    """Class containing wrapper functions for most common scripts provided
    by the THELI GUI. For each shell script argument there is a function
    argument and **kwargs to parse additional parameters to 'checked_call'.
    The functions are not further commented and usually take the main folder
    and data subfolders (like science, bias, flat, ... folder) as arguments."""

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
