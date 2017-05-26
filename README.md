TheliWrapper
============

*THELI* is a tool for the automated reduction of astronomical images. It
features

* Automated reduction of optical, NIR and MIR data
* 90 pre-configured instruments
* Parallelisation
* Flexible background correction
* Automatic distortion correction and creation of large mosaics
* Highly flexible coaddition: e.g. locking onto proper motion targets, various
  projections, etc
* Optimised weighting schemes and defect detection
* Crosstalk and non-linearity correction
* Atmospheric transparency correction
* Absolute flux calibration
* Extensive documentation and
  [online help](https://www.astro.uni-bonn.de/theli/gui/index.html)


Usage
-----

The *TheliWrapper* provides three executables:

1)  `theli.py JOBLIST INST ...`  
    Main executable, does the job of data reduction. The usage is described
    in detail on the [wiki page](https://github.com/jlvdb/TheliTools/wiki).  
    *JOBLIST* specifies the reduction step(s) to apply, e.g. `CbCfCs` to
    process the master bias frame (`Cb`), the flat field (`Cf`) and apply them
    to the data (`Cs`). For more information, try `theli.py --help-jobs`.  
    *INST* specifies the instrument used for the observations, e.g.
    `ACAM@WHT`.  
    For information on how to specify data folders, try `theli --help`. A list
    of all parameters controlling the reduction, use `theli --help-parameters`.

2)  `theli_copy_coadds SOURCE DESTINATION`  
    Searches coadded images in the *SOURCE* folder and copies them to the
    *DESTINATION* folder.

3)  `theli_reset_folder FOLDERS`  
    Restores the orignal input images in each of the *FOLDERS* and deletes all
    other folder content.


Requirements
------------

Python:
* Python (version >= 2.5), including C-headers (python-dev)
* Python packages: numpy, scipy, matplotlib, pyfits
* Python 3 (version >= 3.4)
* Python 3 packages: astropy or pyfits (optional)

C-libraries:
* Python C-headers
* FFTW, GSL (GNU Scientific Library)
* cfitsio, CCfits
* LibTIFF, LibPNG
* PLplot with cairo-driver

Programs:
* csh, wget
* ImageMagick
* *THELI* package, requires *CDS client*
* scripts and configuration files from the *THELI* graphical user interface
  (GUI)
* *scamp* (optional but recommended), requires *PLplot* with *cairo driver*

**Note:** More C-libraries then listed may be required to build the binaries,
depending on your system.


Installation
------------

The *TheliWrapper* is written in Python 3. All required packages are part of
the Python standard library, but it is recommended to install
[pyfits](https://pythonhosted.org/pyfits/) or
[astropy](http://docs.astropy.org/en/stable/) for more efficient access to FITS
image headers.

1)  To use the software it is neccessary to install the
    [*THELI*](https://www.astro.uni-bonn.de/theli/) astronomical data reduction
    package. It requires to install the
    [*CDS client*](http://cdsarc.u-strasbg.fr/doc/cdsclient.html) first.
    To install *THELI*,
    [download](https://www.astro.uni-bonn.de/theli/gui/download.html) it or use

        installation/theli-1.9.5.tgz

    shipped with this package. Run the install scipt in the *pipesetup* folder
    with `./install.sh -m "ALL"` to build the package from source.

2)  It is highly recommended to install *scamp* to compute precise astrometric
    solutions. Although used by *THELI*, it is not part of the package itself
    and requires *PLplot* with the *cairo* driver. On some linux distributions
    (e.g. Ubuntu, Linux Mint or Arch Linux) *scamp* can be found precompiled in
    the package repositories. Otherwise
    [download](https://www.astromatic.net/software/scamp) it and build it with

        ./configure
        make
        make install

3)  Finally install the *THELI GUI*. It requires *Qt3* which has to be
    installed manualy on most systems. If you want to avoid this you can use

        installation/gui-2.10.3-noGUI.tar.gz

    which only contains the reduction scripts, parameter files and reference
    catalogues. If you want to be able to use the GUI as well,
    [download](https://www.astro.uni-bonn.de/theli/gui/download.html) the
    original version instead.  
    Install it with `./install.sh` and copy the *scamp* binary to the binary
    folder of your *THELI* installation: `[path to THELI]/bin/[your platform]/`


Issues
------

* Features to reduce infrared data are experimental yet:
    * Cross talk correction
    * Squence splitting
    * Chop/nod sky subtraction
    * Collapse correction
* Some main features of the original *THELI GUI* are not implemented yet:
    * Photometry (direct and indirect)
    * Constant sky model subtraction
    * Copying and restoring the astrometric solution to the image header
      manually
* The tasks in the *Miscellaneous* section are not implemented:
    * Combine folder of image
    * Imalyzer
    * Image statistics
    * Absolute photometric zeropoint
    * Animate
    * Prepare color picutre


Maintainers
-----------

[Jan Luca van den Busch](https://github.com/jlvdb) (University of Bonn)
