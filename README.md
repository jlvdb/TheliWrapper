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
  reduction, offering e.g.
> * Automated reduction of optical, NIR and MIR data
> * 90 pre-configured instruments
> * Parallelisation
> * Flexible background correction
> * Automatic distortion correction and creation of large mosaics
> * Highly flexible coaddition: e.g. locking onto proper motion targets,
    various projections, etc
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
Install the *THELI GUI*. It requires *Qt3* which has to be installed manualy on
most systems. If you want to avoid this you can use a
[modified version](https://github.com/jlvdb/TheliWrapper/raw/extra-data/INSTALL/gui-2.10.3_modified.tar.gz)
which only contains the reduction scripts, parameter files and reference
catalogues. If you want to be able to use the GUI as well,
[download](https://www.astro.uni-bonn.de/theli/gui/download.html) the original
version instead.  
In both cases install it with `./install.sh` and copy the *scamp* binary to the
binary folder of your *THELI* installation:

     [path to THELI]/bin/[your platform]/

#### TheliWrapper
To install the *TheliWrapper*, just download the
[latest release](https://github.com/jlvdb/TheliWrapper/releases/latest) and
copy and extract it to your preferred destination. When you run `theli.py` for
the first time it will locate the *THELI* configuration folder
(`/home/user/.theli`) and will set up itself automatically.  
Whenever you change your *THELI* installation, it may be necessary to delete
`/home/janluca/.theli/theli_paths.py` such that it will be recreated.


## Project progress and known issues

Not all components and features of the *THELI GUI* are implemented yet, as it
is still under development. This sections gives you an overview over what you
cannot do yet, or what may have unexpected behaviour.

##### Features to reduce infrared data are experimental yet:
* Cross talk correction
* Squence splitting
* Chop/nod sky subtraction
* Collapse correction

##### Some main features of the original *THELI GUI* are not implemented yet:
* Photometry (direct and indirect)
* Constant sky model subtraction
* Copying and restoring the astrometric solution to the image header
  manually

##### The tasks in the *Miscellaneous* section are not implemented:
* Combine folder of image
* Imalyzer
* Image statistics
* Absolute photometric zeropoint
* Animate
* Prepare color picutre

If you have any problems or notice any unexpected behaviour, please contact
the maintainer(s) or create a
[*new issue*](https://github.com/jlvdb/TheliWrapper/issues/new)
(on the project's GitHub-page).


## Acknowledgements

Please cite the following two papers when publishing your scientific work based on *THELI*:

> Schirmer M. 2013, ApJS, 209, 21: *THELI GUI – Convenient reduction of optical, near- and mid-infrared imaging data*

> Erben, T., Schirmer, M., Dietrich, J. et al. 2005, AN, 326, 432: *GaBoDS: The Garching-Bonn Deep Survey. IV. Methods for the image reduction of multi-chip cameras demonstrated on data from the ESO Wide-Field Imager*


## Maintainers

[Jan Luca van den Busch](https://github.com/jlvdb)
([Argelander Institute for Astronomy](https://astro.uni-bonn.de/en))
