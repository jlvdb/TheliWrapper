# TheliWrapper

From the *THELI GUI* [webpage](https://www.astro.uni-bonn.de/theli/gui/index.html)
> *THELI* is a powerful and easy-to-use package for astronomical image reduction, offering e.g.
> * Automated reduction of optical, NIR and MIR data
> * 90 pre-configured instruments
> * Parallelisation
> * Flexible background correction
> * Automatic distortion correction and creation of large mosaics
> * Highly flexible coaddition: e.g. locking onto proper motion targets, various
    projections, etc
> * Optimised weighting schemes and defect detection
> * Crosstalk and non-linearity correction
> * Atmospheric transparency correction
> * Absolute flux calibration
> * Extensive documentation and online help


## Usage

For a detailed description and an usage demonstration, refere to the projects
[Wiki-page](https://github.com/jlvdb/TheliWrapper/wiki).


## Requirements

The *TheliWrapper* is entirely written in Python 3, but it depends on external
components which are written in Python 2 and C/C++. Here is a (not neccessarily
complete) list of components you will need to use the wrapper.

Python:
* Python 2 and 3 (version >= 2.5 and version >= 3.4)
* Python 2 packages: numpy, scipy, matplotlib, pyfits
* Python 3 packages: astropy or pyfits (optional, but recommended)

C-libraries:
* Python C-headers
* FFTW, GSL (GNU Scientific Library)
* cfitsio, CCfits
* LibTIFF, LibPNG

**Note:** More C-libraries then listed may be required to build the binaries,
depending on your system.

Programs:
* csh, wget
* ImageMagick
* *THELI* package, requires *CDS client*
* scripts and configuration files from the *THELI* graphical user interface
  (GUI)
* *scamp* (optional but recommended), requires *PLplot* with *cairo driver*


## Installation

These instructions should guide you through the steps of installing the
*TheliWrapper* together with its dependencies:

1)  *THELI* depends on the *CDS client*.
    [Download](http://cdsarc.u-strasbg.fr/doc/cdsclient.html) the most recent
    version, extract it and install it with

        ./configure
        make
        make install

2)  To install *THELI*,
    [download](https://www.astro.uni-bonn.de/theli/gui/download.html) and
    extract it and run the install scipt with `pipesetup/install.sh -m "ALL"`
    to build the package from source.

3)  It is highly recommended to install *scamp* to compute precise astrometric
    solutions. Although used by *THELI*, it is not part of the package itself
    and requires *PLplot* with the *cairo* driver. On some linux distributions
    (e.g. Ubuntu, Linux Mint or Arch Linux) *scamp* can be found precompiled in
    the package repositories. Otherwise
    [download](https://www.astromatic.net/software/scamp) it and try to build
    it from source with

        ./configure
        make
        make install

4)  Install the *THELI GUI*. It requires *Qt3* which has to be installed manualy
    on most systems. If you want to avoid this you can use

        **missing link** -> gui-2.10.3-noGUI.tar.gz

    which only contains the reduction scripts, parameter files and reference
    catalogues. If you want to be able to use the GUI as well,
    [download](https://www.astro.uni-bonn.de/theli/gui/download.html) the
    original version instead.  
    Install it with `./install.sh` and copy the *scamp* binary to the binary
    folder of your *THELI* installation: `[path to THELI]/bin/[your platform]/`

5)  To install the *TheliWrapper*, just download the
    [source files](https://github.com/jlvdb/TheliWrapper) and copy them to your
    preferred destination. When you run `theli.py` for the first time it will
    locate the *THELI* configuration folder (`/home/user/.theli`) and will set
    up itself automatically.  
    Whenever you change your *THELI* installation, it may be necessary to delete
    `/home/janluca/.theli/theli_paths.py` such that it will be recreated.


## Issues

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


## Maintainers

[Jan Luca van den Busch](https://github.com/jlvdb)
(Argelander Institute for Astronomy)
