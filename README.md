TheliTools
============

*THELI* is a tool for the automated reduction of astronomical images. It
features

- Automated reduction of optical, NIR and MIR data
- 90 pre-configured instruments
- Parallelisation
- Flexible background correction
- Automatic distortion correction and creation of large mosaics
- Highly flexible coaddition: e.g. locking onto proper motion targets, various
  projections, etc
- Optimised weighting schemes and defect detection
- Crosstalk and non-linearity correction
- Atmospheric transparency correction
- Absolute flux calibration
- Extensive documentation and [online help](https://www.astro.uni-bonn.de/theli/gui/index.html)


Usage Example and Demo
----------------------


Requirements
------------
* Python including C-headers (python-dev)
* Python packages: numpy, scipy, matplotlib, pyfits
* Python 3 (version >= 3.4)
* Python 3 packages: astropy or pyfits (optional)
* *THELI* package, requires (*CDS client*)
* scripts and configuration files from the *THELI* graphical user interface
  (GUI)
* *scamp* (optional but recommended), requires *PLplot* with *cairo* driver

**Note**: some more C-libraries, that may not be preinstalled on your system, are
required to build the binaries 


Installation
------------
The *TheliWrapper* is written in Python 3. All required packages are part of
the Python standard library, but it is recommended to install
[pyfits](https://pythonhosted.org/pyfits/) or
[astropy](http://docs.astropy.org/en/stable/) for more efficient access to FITS
image headers.

1) To use the software it is neccessary to install the
   [*THELI*](https://www.astro.uni-bonn.de/theli/) astronomical data reduction
   package. It requires to install the
   [*CDS client*](http://cdsarc.u-strasbg.fr/doc/cdsclient.html) first.
   To install *THELI*, download it from
   [here](https://www.astro.uni-bonn.de/theli/gui/download.html) or use

       installation/theli-1.9.5.tgz

   shipped with this package. Extract the archiev and run the install scipt in
   the *pipesetup* folder with

       ./install.sh -m "ALL"

   to build the package from source.

2) It is highly recommended to install *scamp* to compute precise astrometric
   solutions. Although used by *THELI*, it is not part of the package itself
   and requires *PLplot* with the *cairo* driver. On some linux distributions
   (e.g. Ubunut, Linux Mint or Arch Linux) *scamp* can be found precompiled in
   the package repositories. Otherwise
   [download it](https://www.astromatic.net/software/scamp) and build it with

       ./configure
       make
       make install

3) Next install the *THELI GUI*. It requires *Qt3* which has to be installed
   manualy on most systems. If you want to avoid this you can use

       installation/gui-2.10.3-noGUI.tar.gz

   which only contains the reduction scripts and parameter files. If you want
   to able to use the GUI as well,
   [download it](https://www.astro.uni-bonn.de/theli/gui/download.html) and
   install it with

       ./install.sh

   and copy the *scamp* binary to the folder

       bin/theli/bin/[your platform]

   of your *THELI* installation.


MAINTAINERS
-----------
[Jan Luca van den Busch](https://github.com/jlvdb) (University of Bonn)
