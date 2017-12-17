"""
Defines the data monitor for the Reduction class
"""

import os
import shutil
from time import time
from fnmatch import fnmatch
from inspect import stack

from .base import (FITS_EXTENSIONS,
                   extract_tag, check_system_lock, get_FITS_header_values)


MASTER_PATTERN = ("BIAS_", "FLAT_", "DARK_")


class Folder(object):
    """Class with convenice functions to monitor the content and reduction
    progress of the THELI data folders. Uses file index to reduce redundant
    storage access. The index is only updated, if a minimum time interval has
    passed, or the function which calls the class method changes.

    Arguments:
        path [string]:
            path to the folder that is monitored
        nchips [int]:
            number of chips the instrument has
    """

    _fits_index = {}  # database of FITS files in the folder
    _update_time = 0  # time stamp of last update
    _update_delay = 0.05  # minimum time in seconds between two updates
    _last_call = "<module>"  # default calling function at initialization

    def __init__(self, path, nchips=100):
        super(Folder, self).__init__()
        self.abs = os.path.abspath(path)
        self.parent, self.path = os.path.split(self.abs)
        self.nchips = nchips
        self._update_index()  # generate initial FITS index

    def _update_index(self, force=True):
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
                    newtag = extract_tag(f, self.nchips)
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

    def filters(self):
        """List the filters of FITS images, if possible"""
        self._update_index()
        filters = set()
        for f in self._fits_index:
            try:
                # works for splitted images
                filters.add(get_FITS_header_values(
                    os.path.join(self.abs, f), ["FILTER"])[0])
            except KeyError:
                filters.add('(null)')  # fallback value
        return filters

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
        weightfolder = os.path.join(self.parent, "WEIGHTS")
        if not os.path.exists(weightfolder):
            return False, False
        fitsfiles = self.fits(ignore_sub=True)
        # check weight image existance and compare time stamps
        all_present, all_newer = True, True
        for fitsfile in fitsfiles:
            # match weight image with a fits image
            weight = os.path.join(  # expected weight name from FITS image
                weightfolder, ".weight".join(
                    os.path.splitext(os.path.basename(fitsfile))))
            if not os.path.exists(weight):
                all_present = False  # no weight file exists for this image
            if (os.path.getctime(weight) - os.path.getctime(fitsfile)) < 0:
                all_newer = False  # this file is outdated
        return all_present, all_newer  # test passed

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
            if fnmatch(entry, target):
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
