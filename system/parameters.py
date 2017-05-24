"""
Defines the parameter manager for the Reduction class
"""

import os
from copy import copy
from platform import uname

from .base import DIRS, check_system_lock


class Parameters(object):
    """Controlls the THELI configuration files for easy reading, writing and
    restoring default values.

    Arguments:
        preparse [dict]:
            parameter dict (key: variable name, value: value) to initialize
            configureation files.
    """

    param_sets_default = {
        "param_set1.ini": [
            "PROJECTNAME=\n",
            "NPARA=\n",
            "GUIVERSION=\n",
            "KERNEL=\n",
            "NFRAMES=\n",
            "V_PRE_SPLITMIRCUBE=N\n",
            "V_DO_BIAS=Y\n",
            "V_DO_FLAT=Y\n",
            "V_NONLINCORR=N\n",
            "V_AP_SERVER=vizier.u-strasbg.fr\n",
            "V_AP_MAGLIM=20\n",
            "V_AP_RADIUS=\n",
            "V_AP_REFRA=header\n",
            "V_AP_REFDEC=header"],
        "param_set2.ini": [
            "V_PRE_RENAME_CHECKED=0\n",
            "V_RENAME_FITSKEY=ARCFILE\n",
            "V_SORT_FITSKEY=OBJECT\n",
            "V_SORT_BIAS=\n",
            "V_SORT_DARK=\n",
            "V_SORT_DOMEFLAT=\n",
            "V_SORT_SKYFLAT=\n",
            "V_SORT_STD=\n",
            "V_PRE_XTALK_NOR_CHECKED=0\n",
            "V_PRE_XTALK_ROW_CHECKED=0\n",
            "V_PRE_XTALK_MULTI_CHECKED=0\n",
            "V_PRE_XTALK_NOR_AMPLITUDE=\n",
            "V_PRE_XTALK_ROW_AMPLITUDE=\n",
            "V_PRE_XTALK_NOR_BUTTONID=-1\n",
            "V_PRE_XTALK_ROW_BUTTONID=-1\n",
            "V_PRE_XTALK_MULTI_BUTTONID=-1\n",
            "V_PRE_XTALK_MULTI_NSECTION=\n",
            "V_CAL_OVSCANNLOW=0\n",
            "V_CAL_OVSCANNHIGH=1\n",
            "V_CAL_BIASNLOW=0\n",
            "V_CAL_BIASNHIGH=1\n",
            "V_CAL_DARKNLOW=0\n",
            "V_CAL_DARKNHIGH=1\n",
            "V_CAL_FLATNLOW=0\n",
            "V_CAL_FLATNHIGH=1\n",
            "V_BACK_NLOW1=0\n",
            "V_BACK_NHIGH1=0\n",
            "V_BACK_NLOW2=0\n",
            "V_BACK_NHIGH2=1\n",
            "V_BACK_MAGLIMIT=\n",
            "V_BACK_DISTANCE=\n",
            "V_BACK_SERVER=vizier.u-strasbg.fr\n",
            "V_BACK_DETECTTHRESH=1.3\n",
            "V_BACK_DETECTMINAREA=5\n",
            "V_BACK_MASKEXPAND=\n",
            "V_BACK_ILLUMSMOOTH=\n",
            "V_BACK_FRINGESMOOTH=\n",
            "V_BACK_WINDOWSIZE=0\n",
            "V_BACK_GAPSIZE=\n",
            "V_BACK_APPLYMODE=0\n",
            "V_BACK_COMBINEMETHOD=Median\n",
            "V_BACK_SEXFILTER=Y\n",
            "V_BACK_ADJUSTGAINS=N\n",
            "V_BACK_FRINGESCALE=Y\n",
            "V_BACK_TWOPASS=Y\n",
            "V_COLLDETECTTHRESH=\n",
            "V_COLLDETECTMINAREA=\n",
            "V_COLLMASKEXPAND=\n",
            "V_COLLREJECTTHRESH=1.5\n",
            "V_COLLXMIN=\n",
            "V_COLLXMAX=\n",
            "V_COLLYMIN=\n",
            "V_COLLYMAX=\n",
            "V_COLLDIRECTION=x\n",
            "V_COLLMASKACTION=1\n",
            "V_COLLAUTOTHRESHOLD=0\n",
            "V_WEIGHTLOWTHRESHOLD=\n",
            "V_WEIGHTHIGHTHRESHOLD=\n",
            "V_WEIGHTBINMIN=-100\n",
            "V_WEIGHTBINMAX=500\n",
            "V_GLOBWFLATMIN=0.5\n",
            "V_GLOBWFLATMAX=1.6\n",
            "V_GLOBWDARKMIN=\n",
            "V_GLOBWDARKMAX=\n",
            "V_WEIGHTBINSIZE=4\n",
            "V_DEFECT_KERNELSIZE=\n",
            "V_DEFECT_ROWTOL=\n",
            "V_DEFECT_COLTOL=\n",
            "V_DEFECT_CLUSTOL=\n",
            "V_DEFECT_KERNELSIZE_SF=\n",
            "V_DEFECT_ROWTOL_SF=\n",
            "V_DEFECT_COLTOL_SF=\n",
            "V_DEFECT_CLUSTOL_SF=\n",
            "V_COSMICSTHRESHOLD=0.1\n",
            "V_COSMICDT=6\n",
            "V_COSMICDMIN=1\n",
            "V_BLOOMLOWLIMIT=20000\n",
            "V_BLOOMMINAREA=100\n",
            "V_BLOOMWIDTH=0\n",
            "V_WEIGHT_BINOUTLIER=FALSE\n",
            "V_MASKBLOOMSPIKE=0\n",
            "V_GLOBW_UNIFORMWEIGHT=FALSE\n",
            "V_AP_DETECTTHRESH=5.0\n",
            "V_AP_DETECTMINAREA=5\n",
            "V_DEBLENDMINCONT=0.0005\n",
            "V_AP_LOWNUM=1\n",
            "V_SEXCATMINFWHM=1.5\n",
            "V_SEXCATFLAG=0\n",
            "V_SEXBACKLEVEL=\n",
            "V_AP_FILTER=N\n",
            "V_SCAMP_MAXPOSANGLE=2.0\n",
            "V_SCAMP_MAXOFFSET=2.0\n",
            "V_SCAMP_MAXSCALE=1.05\n",
            "V_SCAMP_SNLOW=5\n",
            "V_SCAMP_SNHIGH=20\n",
            "V_SCAMP_POLYORDER=3\n",
            "V_SCAMP_POLYORDER2=\n",
            "V_SCAMP_DISTORTGROUPS=\n",
            "V_SCAMP_DISTORTKEYS=\n",
            "V_SCAMP_FGROUPRADIUS=1.0\n",
            "V_SCAMP_CROSSIDRADIUS=2.0\n",
            "V_SCAMP_ASTREFWEIGHT=1.0\n",
            "V_SCAMP_ASTRINSTRUKEY=FILTER\n",
            "V_SCAMP_PHOTINSTRUKEY=FILTER\n",
            "V_SCAMP_STABILITY=INSTRUMENT\n",
            "V_SCAMP_MOSAICTYPE=UNCHANGED\n",
            "V_SCAMP_FOCALPLANE=DEFAULT\n",
            "V_SCAMP_MATCHFLIPPED=N\n",
            "V_SCAMP_MATCHWCS=Y\n",
            "V_ANET_MAXSCALE=1.05\n",
            "V_ANET_POLYORDER=\n",
            "V_ANET_SCAMPDISTORT=N\n",
            "V_ABSPHOT_STDCAT_DIRECT=SDSS\n",
            "V_ABSPHOT_STDCAT_INDIRECT=LANDOLT_UBVRI\n",
            "V_ABSPHOT_APERTURE=10\n",
            "V_ABSPHOT_FILTER=B\n",
            "V_ABSPHOT_STDFILTER=U\n",
            "V_ABSPHOT_STDCOLOR=UmB\n",
            "V_ABSPHOT_COLORFIXED=0.0\n",
            "V_ABSPHOT_EXTINCTION=-0.1\n",
            "V_ABSPHOT_ZPMIN=(null)\n",
            "V_ABSPHOT_ZPMAX=(null)\n",
            "V_ABSPHOT_KAPPA=2.0\n",
            "V_ABSPHOT_THRESHOLD=0.15\n",
            "V_ABSPHOT_MAXITER=10\n",
            "V_ABSPHOT_CONVERGENCE=0.01\n",
            "V_ABSPHOT_STDMINMAG=0.0\n",
            "V_ABSPHOT_MAXPHOTERR=0.05\n",
            "V_ABSPHOT_STDFILTERM2=u\n",
            "V_ABSPHOT_CALMODE=RUNCALIB\n",
            "V_ABSPHOT_WCSERR=10\n",
            "V_ABSPHOT_FITTINGMETHODM2=CHIP\n",
            "V_ABSPHOT_WCSERRCHECKBOX=N\n",
            "V_ABSPHOT_NIGHTSELECTION=\n",
            "V_COADD_REFRA=\n",
            "V_COADD_REFDEC=\n",
            "V_COADD_IDENT=default\n",
            "V_COADD_SEEING=\n",
            "V_COADD_RZP=\n",
            "V_COADD_PIXSCALE=\n",
            "V_COADD_SIZEX=\n",
            "V_COADD_SIZEY=\n",
            "V_COADD_SKYPOSANGLE=\n",
            "V_COADD_PROPMOTIONRA=\n",
            "V_COADD_PROPMOTIONDEC=\n",
            "V_COADD_CHIPS=\"\"\n",
            "V_COADD_FILTERTHRESHOLD=\n",
            "V_COADD_FILTERCLUSTERSIZE=\n",
            "V_COADD_FILTERBORDERWIDTH=\n",
            "V_COADD_SMOOTHEDGE=\n",
            "V_COADD_KERNEL=LANCZOS3\n",
            "V_COADD_FILTER=\n",
            "V_COADD_PROJECTION=TAN\n",
            "V_COADD_CELESTIALTYPE=EQUATORIAL\n",
            "V_COADD_COMBINETYPE=WEIGHTED\n",
            "V_COADD_CLIPAMPFRAC=0.3\n",
            "V_COADD_CLIPSIGMA=4\n",
            "V_COADD_RESCALEWEIGHTS=N"],
        "param_set3.ini": [
            "V_SKYSUBDETECTTHRESH=1.5\n",
            "V_SKYSUBDETECTMINAREA=5\n",
            "V_SKYSUBBACKSIZE=256\n",
            "V_SKYSUBMASKEXPAND=\n",
            "V_SAVESKYMODEL=N\n",
            "V_CSKY_RA1=\n",
            "V_CSKY_RA2=\n",
            "V_CSKY_DEC1=\n",
            "V_CSKY_DEC2=\n",
            "V_CSKY_XMIN=\n",
            "V_CSKY_XMAX=\n",
            "V_CSKY_YMIN=\n",
            "V_CSKY_YMAX=\n",
            "V_CSKYMANUAL=\n",
            "V_CSKYMETHOD=0"]
    }
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
        if len(preparse) > 0:
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
        # copy back default configuration file and write it to disk
        self.param_sets = copy(self.param_sets_default)
        for n in (1, 2, 3):
            fname = "param_set%d.ini" % n
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
