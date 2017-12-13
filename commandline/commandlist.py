"""
Defines a data base of command line parameters for argparse.ArgumentParser
"""

# jobs/tasks for joblist parameter, similar tasks start with the same capital
# letter, attribtes:
# name: GUI check box label
# func: class method of Reduction associated with task
# para: list of parameters for class method, matches a command line parameter
#       (in parse_parameters internal argparse name:
#        without leading -- and - replaced by _)
# help: help to print on screen
parse_actions = {
    "Fr": {
        "name": "Sort data using FITS key",
        "func": "sort_data_using_FITS_key",
        "para": [],
        "help": "Sorts data based on the identifier "
                "given in this FITS keyword"},
    "Fs": {
        "name": "Split FITS / correct header",
        "func": "split_FITS_correct_header",
        "para": ['redo'],
        "help": "Splits multi-extension FITS files, and "
                "writes the THELI standard FITS header"},
    "Lc": {
        "name": "Create links",
        "func": "create_links",
        "para": ['links_chips', 'links_scratch_dir'],
        "help": "Distributes the data over several hard disks"},
    "Cb": {
        "name": "Process biases",
        "func": "process_biases",
        "para": ['cal_bias_mode_min', 'cal_bias_mode_max', 'redo'],
        "help": "Creates a master bias from a series of bias exposures"},
    "Cd": {
        "name": "Process draks",
        "func": "process_darks",
        "para": ['cal_dark_mode_min', 'cal_dark_mode_max', 'redo'],
        "help": "Creates a master dark from a series of dark exposures"},
    "Cf": {
        "name": "Process flats",
        "func": "process_flats",
        "para": ['cal_flat_mode_min', 'cal_flat_mode_max', 'redo'],
        "help": "Creates a master flat from a series of flat field exposures"},
    "Cs": {
        "name": "Calibrate data",
        "func": "calibrate_data",
        "para": ['use_dark', 'cal_data_mode_min', 'cal_data_mode_max', 'redo'],
        "help": "Applies the master bias and master flat to the data"},
    "Gs": {
        "name": "Spread sequence (NIR)",
        "func": "spread_sequence",
        "para": ['nir_ngroups', 'nir_grouplen'],
        "help": "Spreads a sequence of IR exposures in a certain way"},
    "Bm": {
        "name": "Background model correction",
        "func": "background_model_correction",
        "para": ['redo'],
        "help": "Applies a background correction (subtraction, "
                "superflat, fringe model, NIR sky)"},
    "Gm": {
        "name": "Merge sequence (NIR)",
        "func": "merge_sequence",
        "para": [],
        "help": "Merges  a sequence of previously spread IR exposures"},
    "Bn": {
        "name": "Chop/Nod sky subtraction",
        "func": "chop_nod_skysub",
        "para": ['chop_pattern', 'chop_pattern_invert', 'redo'],
        "help": "Does a chop-nod sky subtraction for mid-IR data"},
    "Bc": {
        "name": "Collapse correction",
        "func": "collapse_correction",
        "para": ['redo'],
        "help": "Does a collapse correction to remove "
                "horizontal or vertical gradients"},
    "Di": {
        "name": "Debloom images",
        "func": "debloom_images",
        "para": ['redo'],
        "help": "Removes blooming spikes in the images (for "
                "the preparation of colour pictures)"},
    "Vb": {
        "name": "Create binned preview",
        "func": "create_binned_preview",
        "para": ['redo'],
        "help": "Creates a binned overview image for each exposure "
                "of a multi-chip camera, and a TIFF image."},
    "Wg": {
        "name": "Create global weights",
        "func": "create_global_weights",
        "para": ['redo'],
        "help": "Creates the basic weight map for "
                "the individual weight images"},
    "Wc": {
        "name": "Create weights",
        "func": "create_weights",
        "para": ['redo'],
        "help": "Creates the individual weight maps for each image"},
    "Ds": {
        "name": "Distribute target sets",
        "func": "distribute_target_sets",
        "para": ['image_min_overlap', 'redo'],
        "help": "Identifies image associations on the sky. The SCIENCE "
                "directory field in the Initialise section will then "
                "point to the first association found, SCIENCE_set_1."},
    "Ar": {
        "name": "Get reference catalogue",
        "func": "get_reference_catalog",
        "para": ['ref_cat', 'ref_cat_server', 'ref_image',
                 'ref_image_detect_thresh', 'ref_image_detect_min_area',
                 'redo'],
        "help": "Downloads a reference catalogue from "
                "web or creates it from an image"},
    "Pi": {
        "name": "Absolute photometry (indirect)",
        "func": "absolute_photometry_indirect",
        "para": ['redo'],
        "help": "Attempts to derive absolute photometric "
                "zeropoints for each exposure."},
    "Pd": {
        "name": "Absolute photometry (direct)",
        "func": "absolute_photometry_direct",
        "para": ['redo'],
        "help": "Attempts to derive absolute photometric "
                "zeropoints for each exposure."},
    "As": {
        "name": "Create source catalogue",
        "func": "create_source_cat",
        "para": ['redo'],
        "help": "Creates a source catalogue for each image "
                "for later astrometry and photometry"},
    "Ac": {
        "name": "Astro+photomtery",
        "func": "astro_and_photometry",
        "para": ['astrometry_method', 'ignore_scamp_segfault', 'redo'],
        "help": "Calculates astrometric and photometric solutions"},
    "Hu": {
        "name": "Update header",
        "func": "astrometry_update_header",
        "para": [],
        "help": "Writes the zero-order astrometric solution (CRVAL, "
                "CRPIX, CD-matrix) into the FITS headers"},
    "Hr": {
        "name": "Restore header",
        "func": "astrometry_restore_header",
        "para": [],
        "help": "Restores the original (raw data) zero-order astrometric "
                "information in the header (undo \"update header\")"},
    "Sh": {
        "name": "Sky subtraction helper",
        "func": "sky_subtraction_helper",
        "para": [],
        "help": "Prepares a constant sky model subtraction"},
    "Ss": {
        "name": "Sky subtraction",
        "func": "sky_subtraction",
        "para": ['sky_model_const', 'redo'],
        "help": "Subtracts the sky from the images"},
    "Ca": {
        "name": "Coaddition",
        "func": "coaddition",
        "para": ['cd_posangle_from_image', 'redo'],
        "help": "Coadds the data"},
    "Lr": {
        "name": "Resolve links",
        "func": "resolve_links",
        "para": [],
        "help": "Recollects the data spread over several "
                "hard disks in the beginning (Lc)"}
}
# order in which the jobs will be listed in help
parse_actions_ordered = [
    "Fr", "Fs", "Lc", "Cb", "Cd", "Cf", "Cs", "Gs", "Bm",
    "Gm", "Bn", "Bc", "Di", "Vb", "Wg", "Wc", "Ds", "Ar",
    "Pi", "Pd", "As", "Ac", "Hu", "Hr", "Sh", "Ss", "Ca", "Lr"]


