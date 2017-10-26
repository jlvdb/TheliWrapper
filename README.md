![# TheliWrapper](https://github.com/jlvdb/TheliWrapper/blob/extra-data/wiki_images/img/logo.jpeg)

The *TheliWrapper* is a project to simplify the process of astronomical image
reduction with the *THELI* (software package for astronomical image reduction
in optical, near- and mid-infrared) significantly.  
It combines the simplicity of the *THELI GUI*'s preconfigured instruments and
parameter files with the ability to do large scale batch processing for large
observation projects.

For an overview of the *TheliWrapper*'s features, we can refer to the
*THELI GUI* [webpage](https://www.astro.uni-bonn.de/theli/gui/):

> *THELI* is a powerful and easy-to-use package for astronomical image
> reduction, offering e.g.
> * Automated reduction of optical, NIR and MIR data
> * 90 pre-configured instruments
> * Parallelisation
> * Flexible background correction
> * Automatic distortion correction and creation of large mosaics
> * Highly flexible coaddition: e.g. locking onto proper motion targets,
>   various projections, etc
> * Optimised weighting schemes and defect detection
> * Crosstalk and non-linearity correction
> * Atmospheric transparency correction
> * Absolute flux calibration
> * Extensive documentation and online help


## About this README

This file will guide you through the installation of the program and inform you
about the current development stage or known issues. Any other topic will be
covered by the the project's
[Wiki-page](https://github.com/jlvdb/TheliWrapper/wiki), giving more
documentation and a step-by-step usage demonstration you can download and try
yourself.  
For any further problems, please contact the project maintainer(s) (see below).


## Requirements

The *TheliWrapper* is entirely written in Python 3, but it depends on external
components which are written in Python 2 or C/C++. Here is a (not necessarily
complete) list of components you will need to use the wrapper.

#### Python:
* Python 2 and 3 (version >= 2.5 and version >= 3.4)
* Python 2 packages: numpy, scipy, matplotlib, pyfits
* Python 3 packages: astropy or pyfits (optional, but recommended)

#### C-libraries:
* Python C-headers
* FFTW, GSL (GNU Scientific Library)
* cfitsio, CCfits
* LibTIFF, LibPNG
(depends on your system)

#### Programs:
* csh, wget
* ImageMagick
* *THELI* package, requires *CDS client*
* scripts and configuration files from *THELI* graphical user interface (GUI)
* *scamp* (optional but recommended), requires *PLplot* with *cairo driver*


## Installation

These instructions should guide you through the steps of installing the
*TheliWrapper* together with its dependencies:

#### CDS client
*THELI* depends on the *CDS client*.
[Download](http://cdsarc.u-strasbg.fr/doc/cdsclient.html) the most recent
version, extract it and install it with

    ./configure
    make
    make install

#### THELI
To install *THELI*,
[download](https://www.astro.uni-bonn.de/theli/gui/download.html) and extract
it and run the install scipt in `pipesetup/` with `install.sh -m "ALL"` to
build the package from source.

#### Scamp
Even though *THELI* offers alternatives, it is highly recommended to install
*scamp* to compute precise astrometric solutions. It is not part of the package
itself, so has to be installed separately and requires *PLplot* with the
*cairo*-driver. On some linux distributions (e.g. Ubuntu, Linux Mint or
Arch Linux) *scamp* can be found precompiled in the package repositories.  
Otherwise [download](https://www.astromatic.net/software/scamp) it and try to
build it from source (which can be tricky) with

    ./configure
    make
    make install

#### THELI GUI
[Download](https://www.astro.uni-bonn.de/theli/gui/download.html) and install
the *THELI GUI* by using `./install.sh` and copy the *scamp* binary to the
binary folder of your *THELI* installation:

     [path to THELI]/bin/[your platform]/

The GUI requires *Qt3* which has to be installed manualy on most systems.

> **NOTE: Will be available in a future version of the TheliWrapper**
> If you want to avoid installing *Qt3* you can use a
> [modified version](https://github.com/jlvdb/TheliWrapper/raw/extra-data/INSTALL/gui-2.10.3_modified.tar.gz)
> which only contains the reduction scripts, parameter files and reference
> catalogues.


#### TheliWrapper
To install the *TheliWrapper*, just download the
[latest release](https://github.com/jlvdb/TheliWrapper/releases/latest) and
copy and extract it to your preferred destination. When you run `theli.py` for
the first time it will locate the *THELI* configuration folder
(`/home/user/.theli`) and will set up itself automatically.  
Whenever you change your *THELI* installation, it may be necessary to delete
`/home/janluca/.theli/theli_paths.py` such that it will be recreated.


## Project progress and known issues

This project is under development, even though the most important data
recution steps are implented. Yet missing are:
* Photometry (direct and indirect)
* Constant sky model subtraction
* Copying and restoring the astrometric solution to the image header
  manually

If you work with **(near/mid) infrared data** the following tools are availble
but still experimental:
* Cross talk correction
* Squence splitting
* Chop/nod sky subtraction
* Collapse correction

If you have any problems or notice any unexpected behaviour, please contact
the maintainer(s) or create a *new issue* on the project's GitHub-page.


## Maintainers

[Jan Luca van den Busch](https://github.com/jlvdb)
([Argelander Institute for Astronomy](https://astro.uni-bonn.de/en))


## Acknowledgements

Please cite the following two papers when publishing your scientific work based on *THELI*:

> Schirmer M. 2013, ApJS, 209, 21: *THELI GUI – Convenient reduction of optical, near- and mid-infrared imaging data*

> Erben, T., Schirmer, M., Dietrich, J. et al. 2005, AN, 326, 432: *GaBoDS: The Garching-Bonn Deep Survey. IV. Methods for the image reduction of multi-chip cameras demonstrated on data from the ESO Wide-Field Imager*