# not yet implemented parameters
"""
# sky helper
'V_CSKY_RA1'
'V_CSKY_RA2'
'V_CSKY_DEC1'
'V_CSKY_DEC2'
'V_CSKY_XMIN'
'V_CSKY_XMAX'
'V_CSKY_YMIN'
'V_CSKY_YMAX'
'V_CSKYMANUAL'
'V_CSKYMETHOD'
# unmatched, probably not in use any more
'V_GLOBWDARKDIR'  # weighting: use bias instead of dark?
'V_ABSPHOT_NIGHTSELECTION'
"""
# commandline argument data base for argument parser and help,
# grouped by topic/task, possible attributes:
# task: list of jobs affected by this parameter
# sort: numeric key to sort arguments within group
# name: target variable name in THELI parameter files
# type: argument type
# meta: meta variable type (e.g. FILE)
# choi: tuple of possible input choices
# maps: tuple of values to which choices are mapped
# defa: default value
# help: help to print on screen
parse_parameters = {
    "Astro/Photometry": {
        "--astrometry-method": {
            "task": ["Pi", "Pd", "Ac"],
            "sort": 100,
            "type": str,
            "choi": ("scamp", "astrometry.net", "shift-float",
                     "shift-int", "xcoor", "header"),
            "defa": "scamp",
            "help": "Method for astrometric calibration. \"Shift\" methods "
                    "do not care about sky angle and absolute coordinates"},
        "--ref-cat": {
            "task": ["Ar"],
            "sort": 200,
            "type": str,
            "choi": ("SDSS-DR9", "ISGL", "PPMXL", "USNO-B1", "2MASS",
                     "URATI", "SPM4", "UCAC4", "GSC-2.3", "TYC", "Image"),
            "defa": "SDSS-DR9",
            "help": "Reference catalogue to be used for astro- and "
                    "photometry"},
        "--ref-cat-ra": {
            "task": ["Ar"],
            "sort": 201,
            "name": "V_AP_REFRA",
            "type": str,
            "defa": "header",
            "help": "Right ascension (deg or hh:mm:ss) of target, if "
                    "not already present (or wrong) in the FITS header"},
        "--ref-cat-dec": {
            "task": ["Ar"],
            "sort": 202,
            "name": "V_AP_REFDEC",
            "type": str,
            "defa": "header",
            "help": "Declination (deg or hh:mm:ss) of target, if not already "
                    "present (or wrong) in the FITS header"},
        "--ref-cat-target": {
            "task": ["Ar"],
            "sort": 203,
            "type": str,
            "defa": "",
            "help": "Target name to retrieve coordinates from"},
        "--ref-cat-maglim": {
            "task": ["Ar"],
            "sort": 204,
            "name": "V_AP_MAGLIM",
            "type": float,
            "defa": 20.0,
            "help": "Faint magnitude limit for the reference catalogue"},
        "--ref-cat-query-radius": {
            "task": ["Ar"],
            "sort": 205,
            "name": "V_AP_RADIUS",
            "type": float,
            "defa": "",
            "help": "Radius [arcmin] around pointing to retrieve reference "
                    "sources, determined automatically if if empty (\"\")"},
        "--ref-cat-server": {
            "task": ["Ar"],
            "sort": 206,
            "type": str,
            "choi": ("vizier.u-strasbg.fr", "vizier.cfa.harvard.edu",
                     "vizier.hia.nrc.ca", "vizier.nao.ac.jp",
                     "vizier.iucaa.ernet.in", "vizier.ast.cam.ac.uk",
                     "data.bao.ac.cn", "www.ukirt.jach.hawaii.edu",
                     "vizier.inasan.ru"),
            "defa": "vizier.u-strasbg.fr",
            "help": "Online server which hosts the reference catalogue"},
        "--ref-image": {
            "task": ["Ar"],
            "sort": 300,
            "meta": "FILE",
            "type": str,
            "help": "Create reference catalogue from an image with known "
                    "astrometric solution"},
        "--ref-image-detect-thresh": {
            "task": ["Ar"],
            "sort": 301,
            "type": float,
            "defa": -1,
            "help": "Minimum detection threshold for object detection"},
        "--ref-image-detect-min-area": {
            "task": ["Ar"],
            "sort": 302,
            "type": float,
            "defa": -1,
            "help": "Minimum number of connected pixels above the detection "
                    "threshold"}
    },

    "Astrometry (Astrometry.net)": {
        "--anet-pixscale-maxerr": {
            "task": ["Pi", "Pd", "Ac"],
            "sort": 100,
            "name": "V_ANET_MAXSCALE",
            "type": float,
            "defa": 1.05,
            "help": "Maximum relative error in the pixel scale"},
        "--anet-distort-degrees": {
            "task": ["Pi", "Pd", "Ac"],
            "sort": 200,
            "name": "V_ANET_POLYORDER",
            "type": int,
            "defa": 3,
            "help": "Degree of the astrometry.net SIP distortion polynomials, "
                    "if empty (\"\"), no distortion is fitted (ignored in "
                    "coaddition, see --anet-distortion)"},
        "--anet-distortion": {
            "task": ["Pi", "Pd", "Ac"],
            "sort": 201,
            "name": "V_ANET_SCAMPDISTORT",
            "type": str,
            "choi": ("Y", "N"),
            "maps": ("Y", "N"),
            "defa": "N",
            "help": "Correct distortion using Scamp for compatibility with "
                    "swarp (coaddition), relies on --scp-distort-degrees, "
                    "--scp-astrom-group-key and --scp-stability-type"}
    },

    "Astrometry (Scamp)": {
        "--scp-posangle-maxerr": {
            "task": ["Pi", "Pd", "Ac"],
            "sort": 100,
            "name": "V_SCAMP_MAXPOSANGLE",
            "type": float,
            "defa": 2.0,
            "help": "Maximum uncertainty [degrees] in the position angle"},
        "--scp-refpix-maxerr": {
            "task": ["Pi", "Pd", "Ac"],
            "sort": 101,
            "name": "V_SCAMP_MAXOFFSET",
            "type": float,
            "defa": 2.0,
            "help": "Maximum uncertainty [arcmin] in the CRPIX1/2 value of "
                    "the FITS header"},
        "--scp-pixscale-maxerr": {
            "task": ["Pi", "Pd", "Ac"],
            "sort": 102,
            "name": "V_SCAMP_MAXSCALE",
            "type": float,
            "defa": 1.05,
            "help": "Maximum error allowed in the pixel scale, max: 2.0"},
        "--scp-include-radius": {
            "task": ["Pi", "Pd", "Ac"],
            "sort": 103,
            "name": "V_SCAMP_FGROUPRADIUS",
            "type": float,
            "defa": 1.0,
            "help": "Maximum distance between pointings to be included in one "
                    "coaddition, max: 180"},
        "--scp-refcat-weight": {
            "task": ["Pi", "Pd", "Ac"],
            "sort": 104,
            "name": "V_SCAMP_ASTREFWEIGHT",
            "type": float,
            "defa": 1.0,
            "help": "Relative weight for reference sources"},
        "--scp-match-tolerance": {
            "task": ["Pi", "Pd", "Ac"],
            "sort": 200,
            "name": "V_SCAMP_CROSSIDRADIUS",
            "type": float,
            "defa": "",
            "help": "Tolerance [arcsec] for matching detected and reference "
                    "sources, should be about 5-10 times or less for "
                    "instruments with small distortions"},
        "--scp-match-flipped": {
            "task": ["Pi", "Pd", "Ac"],
            "sort": 201,
            "name": "V_SCAMP_MATCHFLIPPED",
            "type": str,
            "choi": ("Y", "N"),
            "maps": ("Y", "N"),
            "defa": "N",
            "help": "Match images that are flipped"},
        "--scp-match-wcs": {
            "task": ["Pi", "Pd", "Ac"],
            "sort": 202,
            "name": "V_SCAMP_MATCHWCS",
            "type": str,
            "choi": ("Y", "N"),
            "maps": ("Y", "N"),
            "defa": "Y",
            "help": "Controlls if sky coordinates from reference, can be "
                    "switched off, if header coordinates are within "
                    "--scp-match-tolerance of reference data."},
        "--scp-distort-degrees": {
            "task": ["Pi", "Pd", "Ac"],
            "sort": 300,
            "name": "V_SCAMP_POLYORDER",
            "type": int,
            "defa": 3,
            "help": "Degree of distortion polynomial (pixel scale), 1: no "
                    "distortion, 2: linear variation, 3: quadratic variation, "
                    "..., must be within [1...9]"},
        "--scp-distort-polynomial": {
            "task": ["Pi", "Pd", "Ac"],
            "sort": 301,
            "name": "V_SCAMP_POLYORDER2",
            "type": str,
            "defa": "",
            "help": "Comma-separated list of additional distortion degrees, "
                    "for instable cases"},
        "--scp-distort-groups": {
            "task": ["Pi", "Pd", "Ac"],
            "sort": 302,
            "name": "V_SCAMP_DISTORTGROUPS",
            "type": str,
            "defa": "",
            "help": "Comma-separated list of additional distortion degrees, "
                    "for instable cases"},
        "--scp-distort-fitskeys": {
            "task": ["Pi", "Pd", "Ac"],
            "sort": 303,
            "name": "V_SCAMP_DISTORTKEYS",
            "type": str,
            "defa": "",
            "help": "Comma-separated list of additional distortion FITS keys "
                    "(must be preceeded with \":\"), for instable cases"},
        "--scp-sn-min": {
            "task": ["Pi", "Pd", "Ac"],
            "sort": 400,
            "name": "V_SCAMP_SNLOW",
            "type": float,
            "defa": 20.0,
            "help": "The minimum S/N for a source to be kept in SCAMP"},
        "--scp-sn-max": {
            "task": ["Pi", "Pd", "Ac"],
            "sort": 401,
            "name": "V_SCAMP_SNHIGH",
            "type": float,
            "defa": 5.0,
            "help": "The minimum S/N for a source to be kept for the high-S/N "
                    "statistics"},
        "--scp-astrom-group-key": {
            "task": ["Pi", "Pd", "Ac"],
            "sort": 500,
            "name": "V_SCAMP_ASTRINSTRUKEY",
            "type": str,
            "defa": "FILTER",
            "help": "FITS key used to group exposures in the astrometric "
                    "solution, default: FILTER"},
        "--scp-photom-group-key": {
            "task": ["Pi", "Pd", "Ac"],
            "sort": 501,
            "name": "V_SCAMP_PHOTINSTRUKEY",
            "type": str,
            "defa": "FILTER",
            "help": "FITS key used to group exposures in the photometric "
                    "solution, default: FILTER"},
        "--scp-focal-plane": {
            "task": ["Pi", "Pd", "Ac"],
            "sort": 600,
            "name": "V_SCAMP_FOCALPLANE",
            "type": str,
            "choi": ("DEFAULT", "NEW", "NONE"),
            "defa": "DEFAULT",
            "help": "compute a focal plane configuration, use the default "
                    "or disable it (set --scp-mosaic-type to \"SAME_CRVAL\" "
                    "for multichip cameras, if none is used, set "
                    "--scp-mosaic-type to \"UNCHANGED\"."},
        "--scp-mosaic-type": {
            "task": ["Pi", "Pd", "Ac"],
            "sort": 601,
            "name": "V_SCAMP_MOSAICTYPE",
            "type": str,
            "choi": ("UNCHANGED", "SAME_CRVAL", "SHARE_PROJAXIS",
                     "FIX_FOCALPLANE", "LOOSE"),
            "defa": "UNCHANGED",
            "help": "Controls the positioning of chips in mosaic cameras (use"
                    "UNCHANGED for single-chip cameras), more information in "
                    "the Scamp manual"},
        "--scp-stability-type": {
            "task": ["Pi", "Pd", "Ac"],
            "sort": 602,
            "name": "V_SCAMP_STABILITY",
            "type": str,
            "choi": ("INSTRUMENT", "EXPOSURE"),
            "defa": "INSTRUMENT",
            "help": "???"}
    },

    # ########################### #
    # #  STOPPED REVISION HERE  # #
    # ########################### #

    "Background modeling": {
        "--bg-convolve": {
            "task": ["Bm"],
            "sort": 100,
            "name": "V_BACK_SEXFILTER",
            "type": str,
            "choi": ("Y", "N"),
            "maps": ("Y", "N"),
            "defa": "Y",
            "help": "Convolves the image with a general purpose filter "
                    "(note: this increases the footprint of hot pixels)"},
        "--bg-detect-thresh": {
            "task": ["Bm"],
            "sort": 101,
            "name": "V_BACK_DETECTTHRESH",
            "type": float,
            "defa": 1.3,
            "help": "Minimum detection threshold for object detection, if "
                    "empty (\"\"), no masking will take place before "
                    "combining images"},
        "--bg-detect-min-area": {
            "task": ["Bm"],
            "sort": 102,
            "name": "V_BACK_DETECTMINAREA",
            "type": int,
            "defa": 5,
            "help": "Minimum number of connected pixels above the detection "
                    "threshold, if empty (\"\"), no masking will take place "
                    "before combining images"},
        "--bg-detect-mask-expand": {
            "task": ["Bm"],
            "sort": 103,
            "name": "V_BACK_MASKEXPAND",
            "type": float,
            "defa": "",
            "help": "If not empty, pixels within the scaled best-fit "
                    "SExtractor ellipse will be set to zero. In this way very "
                    "faint flux invisible in an individual image can be "
                    "caught as well. Good starting value: 3.0"},
        "--bg-combine-method": {
            "task": ["Bm"],
            "sort": 104,
            "name": "V_BACK_COMBINEMETHOD",
            "type": str,
            "choi": ("Median", "Average"),
            "maps": (0, 1),
            "defa": "Median",
            "help": "How to combine the images of a stack"},
        "--bg-apply-2pass": {
            "task": ["Bm"],
            "sort": 200,
            "name": "V_BACK_TWOPASS",
            "type": str,
            "choi": ("Y", "N"),
            "maps": ("Y", "N"),
            "defa": "Y",
            "help": "Whether a two-pass background correction is desired. If "
                    "yes, then the first pass will be without SExtractor "
                    "object masking."},
        "--bg-reject-low-1pass": {
            "task": ["Bm"],
            "sort": 201,
            "name": "V_BACK_NLOW1",
            "type": int,
            "defa": 0,
            "help": "Number of low pixels to be rejected from the stack "
                    "during the first pass of the background modeling"},
        "--bg-reject-high-1pass": {
            "task": ["Bm"],
            "sort": 202,
            "name": "V_BACK_NHIGH1",
            "type": int,
            "defa": 0,
            "help": "Number of high pixels to be rejected from the stack "
                    "during the first pass of the background modeling"},
        "--bg-reject-low-2pass": {
            "task": ["Bm"],
            "sort": 203,
            "name": "V_BACK_NLOW2",
            "type": int,
            "defa": 0,
            "help": "Number of low pixels to be rejected from the stack "
                    "during the second pass of the background modeling"},
        "--bg-reject-high-2pass": {
            "task": ["Bm"],
            "sort": 204,
            "name": "V_BACK_NHIGH2",
            "type": int,
            "defa": 1,
            "help": "Number of high pixels to be rejected from the stack "
                    "during the second pass of the background modeling"},
        "--bg-reject-bstar-mag": {
            "task": ["Bm"],
            "sort": 300,
            "name": "V_BACK_MAGLIMIT",
            "type": float,
            "defa": "",
            "help": "Chips that have stars brighter than this magnitude in or "
                    "near them will be rejected from the background "
                    "modeling."},
        "--bg-reject-bstar-dist": {
            "task": ["Bm"],
            "sort": 301,
            "name": "V_BACK_DISTANCE",
            "type": float,
            "defa": "",
            "help": "Minimum distance of a bright star from a chip edge to be "
                    "considered \"safe\", in arcminutes"},
        "--bg-reject-bstar-refserver": {
            "task": ["Bm"],
            "sort": 302,
            "name": "V_BACK_SERVER",
            "type": str,
            "choi": ("vizier.u-strasbg.fr", "vizier.cfa.harvard.edu",
                     "vizier.hia.nrc.ca", "vizier.nao.ac.jp",
                     "vizier.iucaa.ernet.in", "vizier.ast.cam.ac.uk",
                     "data.bao.ac.cn", "www.ukirt.jach.hawaii.edu",
                     "vizier.inasan.ru"),
            "defa": "vizier.u-strasbg.fr",
            "help": "The server from which to download the bright star "
                    "catalog"},
        "--bg-method": {
            "task": ["Bm"],
            "sort": 400,
            "name": "V_BACK_APPLYMODE",
            "type": str,
            "choi": ("subtract", "divide", "defringe", "devide+defringe"),
            "maps": (0, 1, 2, 3),
            "defa": "subtract",
            "help": "Method to apply the background model"},
        "--bg-smooth-scale": {
            "task": ["Bm"],
            "sort": 401,
            "name": "V_BACK_ILLUMSMOOTH",
            "type": float,
            "defa": "",
            "help": "Size of the smoothing kernel. Leave this field EMPTY if "
                    "the background model should NOT be smoothed."},
        "--bg-smooth-scale-fringe": {
            "task": ["Bm"],
            "sort": 402,
            "name": "V_BACK_FRINGESMOOTH",
            "type": float,
            "defa": "",
            "help": "Half width of the smoothing kernel for the FRINGE model. "
                    "If empty, then no smoothing is performed. Values of 1-2 "
                    "are usually sufficient."},
        "--bg-model-rescale": {
            "task": ["Bm"],
            "sort": 403,
            "name": "V_BACK_FRINGESCALE",
            "type": str,
            "choi": ("Y", "N"),
            "maps": ("Y", "N"),
            "defa": "Y",
            "help": "Uncheck this box if you do not want the model to be "
                    "scaled to the sky background of individual exposures; "
                    "for example, if you have large and bright galaxies in "
                    "the images, then rescaling would lead to an "
                    "overestimation of the background."},
        "--bg-adjust-gain": {
            "task": ["Bm"],
            "sort": 404,
            "name": "V_BACK_ADJUSTGAINS",
            "type": str,
            "choi": ("Y", "N"),
            "maps": ("Y", "N"),
            "defa": "N",
            "help": "Check this if the gain correction from the flat field "
                    "alone did not work sufficiently well."},
        "--bg-window-number": {
            "task": ["Bm"],
            "sort": 500,
            "name": "V_BACK_WINDOWSIZE",
            "type": int,
            "defa": 0,
            "help": "The number of images closest in time to an exposure, "
                    "used to calculate a background model for this exposure. "
                    "If set to zero or left empty, a static model will be "
                    "used."},
        "--bg-window-timespan": {
            "task": ["Bm"],
            "sort": 501,
            "name": "V_BACK_GAPSIZE",
            "type": float,
            "defa": "",
            "help": "The maximum amount of time, in hours, by which an "
                    "exposure sequence may be interrupted without enforcing a "
                    "new set of background models."}
    },

    "Calibration": {
        "--cal-nonlin-correction": {
            "task": ["Cb", "Cd", "Cf", "Cs"],
            "sort": 100,
            "name": "V_NONLINCORR",
            "type": str,
            "choi": ("Y", "N"),
            "maps": ("Y", "N"),
            "defa": "N",
            "help": "Mark this CheckBox if you want to correct for non-"
                    "linearity in your data. This requires that the non-"
                    "linearity coefficients have been measured and provided "
                    "in a separate configuration file. "},
        "--cal-overscan-reject-low": {
            "task": ["Cb", "Cd", "Cf", "Cs"],
            "sort": 200,
            "name": "V_CAL_OVSCANNLOW",
            "type": int,
            "defa": 0,
            "help": "Number of low pixels to be rejected from the stack"},
        "--cal-overscan-reject-high": {
            "task": ["Cb", "Cd", "Cf", "Cs"],
            "sort": 201,
            "name": "V_CAL_OVSCANNHIGH",
            "type": int,
            "defa": 1,
            "help": "Number of high pixels to be rejected from the stack"},
        "--no-bias": {
            "task": ["Cd", "Cf", "Cs"],
            "sort": 300,
            "name": "V_DO_BIAS",
            "type": str,
            "choi": ("Y", "N"),
            "maps": ("Y", "N"),
            "defa": "Y",
            "help": "Mark this CheckBox if you do not want a BIAS / DARK "
                    "subtracted from your FLAT / SCIENCE, or if you don't "
                    "have a BIAS / DARK."},
        "--cal-bias-mode-min": {
            "task": ["Cb"],
            "sort": 301,
            "type": float,
            "help": "Bias exposures with a mode lower than this value are "
                    "rejected from the calculation of the master BIAS."},
        "--cal-bias-mode-max": {
            "task": ["Cb"],
            "sort": 302,
            "type": float,
            "help": "Bias exposures with a mode higher than this value are "
                    "rejected from the calculation of the master BIAS."},
        "--cal-bias-reject-low": {
            "task": ["Cb"],
            "sort": 303,
            "name": "V_CAL_BIASNLOW",
            "type": int,
            "defa": 0,
            "help": "Number of low pixels to be rejected from the stack"},
        "--cal-bias-reject-high": {
            "task": ["Cb"],
            "sort": 304,
            "name": "V_CAL_BIASNHIGH",
            "type": int,
            "defa": 1,
            "help": "Number of high pixels to be rejected from the stack"},
        "--use-dark": {
            "task": ["Cf", "Cs"],
            "sort": 400,
            "type": str,
            "choi": ("Y", "N"),
            "maps": (True, False),
            "defa": "N",
            "help": "Use a DARK instead of the BIAS"},
        "--cal-dark-mode-min": {
            "task": ["Cd"],
            "sort": 401,
            "type": float,
            "help": "Dark exposures with a mode lower than this value are "
                    "rejected from the calculation of the master DARK."},
        "--cal-dark-mode-max": {
            "task": ["Cd"],
            "sort": 402,
            "type": float,
            "help": "Dark exposures with a mode higher than this value are "
                    "rejected from the calculation of the master DARK."},
        "--cal-dark-reject-low": {
            "task": ["Cd"],
            "sort": 403,
            "name": "V_CAL_DARKNLOW",
            "type": int,
            "defa": 0,
            "help": "Number of low pixels to be rejected from the stack"},
        "--cal-dark-reject-high": {
            "task": ["Cd"],
            "sort": 404,
            "name": "V_CAL_DARKNHIGH",
            "type": int,
            "defa": 1,
            "help": "Number of high pixels to be rejected from the stack"},
        "--no-flat": {
            "task": ["Cs"],
            "sort": 500,
            "name": "V_DO_FLAT",
            "type": str,
            "choi": ("Y", "N"),
            "maps": ("Y", "N"),
            "defa": "Y",
            "help": "Mark this CheckBox if you do not want a FLAT applied to "
                    "your SCIENCE data, or if you don't have a FLAT."},
        "--cal-flat-mode-min": {
            "task": ["Cf"],
            "sort": 501,
            "type": float,
            "help": "Dark exposures with a mode lower than this value are "
                    "rejected from the calculation of the master DARK."},
        "--cal-flat-mode-max": {
            "task": ["Cf"],
            "sort": 502,
            "type": float,
            "help": "Dark exposures with a mode higher than this value are "
                    "rejected from the calculation of the master DARK."},
        "--cal-flat-reject-low": {
            "task": ["Cf"],
            "sort": 503,
            "name": "V_CAL_FLATNLOW",
            "type": int,
            "defa": 0,
            "help": "Number of low pixels to be rejected from the stack"},
        "--cal-flat-reject-high": {
            "task": ["Cf"],
            "sort": 504,
            "name": "V_CAL_FLATNHIGH",
            "type": int,
            "defa": 1,
            "help": "Number of high pixels to be rejected from the stack"},
        "--cal-data-mode-max": {
            "task": ["Cs"],
            "sort": 600,
            "type": float,
            "help": "Exposures with a mode lower than this value are "
                    "rejected."},
        "--cal-data-mode-min": {
            "task": ["Cs"],
            "sort": 601,
            "type": float,
            "help": "Exposures with a mode higher than this value are "
                    "rejected."}
    },

    "Chop/Nod subtraction": {
        "--chop-pattern": {
            "task": ["Bn"],
            "sort": 100,
            "type": str,
            "choi": ("0110", "1001", "0101", "1010"),
            "defa": "0110",
            "help": "Select the Chop-Nod pattern (0: sky, 1: ontarget)"},
        "--chop-pattern-invert": {
            "task": ["Bn"],
            "sort": 101,
            "type": str,
            "choi": ("Y", "N"),
            "maps": (True, False),
            "defa": "N",
            "help": "Activate this CheckBox if you want the pattern inverted "
                    "for every second group, i.e. 0110-1001-0110-1001"}
    },

    "Coaddition": {
        "--cd-ref-ra": {
            "task": ["Ca"],
            "sort": 100,
            "name": "V_COADD_REFRA",
            "type": str,
            "defa": "",
            "help": "Projection reference coordinate: right ascension"},
        "--cd-ref-dec": {
            "task": ["Ca"],
            "sort": 101,
            "name": "V_COADD_REFDEC",
            "type": str,
            "defa": "",
            "help": "Projection reference coordinate: declination"},
        "--cd-ref-identifier": {
            "task": ["Ca"],
            "sort": 102,
            "name": "V_COADD_IDENT",
            "type": str,
            "defa": "",  # check where filter appending happens
            "help": "Unique identifier for the coaddition. The filter chosen "
                    "is appended automatically to this string. Max string "
                    "length: 37 chars"},
        "--cd-coadd-chips": {
            "task": ["Ca"],
            "sort": 103,
            "name": "V_COADD_CHIPS",
            "type": int,
            "defa": "",  # should be '""', but this causes problems in parser
            "help": "Blank-separated list of the chips that shall be coadded"},
        "--cd-filter": {
            "task": ["Ca"],
            "sort": 140,
            "name": "V_COADD_FILTER",
            "type": str,
            "help": "If images taken with different filters are in the "
                    "SCIENCE directory, which ones do you want to coadd?"},
        "--cd-prop-motion-ra": {
            "task": ["Ca"],
            "sort": 200,
            "name": "V_COADD_PROPMOTIONRA",
            "type": float,
            "defa": "",  # there is an extra box for the unit, def --arcsec/s?
            "help": "The proper motion right ascension of a moving target. "
                    "The coadded images get shifted accordingly."},
        "--cd-prop-motion-dec": {
            "task": ["Ca"],
            "sort": 201,
            "name": "V_COADD_PROPMOTIONDEC",
            "type": float,
            "defa": "",  # there is an extra box for the unit, def --arcsec/s?
            "help": "The proper motion declination of a moving target. The "
                    "coadded images get shifted accordingly."},
        "--cd-xdim": {
            "task": ["Ca"],
            "sort": 300,
            "name": "V_COADD_SIZEX",
            "type": int,
            "defa": "",
            "help": "The x size of the coadded image in pixels. If left "
                    "empty, it will be determined automatically."},
        "--cd-ydim": {
            "task": ["Ca"],
            "sort": 301,
            "name": "V_COADD_SIZEY",
            "type": int,
            "defa": "",
            "help": "The y size of the coadded image in pixels. If left "
                    "empty, it will be determined automatically."},
        "--cd-posangle": {
            "task": ["Ca"],
            "sort": 302,
            "name": "V_COADD_SKYPOSANGLE",
            "type": float,
            "defa": "",
            "help": "The sky position angle of the coadded image. A positive "
                    "angle means a rotation is performed from North over "
                    "East, i.e. the image is rotated clockwise. If zero is "
                    "entered or the field left empty, then North will be up "
                    "and East left. If the data was taken with non-zero "
                    "position angle, then entering the same value will result "
                    "in an 'unrotated' coadded image."},
        "--cd-posangle-from-image": {
            "task": ["Ca"],
            "sort": 303,
            "type": str,
            "choi": ("Y", "N"),
            "maps": (True, False),
            "defa": "N",
            "help": "If the sky position angle should be determined from the "
                    "image headers"},
        "--cd-seeing-max": {
            "task": ["Ca"],
            "sort": 304,
            "name": "V_COADD_SEEING",
            "type": float,
            "defa": "",
            "help": "Images with a seeing larger than this value will not be "
                    "coadded."},
        "--cd-zp-min": {
            "task": ["Ca"],
            "sort": 305,
            "name": "V_COADD_RZP",
            "type": float,
            "defa": "",
            "help": "Images with a relative zeropoint lower than this value "
                    "will not be coadded."},
        "--cd-pixscale": {
            "task": ["Ca"],
            "sort": 306,
            "name": "V_COADD_PIXSCALE",
            "type": float,
            "defa": "",
            "help": "Resampling pixel scale"},
        "--cd-smooth-edges-lenght": {
            "task": ["Ca"],
            "sort": 307,
            "name": "V_COADD_SMOOTHEDGE",
            "type": int,
            "defa": "",
            "help": "The length over which overlapping edges in a mosaic "
                    "should be blended into each other."},
        "--cd-mask-reject-threshold": {
            "task": ["Ca"],
            "sort": 400,
            "name": "V_COADD_FILTERTHRESHOLD",
            "type": float,
            "defa": "",
            "help": "Rejection threshold in units of sigma"},
        "--cd-mask-cluster-size": {
            "task": ["Ca"],
            "sort": 401,
            "name": "V_COADD_FILTERCLUSTERSIZE",
            "type": int,
            "defa": "",
            "help": "Only mask pixel groups consisting of at least this many "
                    "bad pixels (values larger than 9 have no effect and will "
                    "be reset to 9)."},
        "--cd-mask-border-width": {
            "task": ["Ca"],
            "sort": 402,
            "name": "V_COADD_FILTERBORDERWIDTH",
            "type": int,
            "defa": "",
            "help": "If a pixel is bad, then mask a border of this width "
                    "around it, too. If set to 1 (2), a cluster of 3x3 (5x5) "
                    "pixels centred on the bad pixel will be masked, too, and "
                    "so on."},
        "--cd-kernel": {
            "task": ["Ca"],
            "sort": 500,
            "name": "V_COADD_KERNEL",
            "type": str,
            "choi": ("NEAREST", "BILINEAR", "LANCZOS2",
                     "LANCZOS3", "LANCZOS4"),
            "defa": "LANCZOS3",
            "help": "The kernel used for resampling. Best choice: LANCZOS3"},
        "--cd-projection": {
            "task": ["Ca"],
            "sort": 501,
            "name": "V_COADD_PROJECTION",
            "type": str,
            "choi": ("AZP", "TAN", "STG", "SIN", "ARC", "ZPN", "ZEA",
                     "AIR", "CYP", "CEA", "CAR", "MER", "COP", "COE",
                     "COD", "COO", "BON", "PCO", "GLS", "PAR", "MOL",
                     "AIT", "TSC", "CSC", "QSC", "NONE"),
            "defa": "TAN",
            "help": "Type of projection, best choice: TAN or COE if field of "
                    "view less than 10 deg. For all-sky images AIT is a "
                    "frequently used method."},
        "--cd-coord-system": {
            "task": ["Ca"],
            "sort": 502,
            "name": "V_COADD_CELESTIALTYPE",
            "type": str,
            "choi": ("EQUATORIAL", "GALACTIC", "ECLIPTIC", "SUPERGALACTIC"),
            "defa": "EQUATORIAL",
            "help": "Celestial coordinate system. PIXEL means no "
                    "(de)projection is used."},
        "--cd-combine-type": {
            "task": ["Ca"],
            "sort": 503,
            "name": "V_COADD_COMBINETYPE",
            "type": str,
            "choi": ("WEIGHTED", "MEDIAN", "AVERAGE", "MIN", "MAX", "CHI2"),
            "defa": "WEIGHTED",
            "help": "The image combination method"},
        "--cd-rescale-weights": {
            "task": ["Ca"],
            "sort": 504,
            "name": "V_COADD_RESCALEWEIGHTS",
            "type": str,
            "choi": ("Y", "N"),
            "maps": ("Y", "N"),
            "defa": "N",
            "help": "Whether the weight images are to be automatically "
                    "rescaled by SWarp. Switch ON for empty fields only. "
                    "Large bright galaxies or nebula will distort the "
                    "automatic rms measurement."},
        "--cd-clip-flux-frac": {
            "task": ["Ca"],
            "sort": 600,
            "name": "V_COADD_CLIPAMPFRAC",
            "type": float,
            "defa": 0.3,
            "help": "Fraction of flux variation allowed with clipping when "
                    "using --cd-combine-type CLIPPED"},
        "--cd-clip-flux-rms": {
            "task": ["Ca"],
            "sort": 601,
            "name": "V_COADD_CLIPSIGMA",
            "type": float,
            "defa": 4.,
            "help": "RMS error multiple variation allowed with clipping when "
                    "using --cd-combine-type CLIPPED"}
    },

    "Collapse correction": {
        "--coll-detect-thresh": {
            "task": ["Bc"],
            "sort": 100,
            "name": "V_COLLDETECTTHRESH",
            "type": float,
            "defa": "",
            "help": "Detection threshold; if left empty, no detection will "
                    "take place"},
        "--coll-detect-min-area": {
            "task": ["Bc"],
            "sort": 101,
            "name": "V_COLLDETECTMINAREA",
            "type": int,
            "defa": "",
            "help": "Minimum number of connected pixels above the detection "
                    "threshold; if left empty, no detection will take place"},
        "--coll-detect-mask-expand": {
            "task": ["Bc"],
            "sort": 102,
            "name": "V_COLLMASKEXPAND",
            "type": float,
            "defa": "",
            "help": "If not empty, pixels within the scaled best-fit "
                    "SExtractor ellipse will be set to zero. In this way very "
                    "faint flux invisible in an individual image can be "
                    "caught as well. Good starting value: 3.0"},
        "--coll-detect-thresh-auto": {
            "task": ["Bc"],
            "sort": 103,
            "name": "V_COLLAUTOTHRESHOLD",
            "type": str,
            "choi": ("Y", "N"),
            "maps": (1, 0),
            "defa": "N",
            "help": "If activated, the DT parameter is automatically cross-"
                    "checked. If a larger value is found to be better, then "
                    "the user-supplied value is overriden."},
        "--coll-detect-store-masks": {
            "task": ["Bc"],
            "sort": 104,
            "name": "V_COLLMASKACTION",
            "type": str,
            "choi": ("Y", "N"),
            "maps": (1, 0),
            "defa": "Y",
            "help": "Keeps the object masks for visual inspection."},
        "--coll-reject-thresh": {
            "task": ["Bc"],
            "sort": 200,
            "name": "V_COLLREJECTTHRESH",
            "type": float,
            "defa": 1.5,
            "help": "Rejection threshold for the averaging process"},
        "--coll-direction": {
            "task": ["Bc"],
            "sort": 201,
            "name": "V_COLLDIRECTION",
            "type": str,
            "choi": ("x", "y", "xy", "xyyx", "yxxy"),
            "defa": "x",
            "help": "Direction vector for collapse correction. \"xyyx\" and "
                    "\"yxxy\" are patterns acting on the quartiles (from top "
                    "left to bottom right) in direction x or y respectively."},
        "--coll-exclude-xmin": {
            "task": ["Bc"],
            "sort": 300,
            "name": "V_COLLXMIN",
            "type": int,
            "defa": "",
            "help": "Left limit for the excluded region"},
        "--coll-exclude-xmax": {
            "task": ["Bc"],
            "sort": 301,
            "name": "V_COLLXMAX",
            "type": int,
            "defa": "",
            "help": "Right limit for the excluded region"},
        "--coll-exclude-ymin": {
            "task": ["Bc"],
            "sort": 302,
            "name": "V_COLLYMIN",
            "type": int,
            "defa": "",
            "help": "Bottom limit for the excluded region"},
        "--coll-exclude-ymax": {
            "task": ["Bc"],
            "sort": 303,
            "name": "V_COLLYMAX",
            "type": int,
            "defa": "",
            "help": "Top limit for the excluded region"}
    },

    "Cross talk": {
        "--xtalk-normal": {
            "task": ["Fs"],
            "sort": 100,
            "name": "V_PRE_XTALK_NOR_CHECKED",
            "type": str,
            "choi": ("Y", "N"),
            "maps": (1, 0),
            "defa": "N",
            "help": "Perform cross talk correction in two readout stripes or "
                    "quartiles."},
        "--xtalk-normal-amplitude": {
            "task": ["Fs"],
            "sort": 101,
            "name": "V_PRE_XTALK_NOR_AMPLITUDE",
            "type": float,
            "defa": "",
            "help": "Crosstalk amplitude. Negative values mean that images "
                    "leave a negative footprint."},
        "--xtalk-normal-type": {
            "task": ["Fs"],
            "sort": 102,
            "name": "V_PRE_XTALK_NOR_BUTTONID",
            "type": str,
            "choi": ("2x2", "col", "row", ""),
            "maps": (0, 2, 1, -1),  # are these IDs correct?
            "defa": "",
            "help": "Cross talk pattern"},
        "--xtalk-row": {
            "task": ["Fs"],
            "sort": 200,
            "name": "V_PRE_XTALK_ROW_CHECKED",
            "type": str,
            "choi": ("Y", "N"),
            "maps": (1, 0),
            "defa": "N",
            "help": "Perform cross talk correction in a more complicated row "
                    "or column pattern."},
        "--xtalk-row-amplitude": {
            "task": ["Fs"],
            "sort": 201,
            "name": "V_PRE_XTALK_ROW_AMPLITUDE",
            "type": float,
            "defa": "",
            "help": "Crosstalk amplitude. Negative values mean that images "
                    "leave a negative footprint."},
        "--xtalk-row-type": {
            "task": ["Fs"],
            "sort": 202,
            "name": "V_PRE_XTALK_ROW_BUTTONID",
            "type": str,
            "choi": ("2x2-row", "2x2-col", "2col-col", "2row-col",
                     "1row-col", "1col-row", ""),
            "maps": (0, 3, 1, 5, 2, 4, -1),  # are these IDs correct?
            "defa": "",
            "help": "Cross talk pattern"},
        "--xtalk-multi": {
            "task": ["Fs"],
            "sort": 300,
            "name": "V_PRE_XTALK_MULTI_CHECKED",
            "type": str,
            "choi": ("Y", "N"),
            "maps": (1, 0),
            "defa": "N",
            "help": "Perform cross talk correction in multiple rows or "
                    "columns."},
        "--xtalk-multi-sections": {
            "task": ["Fs"],
            "sort": 301,
            "name": "V_PRE_XTALK_MULTI_NSECTION",
            "type": int,
            "defa": "",
            "help": "The number of readout stripes (usually for the larger "
                    "HAWAII2 arrays)"},
        "--xtalk-multi-type": {
            "task": ["Fs"],
            "sort": 302,
            "name": "V_PRE_XTALK_MULTI_BUTTONID",
            "type": str,
            "choi": ("col", "row", ""),
            "maps": (1, 0, -1),  # are these IDs correct?
            "defa": "",
            "help": "Cross talk pattern"}
    },

    "Deblooming": {
        "--debloom-saturation": {
            "task": ["Di"],
            "sort": 0,
            "type": float,
            "defa": 55000,
            "help": "Pixels with values higher than that are assumed to be "
                    "affected by blooming."}
    },

    "Photometry (direct)": {
        "--dphot-ref-cat": {
            "task": ["Pd"],
            "sort": 100,
            "name": "V_ABSPHOT_STDCAT_DIRECT",
            "type": str,
            "choi": ("SDSS", "2MASS"),
            "defa": "SDSS",
            "help": "Reference catalogue to be used for photometry"},
        # choices depend on 'dphot_ref_cat'
        "--dphot-ref-filter": {
            "task": ["Pd"],
            "sort": 200,
            "name": "V_ABSPHOT_STDFILTERM2",
            "type": str,
            "choi": ("u", "g", "r", "i", "z", "J", "H", "Ks"),
            "defa": "r",
            "help": "Select in which filters your observations were made."},
        "--dphot-photom-err-max": {
            "task": ["Pd"],
            "sort": 201,
            "name": "V_ABSPHOT_MAXPHOTERR",
            "type": float,
            "defa": 0.05,
            "help": "The maximum measurement error for sources in your data "
                    "that go into the fit."},
        "--dphot-fitting-mode": {
            "task": ["Pd"],
            "sort": 300,
            "name": "V_ABSPHOT_FITTINGMETHODM2",
            "type": str,
            "choi": ("CHIP", "MOSAIC"),
            "defa": "CHIP",
            "help": "Select if you want each chip to be calibrated "
                    "independently (images get scaled to the same zeropoint), "
                    "or if you want to treat the chips as one photometrically "
                    "stable mosaic."},
    },

    "Photometry (indirect)": {
        "--iphot-ref-cat": {
            "task": ["Pi"],
            "sort": 100,
            "name": "V_ABSPHOT_STDCAT_INDIRECT",
            "type": str,
            "choi": ("LANDOLT_UBVRI", "STETSON_UBVRI", "STRIPE82_ugriz",
                     "STRIPE82_u'g'r'i'z'", "MKO_JHK", "HUNT_JHK",
                     "2MASSfaint_JHK", "PERSSON_JHKKs", "JAC_YJHKLM",
                     "MKO_LM", "WASHINGTON"),
            "defa": "LANDOLT_UBVRI",
            "help": "Reference catalogue to be used for photometry"},
        "--iphot-aperture": {
            "task": ["Pi"],
            "sort": 200,
            "name": "V_ABSPHOT_APERTURE",
            "type": int,
            "defa": 10,
            "help": "Diameter of the photometric aperture in pixels"},
        "--iphot-filter": {
            "task": ["Pi"],
            "sort": 201,
            "name": "V_ABSPHOT_FILTER",
            "type": str,
            "defa": "",
            "help": "The name of the filter in which you observed"},
        # choices depend on 'iphot_ref_cat'
        "--iphot-std-color": {
            "task": ["Pi"],
            "sort": 202,
            "name": "V_ABSPHOT_STDCOLOR",
            "type": str,
            "choi": ("U-B", "B-V", "V-R", "R-I", "V-I", "u-g",
                     "g-r", "r-i", "i-z", "Y-J", "J-H", "H-K",
                     "H-Ks", "K-L", "L-M", "C-M", "M-T1", "T1-T2"),
            "maps": ("UmB", "BmV", "VmR", "RmI", "VmI", "umg",
                     "gmr", "rmi", "imz", "YmJ", "JmH", "HmK",
                     "HmKs", "KmL", "LmM", "CmM", "MmT1", "T1mT2"),
            "defa": "r-i",
            "help": "Color from reference catalogue to use for photometry."},
        # choices depend on 'iphot_ref_cat'
        "--iphot-std-filter": {
            "task": ["Pi"],
            "sort": 203,
            "name": "V_ABSPHOT_STDFILTER",
            "type": str,
            "choi": ("U", "B", "V", "R", "I", "u", "g", "r", "i", "z",
                     "Y", "J", "H", "K", "Ks", "L", "M", "C", "T1", "T2"),
            "defa": "r",
            "help": "Filter of reference catalogue to use for photometry."},
        "--iphot-extinction": {
            "task": ["Pi"],
            "sort": 300,
            "name": "V_ABSPHOT_EXTINCTION",
            "type": float,
            "defa": 0,
            "help": "The extinction coefficient if it should be fixed, must "
                    "be negative"},
        "--iphot-color-term": {
            "task": ["Pi"],
            "sort": 301,
            "name": "V_ABSPHOT_COLORFIXED",
            "type": float,
            "defa": 0.0,
            "help": "The color term if it should be fixed"},
        "--iphot-zp-min": {
            "task": ["Pi"],
            "sort": 302,
            "name": "V_ABSPHOT_ZPMIN",
            "type": float,
            "defa": "",
            "help": "The brightest acceptable limit of the zeropoint"},
        "--iphot-zp-max": {
            "task": ["Pi"],
            "sort": 303,
            "name": "V_ABSPHOT_ZPMAX",
            "type": float,
            "defa": "",
            "help": "The faintest acceptable limit of the zeropoint"},
        "--iphot-kappa": {
            "task": ["Pi"],
            "sort": 304,
            "name": "V_ABSPHOT_KAPPA",
            "type": float,
            "defa": 2.0,
            "help": "The kappa-sigma rejection threshold for sources during "
                    "the iterative fit"},
        "--iphot-thresh": {
            "task": ["Pi"],
            "sort": 305,
            "name": "V_ABSPHOT_THRESHOLD",
            "type": float,
            "defa": 0.15,
            "help": "Sources this many mag below the fit will be rejected "
                    "(likely non-photometric exposures)"},
        "--iphot-mag-min": {
            "task": ["Pi"],
            "sort": 400,
            "name": "V_ABSPHOT_STDMINMAG",
            "type": float,
            "defa": 0.0,
            "help": "Stars brighter than this magnitude will not be taken "
                    "into account during the zeropoint determination."},
        "--iphot-iter-max": {
            "task": ["Pi"],
            "sort": 401,
            "name": "V_ABSPHOT_MAXITER",
            "type": int,
            "defa": 10,
            "help": "The maximum number of iterations"},
        "--iphot-convergence": {
            "task": ["Pi"],
            "sort": 402,
            "name": "V_ABSPHOT_CONVERGENCE",
            "type": float,
            "defa": 0.01,
            "help": "Convergence is achieved if ZP, ExtCoeff and ColCoeff "
                    "change by less than this amount at the same time."},
        "--iphot-calib-mode": {
            "task": ["Pi"],
            "sort": 403,
            "name": "V_ABSPHOT_CALMODE",
            "type": str,
            "choi": ("RUNCALIB", "NIGHTCALIB"),
            "defa": "RUNCALIB",
            "help": "Choose whether a combined photometric solution is "
                    "calculated for ALL nights (RUNCALIB), or whether each "
                    "night is calibrated individually (NIGHTCALIB)"},
        "--iphot-do-astrometry": {
            "task": ["Pi"],
            "sort": 500,
            "name": "V_ABSPHOT_WCSERRCHECKBOX",
            "type": str,
            "choi": ("Y", "N"),
            "maps": ("Y", "N"),
            "defa": "Y",
            "help": "Uncheck this switch if NO astrometric solution should be "
                    "attempted (e.g. because the source density of the "
                    "standard star field is too low). Provide the uncertainty "
                    "of the original WCS in the field below."},
        "--iphot-wcs-err": {
            "task": ["Pi"],
            "sort": 501,
            "name": "V_ABSPHOT_WCSERR",
            "type": float,
            "defa": 10,
            "help": "Provide here the uncertainty of the original WCS if NO "
                    "astrometric solution shall be attempted."}
    },

    "Preview image": {
        "--preview-binning": {
            "task": ["Vb"],
            "sort": 100,
            "name": "V_WEIGHTBINSIZE",
            "type": int,
            "defa": 4,
            "help": "The binning factor for the mosaic"},
        "--preview-lim-low": {
            "task": ["Vb"],
            "sort": 200,
            "name": "V_WEIGHTBINMIN",
            "type": int,
            "defa": -100,
            "help": "The images have their mode subtracted to ensure "
                    "consistent min/max levels independent of the sky "
                    "background. Enter here the lower threshold for the FITS "
                    "-> TIFF conversion."},
        "--preview-lim-high": {
            "task": ["Vb"],
            "sort": 201,
            "name": "V_WEIGHTBINMAX",
            "type": int,
            "defa": 500,
            "help": "The images have their mode subtracted to ensure "
                    "consistent min/max levels independent of the sky "
                    "background. Enter here the upper threshold for the FITS "
                    "-> TIFF conversion."},
        "--preview-reject-outliers": {
            "task": ["Vb"],
            "sort": 300,
            "name": "V_WEIGHT_BINOUTLIER",
            "type": str,
            "choi": ("Y", "N"),
            "maps": ("TRUE", "FALSE"),
            "defa": "N",
            "help": "Set this switch if you want hot pixels etc masked in the "
                    "binned image."}
    },

    "Sequence splitting": {
        "--nir-ngroups": {
            "task": ["Gs"],
            "sort": 100,
            "type": int,
            "help": "Number of groups into which you want to split a "
                    "sequence"},
        "--nir-grouplen": {
            "task": ["Gs"],
            "sort": 101,
            "type": int,
            "help": "Number of exposures in a sequence"}
    },

    "Sky subtraction": {
        "--sky-model-const": {
            "task": ["Ss"],
            "sort": 100,
            "type": str,
            "choi": ("Y", "N"),
            "maps": (True, False),
            "defa": "N",
            "help": "Choose between an automatic background model and a "
                    "constant sky value subtraction"},
        "--sky-detect-thresh": {
            "task": ["Ss"],
            "sort": 200,
            "name": "V_SKYSUBDETECTTHRESH",
            "type": float,
            "defa": 1.5,
            "help": "Detection threshold per pixel for an object to be "
                    "masked."},
        "--sky-detect-min-area": {
            "task": ["Ss"],
            "sort": 201,
            "name": "V_SKYSUBDETECTMINAREA",
            "type": int,
            "defa": 5,
            "help": "Minimum number of connected pixels for an object to be "
                    "masked."},
        "--sky-detect-mask-expand": {
            "task": ["Ss"],
            "sort": 202,
            "name": "V_SKYSUBMASKEXPAND",
            "type": float,
            "defa": "",
            "help": "If not empty, pixels within the scaled best-fit "
                    "SExtractor ellipse will be set to zero. In this way very "
                    "faint flux invisible in an individual image can be "
                    "caught as well. Good starting value: 3.0"},
        "--sky-smooth-scale": {
            "task": ["Ss"],
            "sort": 203,
            "name": "V_SKYSUBBACKSIZE",
            "type": int,
            "defa": 256,
            "help": "FWHM of the Gaussian convolution kernel used for sky "
                    "background modelling, in pixels."},
        "--sky-save-model": {
            "task": ["Ss"],
            "sort": 300,
            "name": "V_SAVESKYMODEL",
            "type": str,
            "choi": ("Y", "N"),
            "maps": ("Y", "N"),
            "defa": "N",
            "help": "Activate if you want the individual sky models to be "
                    "saved as a separate images (*sky.fits). Otherwise they "
                    "will be deleted on the fly."}
    },

    "Sorting": {
        "--sort-key-type": {
            "task": ["Fr"],
            "sort": 100,
            "name": "V_SORT_FITSKEY",
            "type": str,
            "defa": "OBJECT",
            "help": "The FITS key that identifies the exposure type"},
        "--sort-key-bias": {
            "task": ["Fr"],
            "sort": 200,
            "name": "V_SORT_BIAS",
            "type": str,
            "defa": "",
            "help": "Key value that identifies a BIAS"},
        "--sort-key-dark": {
            "task": ["Fr"],
            "sort": 201,
            "name": "V_SORT_DARK",
            "type": str,
            "defa": "",
            "help": "Key value that identifies a DARK"},
        "--sort-key-domeflat": {
            "task": ["Fr"],
            "sort": 202,
            "name": "V_SORT_DOMEFLAT",
            "type": str,
            "defa": "",
            "help": "Key value that identifies a DOMEFLAT"},
        "--sort-key-skyflat": {
            "task": ["Fr"],
            "sort": 203,
            "name": "V_SORT_SKYFLAT",
            "type": str,
            "defa": "",
            "help": "Key value that identifies a SKYFLAT"},
        "--sort-key-standard": {
            "task": ["Fr"],
            "sort": 204,
            "name": "V_SORT_STD",
            "type": str,
            "defa": "",
            "help": "Key value that identifies a STANDARD"},
    },

    "Source extraction": {
        "--sxt-detect-thresh": {
            "task": ["Pi", "Pd", "As"],
            "sort": 100,
            "name": "V_AP_DETECTTHRESH",
            "type": float,
            "defa": 5.0,
            "help": "Minimum detection threshold for the object detection. "
                    "Decrease this value if you want more sources. Minimum "
                    "useful value: 1.0-1.5"},
        "--sxt-detect-min-area": {
            "task": ["Pi", "Pd", "As"],
            "sort": 101,
            "name": "V_AP_DETECTMINAREA",
            "type": int,
            "defa": 5,
            "help": "Minimum number of connected pixels above the detection "
                    "threshold. Decrease this value if you want more objects. "
                    "Minimum useful value: 2-4, depending on sampling."},
        "--sxt-deblend-min-count": {
            "task": ["Pi", "Pd", "As"],
            "sort": 102,
            "name": "V_DEBLENDMINCONT",
            "type": float,
            "defa": 0.0005,
            "help": "Minimum contrast for the object detection of SExtractor. "
                    "Increase this value if you want LESS sources detected "
                    "within a larger source, e.g. a globular cluster or "
                    "galaxy."},
        "--sxt-fwhm-min": {
            "task": ["Pi", "Pd", "As"],
            "sort": 200,
            "name": "V_SEXCATMINFWHM",
            "type": float,
            "defa": 1.5,
            "help": "Sources with a FWHM (in pixels) smaller than this value "
                    "will be rejected from the catalogs (e.g. to get rid of "
                    "hot pixels)."},
        "--sxt-keep-flags": {
            "task": ["Pi", "Pd", "As"],
            "sort": 201,
            "name": "V_SEXCATFLAG",
            "type": int,
            "defa": 0,
            "help": "Objects with a SExtractor FLAG larger than this number "
                    "will be removed from the catalog. Enter 0 if you want "
                    "only clean sources, or 8 if you want to keep saturated "
                    "sources as well."},
        "--sxt-objects-min": {
            "task": ["Pi", "Pd", "As"],
            "sort": 202,
            "name": "V_AP_LOWNUM",
            "type": int,
            "defa": 1,
            "help": "The catalog/image must contain at least this many "
                    "objects (after all filterings) in order to be kept for "
                    "astrometry."},
        "--sxt-background-level": {
            "task": ["Pi", "Pd", "As"],
            "sort": 203,
            "name": "V_SEXBACKLEVEL",
            "type": float,
            "defa": "",
            "help": "If the image contains a significant amount of NAN pixel "
                    "values and you do not or cannot change this, then you "
                    "should set the sky background level manually. Otherwise "
                    "leave the field empty."},
        # where is the saturation level. is is --debloom-saturation ?
        "--sxt-filter-hotpix": {
            "task": ["Pi", "Pd", "As"],
            "sort": 300,
            "name": "V_AP_FILTER",
            "type": str,
            "choi": ("Y", "N"),
            "maps": ("Y", "N"),
            "defa": "N",
            "help": "If your object catalogues are plagued by hot pixels, "
                    "then try this option (runs an additional outlier "
                    "rejection)."}
    },

    "Splitting": {
        "--links-scratch-dir": {
            "task": ["Lc"],
            "sort": 100,
            "meta": "DIR",
            "type": str,
            "help": "Full path to the scratch directory where you want to "
                    "have the chips."},
        "--links-chips": {
            "task": ["Lc"],
            "sort": 101,
            "type": int,
            "help": "Blank-separated list of the chips you want to move. For "
                    "example:  1 3 5 7"},
        "--links-resolve-dir": {
            "task": ["Lr"],
            "sort": 200,
            "meta": "DIR",
            "type": str,
            "help": "Directory for which you want to resolve the link "
                    "structure."},
        "--rename": {
            "task": ["Fs"],
            "sort": 300,
            "name": "V_PRE_RENAME_CHECKED",
            "type": str,
            "choi": ("Y", "N"),
            "maps": (1, 0),
            "defa": "N",
            "help": "If activated, renames the images to the value of the "
                    "FITS key given by --rename-key"},
        "--rename-key": {
            "task": ["Fs"],
            "sort": 301,
            "name": "V_RENAME_FITSKEY",
            "type": str,
            "defa": "ARCFILE",
            "help": "FITS key used to rename files"},
        "--split-mircube": {
            "task": ["Fs"],
            "sort": 302,
            "name": "V_PRE_SPLITMIRCUBE",
            "type": str,
            "choi": ("Y", "N"),
            "maps": ("Y", "N"),
            "defa": "N",
            "help": "Whether the MIR cubes should be split into individual "
                    "chop-nod corrected exposures, or whether the entire "
                    "stacked cube should be kept."},
        "--image-min-overlap": {
            "task": ["Ds"],
            "sort": 400,
            "type": int,
            "defa": 1000,
            "help": "Images with an overlap larger than this value are "
                    "considered to belong to the same target. The maximum "
                    "allowed value is 1024."}
    },

    "Weighting": {
        "--wt-uniform": {
            "task": ["Wg"],
            "sort": 100,
            "name": "V_GLOBW_UNIFORMWEIGHT",
            "type": str,
            "choi": ("Y", "N"),
            "maps": ("TRUE", "FALSE"),
            "defa": "N",
            "help": "If you do not want the normalised flat to form the basis "
                    "for the weights, then activate this switch"},
        "--wt-dark-min": {
            "task": ["Wg"],
            "sort": 201,
            "name": "V_GLOBWDARKMIN",
            "type": float,
            "defa": "",
            "help": "Lower threshold for pixels in the masterdark"},
        "--wt-dark-max": {
            "task": ["Wg"],
            "sort": 200,
            "name": "V_GLOBWDARKMAX",
            "type": float,
            "defa": "",
            "help": "Upper threshold for pixels in the masterdark"},
        "--wt-flat-min": {
            "task": ["Wg"],
            "sort": 203,
            "name": "V_GLOBWFLATMIN",
            "type": float,
            "defa": 0.5,
            "help": "Lower threshold for pixels in the normalised flat"},
        "--wt-flat-max": {
            "task": ["Wg"],
            "sort": 202,
            "name": "V_GLOBWFLATMAX",
            "type": float,
            "defa": 1.6,
            "help": "Upper threshold for pixels in the normalised flat"},
        # where is Use BIAS instead of DARK
        "--wt-defect-flat-smooth-scale": {
            "task": ["Wg"],
            "sort": 300,
            "name": "V_DEFECT_KERNELSIZE",
            "type": int,
            "defa": "",
            "help": "The normalised flat-field will be smoothed by a kernel "
                    "of this size. The unsmoothed flat is then divided by the "
                    "smoothed flat to remove large-scale effects. The "
                    "resulting image can be used to search for chip defects."},
        "--wt-defect-bg-smooth-scale": {
            "task": ["Wg"],
            "sort": 301,
            "name": "V_DEFECT_KERNELSIZE_SF",
            "type": int,
            "defa": "",
            "help": "The superflat will be smoothed by a kernel of this size. "
                    "The unsmoothed flat is then divided by the smoothed flat "
                    "to remove large-scale effects. The resulting image can "
                    "be used to search for chip defects."},
        "--wt-defect-flat-rowtol": {
            "task": ["Wg"],
            "sort": 302,
            "name": "V_DEFECT_ROWTOL",
            "type": int,
            "defa": "",
            "help": "Rows that deviate by that fraction or more from the "
                    "other rows are masked (value: e.g. 0.02)"},
        "--wt-defect-bg-rowtol": {
            "task": ["Wg"],
            "sort": 303,
            "name": "V_DEFECT_ROWTOL_SF",
            "type": int,
            "defa": "",
            "help": "Rows that deviate by that fraction or more from the "
                    "other rows are masked (value: e.g. 0.02)"},
        "--wt-defect-flat-coltol": {
            "task": ["Wg"],
            "sort": 304,
            "name": "V_DEFECT_COLTOL",
            "type": int,
            "defa": "",
            "help": "Columns that deviate by that fraction or more from the "
                    "other columns are masked.(value: e.g. 0.02)"},
        "--wt-defect-bg-coltol": {
            "task": ["Wg"],
            "sort": 305,
            "name": "V_DEFECT_COLTOL_SF",
            "type": int,
            "defa": "",
            "help": "Columns that deviate by that fraction or more from the "
                    "other columns are masked.(value: e.g. 0.02)"},
        "--wt-defect-flat-clustertol": {
            "task": ["Wg"],
            "sort": 306,
            "name": "V_DEFECT_CLUSTOL",
            "type": int,
            "defa": "",
            "help": "Pixels that deviate by this fraction or more from the "
                    "pixels in the local neighbourhood are masked (value: "
                    "e.g. 0.05 to 0.3)"},
        "--wt-defect-bg-clustertol": {
            "task": ["Wg"],
            "sort": 307,
            "name": "V_DEFECT_CLUSTOL_SF",
            "type": int,
            "defa": "",
            "help": "Pixels that deviate by this fraction or more from the "
                    "pixels in the local neighbourhood are masked (value: "
                    "e.g. 0.05 to 0.3)"},
        "--wt-adu-min": {
            "task": ["Wc"],
            "sort": 400,
            "name": "V_WEIGHTLOWTHRESHOLD",
            "type": float,
            "defa": "",
            "help": "Pixels below this value will be set to zero in the "
                    "WEIGHT"},
        "--wt-adu-max": {
            "task": ["Wc"],
            "sort": 401,
            "name": "V_WEIGHTHIGHTHRESHOLD",
            "type": float,
            "defa": "",
            "help": "Pixels above this value will be set to zero in the "
                    "WEIGHT"},
        "--wt-cosmics-detect-thresh": {
            "task": ["Wc"],
            "sort": 402,
            "name": "V_COSMICDMIN",
            "type": float,
            "defa": 1,
            "help": "Detection threshold of a pixel affected by a cosmic"},
        "--wt-cosmics-detect-min-area": {
            "task": ["Wc"],
            "sort": 403,
            "name": "V_COSMICDT",
            "type": int,
            "defa": 6,
            "help": "Minimum number of connected pixels that make up a "
                    "cosmic"},
        "--wt-cosmics-thresh": {
            "task": ["Wc"],
            "sort": 404,
            "name": "V_COSMICSTHRESHOLD",
            "type": float,
            "defa": 0.1,
            "help": "Increase this value for slightly undersampled data to a "
                    "value higher than 10, 100 or even 1000 to avoid masked "
                    "stellar cores. If you do not want any masking of cosmics "
                    "to take place, then leave this field empty."},
        "--wt-spikes-mask": {
            "task": ["Wc"],
            "sort": 500,
            "name": "V_MASKBLOOMSPIKE",
            "type": str,
            "choi": ("Y", "N"),
            "maps": (1, 0),
            "defa": "N",
            "help": "Detects blooming spikes and sets their weight to zero"},
        "--wt-spikes-thresh": {
            "task": ["Wc"],
            "sort": 501,
            "name": "V_BLOOMLOWLIMIT",
            "type": int,
            "defa": 20000,
            "help": "A lower brightness threshold for the detection of "
                    "blooming spikes."},
        "--wt-spikes-pix-min": {
            "task": ["Wc"],
            "sort": 502,
            "name": "V_BLOOMMINAREA",
            "type": int,
            "defa": 100,
            "help": "The minimum number of pixels in the blooming spike."},
        "--wt-spikes-extend-range": {
            "task": ["Wc"],
            "sort": 503,
            "name": "V_BLOOMWIDTH",
            "type": float,
            "defa": 0.,
            "help": "Extends the dynamic range in a blooming spike by this "
                    "value on the bright and the faint end. This is useful if "
                    "the spike is not fully detected automatically. Default "
                    "setting: 0 (empty)"}
    }
}
# quick lookup list of all parameters
parse_parameters_allkeys = []
for group in parse_parameters:
    parse_parameters_allkeys.extend(list(parse_parameters[group].keys()))
