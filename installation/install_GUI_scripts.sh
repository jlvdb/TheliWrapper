#!/bin/bash

# read command line arguments

theliversion="theli-1.9.5"
delay=1.0

DO_SCISOFT="N"

# How many CPUs does this machine have? This is used for running make in parallel mode
# We leave the user 1 CPU for convenience
ncpu=`cat /proc/cpuinfo | grep processor | wc | awk '{if ($1>1) print $1-1; else print $1}'`

# exit conditions

# are we using the right qmake/uic versions
#test=`which qmake-qt3 | wc -w`
#if [ "${test}" = "1" ]; then
#    QMAKE=`which qmake-qt3`
#else
#   qmake -v >& bla
#   QMAKEVERSION=`awk '(NR==1) {print $5}' bla | awk 'BEGIN {FS="."} {print $1}'`
#   if [ "${QMAKEVERSION}" = "3" ]; then
#       QMAKE=`which qmake`
#   else
#       echo "Qt qmake is not version 3, or not installed!"
#       echo "Please install the Qt3 development package, or if already done then"
#       echo "point the link /usr/bin/qmake to the Qt3 version"
#       exit
#   fi
#fi

# are we running the script from the right directory
instdir=`pwd`
instdir=`basename ${instdir}`
if [ "${instdir}" = "gui" ]; then
    echo "You must run this script from within:   `pwd`-<version>"
    echo "and not from within the current dir:    `pwd`"
    exit
fi

GoOn=0
while [ $GoOn = 0 ]
do
   case $1 in
   -scisoft)       # only for scisoft maintainers
       DO_SCISOFT=Y
       shift
       ;;
    *)
       GoOn=1
       ;;
   esac
done

P_GAWK=`which gawk`


#################################################
# move an old installation/link away,
# and prepare linking
#################################################

guiversion=`pwd | ${P_GAWK} 'BEGIN{FS="/"} {print $NF}'`
guipath=`pwd`
cd ..
mainpath=`pwd`       #/home/user/THELI
# some other path names we need
thelipath=${mainpath}/theli/
packagepath=${guipath}/packages/
guiscriptpath=${guipath}/scripts/

date=`date +%F`

test -e theli && rm theli
test -e gui && rm gui

if [ ! -d ${theliversion} ]; then
    echo "ERROR: Could not find ${theliversion} required by this GUI version."
    exit
fi

cd ${mainpath}
ln -sf ${theliversion} theli
ln -sf ${guipath} gui
cd theli
if [ -L gui ]; then
    rm gui
fi
ln -sf ${guipath} gui
cd ${guipath}
test -L ${guiversion} && rm ${guiversion}


##################################################
# done preparing stuff
##################################################

cd ${guipath}

CC=gcc
os=`uname`

if [ "${os}" == "Linux" ]; then
  LONG=`${thelipath}/pipesetup/endian | ${P_GAWK:?} '($1=="Sizes:") {print substr($5,3,1)}'`
  if [ "${LONG}" == "8" ]; then
    os=${os}"_64"
  fi
fi

echo " "
echo "Your operating system is: " ${os}
echo " "

bindir=${thelipath}bin/${os}/

####################################################
# initialising
####################################################

cd ${guipath}

# create a new progs.ini file
cp ${thelipath}/scripts/${os}/progs.ini scripts/progsini_tmp

cd ${guiscriptpath}

${P_GAWK} 'BEGIN {FS="="} {
     if ($1=="PIPESOFT") {
         print $1"=""'${thelipath}'"
         print "BIN_ANET=${PIPESOFT}/gui/packages/astrometry/build/bin/"}
     if ($1=="CONF") print $1"=${PIPESOFT}/gui/reduction; export CONF"
     if ($1=="SCRIPTS") print $1"=${PIPESOFT}/gui/scripts/"
     if ($1=="export TEMPDIR") print $1"=~/.theli/tmp/"
     if ($1 != "CONF" && 
         $1 != "export TEMPDIR" && 
         $1 != "PIPESOFT" &&
         $1 != "P_ACLIENT" &&
         $1 != "NPARA" &&
         $1 != "P_SCAMP" &&
         $1 != "S_ASTROMETRIX" &&
         $1 != "S_PHOTOMETRIX" &&
         $1 != "SCRIPTS" &&
         $1 != "UTILSCRIPTS" &&
         $1 != "S_SCAMPCAT" &&
         $1 != "S_PHOTOABS" &&
         $1 != "S_APLASTROMSCAMP" &&
         $1 != "S_SUPERFLATEXCLUSION") print
     }' progsini_tmp > progs.ini

{
echo "#"
echo "# this is needed for the GUI"
echo "#"
echo S_ZPABS | ${P_GAWK} '{print $1"=${SCRIPTS}/zpabs.py"}'
echo S_SCAMPCAT | ${P_GAWK} '{print $1"=${SCRIPTS}/scampcat.py"}'
echo S_APLASTROMSCAMP | ${P_GAWK} '{print $1"=${SCRIPTS}/aplastrom_scamp.py"}'
echo S_SUPERFLATEXCLUSION | ${P_GAWK} '{print $1"=${SCRIPTS}/superflatexclusion.py"}'
echo P_GETPMMOBJECTS | ${P_GAWK} '{print $1"=${BIN}/get_pmm_objects"}'
echo P_LDACDESC | ${P_GAWK} '{print $1"=${BIN}/ldacdesc"}'
echo P_LDACDELTAB | ${P_GAWK} '{print $1"=${BIN}/ldacdeltab"}'
echo P_LDACDELKEY | ${P_GAWK} '{print $1"=${BIN}/ldacdelkey"}'
echo P_LDACPUTXY | ${P_GAWK} '{print $1"=${BIN}/ldacputxy"}'
echo P_FITSFLIP | ${P_GAWK} '{print $1"=${BIN}/fitsflip"}'
echo P_DEBLOOM | ${P_GAWK} '{print $1"=${BIN}/debloom"}'
echo P_EQUALISEBAYERFLAT | ${P_GAWK} '{print $1"=${BIN}/equalisebayerflat"}'
echo P_FITSCOLLAPSE | ${P_GAWK} '{print $1"=${BIN}/fitscollapse"}'
echo P_FITSWRAP | ${P_GAWK} '{print $1"=${BIN}/fitswrap"}'
echo P_FITSCUBESLICE | ${P_GAWK} '{print $1"=${BIN}/fitscubeslice"}'
echo P_FITSADDKEY | ${P_GAWK} '{print $1"=${BIN}/fitsaddkey"}'
echo P_FITSCUT | ${P_GAWK} '{print $1"=${BIN}/fitscut"}'
echo P_FITSBIN | ${P_GAWK} '{print $1"=${BIN}/fitsbin"}'
echo P_FITSBLOOMDETECT | ${P_GAWK} '{print $1"=${BIN}/fitsbloomdetect"}'
echo P_FITSFILL | ${P_GAWK} '{print $1"=${BIN}/fitsfill"}'
echo P_FITSGRAD | ${P_GAWK} '{print $1"=${BIN}/fitsgrad"}'
echo P_FITSDEMOSAICBAYER | ${P_GAWK} '{print $1"=${BIN}/fitsdemosaicbayer"}'
echo P_FITS3MAX | ${P_GAWK} '{print $1"=${BIN}/fits3max"}'
echo P_FITSGAUSS | ${P_GAWK} '{print $1"=${BIN}/fitsgauss"}'
echo P_FITS2TIFF | ${P_GAWK} '{print $1"=${BIN}/fits2tiff"}'
echo P_TIFF2FITS | ${P_GAWK} '{print $1"=${BIN}/tiff2fits"}'
echo P_CORRLIRIS | ${P_GAWK} '{print $1"=${BIN}/corrliris"}'
echo P_CROSSTALK | ${P_GAWK} '{print $1"=${BIN}/crosstalk"}'
echo P_FINDGSC | ${P_GAWK} '{print $1"=${BIN}/findgsc"}'
echo P_FINDUSNOB1 | ${P_GAWK} '{print $1"=${BIN}/findusnob1"}'
echo P_FIND2MASS | ${P_GAWK} '{print $1"=${BIN}/find2mass"}'
echo P_FINDSDSS7 | ${P_GAWK} '{print $1"=${BIN}/findsdss7"}'
echo P_FINDUCAC3 | ${P_GAWK} '{print $1"=${BIN}/finducac3"}'
echo P_FINDNOMAD1 | ${P_GAWK} '{print $1"=${BIN}/findnomad1"}'
echo P_VIZQUERY | ${P_GAWK} '{print $1"=${BIN}/vizquery"}'
echo P_SESAME | ${P_GAWK} '{print $1"=${BIN}/sesame"}'
echo P_ACLIENT | ${P_GAWK} '{print $1"=${BIN}/aclient"}'
echo P_SCAMP | ${P_GAWK} '{print $1"=${BIN}/scamp"}'
echo P_RENAME | ${P_GAWK} '{print $1"=${BIN}/rename"}'
echo P_MISSFITS | ${P_GAWK} '{print $1"=${BIN}/missfits"}'
echo P_SWARPFILTER | ${P_GAWK} '{print $1"=${BIN}/swarpfilter"}'
echo P_FITSBLOCKEDIT | ${P_GAWK} '{print $1"=${BIN}/fitsblockedit"}'
echo P_FITSMASK | ${P_GAWK} '{print $1"=${BIN}/fitsmask"}'
echo P_FITSMEDIAN | ${P_GAWK} '{print $1"=${BIN}/fitsmedian"}'
echo P_FITSNANMASK | ${P_GAWK} '{print $1"=${BIN}/fitsnanmask"}'
echo P_FITSSTAT | ${P_GAWK} '{print $1"=${BIN}/fitsstat"}'
echo P_FITSSPLITBAYER | ${P_GAWK} '{print $1"=${BIN}/fitssplitbayer"}'
echo P_FITSGUESSGEOM | ${P_GAWK} '{print $1"=${BIN}/fitsguessgeom"}'
echo P_SPLITSUPRIMECAM | ${P_GAWK} '{print $1"=${BIN}/splitsuprimecam"}'
echo P_PASTESWOPE | ${P_GAWK} '{print $1"=${BIN}/paste_swope"}'
echo P_PASTELASCUMBRES | ${P_GAWK} '{print $1"=${BIN}/paste_lascumbres"}'
echo P_PASTEDUALCHANNEL | ${P_GAWK} '{print $1"=${BIN}/paste_dualchannel"}'
echo P_PASTEQUADCHANNEL | ${P_GAWK} '{print $1"=${BIN}/paste_quadchannel"}'
echo P_PASTESAMI | ${P_GAWK} '{print $1"=${BIN}/paste_sami"}'
echo P_SPLITGMOSMULTIPORT | ${P_GAWK} '{print $1"=${BIN}/split_gmos_multiport"}'
echo P_SPLITDECAM | ${P_GAWK} '{print $1"=${BIN}/split_decam"}'
echo P_SPLITGROND | ${P_GAWK} '{print $1"=${BIN}/split_grond"}'
echo P_SPLITPAUCAM | ${P_GAWK} '{print $1"=${BIN}/split_paucam"}'
echo P_GETSHIFT | ${P_GAWK} '{print $1"=${BIN}/get_shift"}'
echo P_FITSNONLINEARITY | ${P_GAWK} '{print $1"=${BIN}/fitsnonlinearity"}'
echo P_FITSPIC | ${P_GAWK} '{print $1"=${BIN}/fitspic"}'
echo P_FITSPOLYGON | ${P_GAWK} '{print $1"=${BIN}/fitspolygon"}'
echo P_EXPANDSEXMASK | ${P_GAWK} '{print $1"=${BIN}/expand_sexmask"}'
echo P_DCRAW | ${P_GAWK} '{print $1"=${BIN}/dcraw"}'
echo P_DECSEXCONV | ${P_GAWK} '{print $1"=${BIN}/decsexconv"}'
echo P_STIFF | ${P_GAWK} '{print $1"=${BIN}/stiff"}'
echo P_SUBSKY | ${P_GAWK} '{print $1"=${BIN}/subsky"}'
echo P_GIFSICLE | ${P_GAWK} '{print $1"=${BIN}/gifsicle"}'
echo P_XY2SKY | ${P_GAWK} '{print $1"=${BIN}/xy2sky"}'
echo P_SKY2XY | ${P_GAWK} '{print $1"=${BIN}/sky2xy"}'
echo P_ISFITS | ${P_GAWK} '{print $1"=${BIN}/isfits"}'
echo P_GETKEY | ${P_GAWK} '{print $1"=${BIN}/getkey"}'
echo P_SKY2XY_HELPER | ${P_GAWK} '{print $1"=${BIN}/sky2xy_helper"}'
echo P_GET_ROTIMSIZE | ${P_GAWK} '{print $1"=${BIN}/get_rotimsize"}'
echo P_CLEANSTRING | ${P_GAWK} '{print $1"=${BIN}/cleanstring"}'
echo P_NUMCPU | ${P_GAWK} '{print $1"=${BIN}/numcpu"}'
echo P_GETSTATS | ${P_GAWK} '{print $1"=${BIN}/getstats"}'
echo P_CDELT2CD | ${P_GAWK} '{print $1"=${BIN}/cdelt2cd"}'
echo P_GETCDMATRIX | ${P_GAWK} '{print $1"=${BIN}/get_cdmatrix"}'
echo P_GETPIXSCALE | ${P_GAWK} '{print $1"=${BIN}/get_pixscale"}'
echo P_GETPOSANGLE | ${P_GAWK} '{print $1"=${BIN}/get_posangle"}'
echo P_GETREFCATRADIUS | ${P_GAWK} '{print $1"=${BIN}/get_refcat_radius"}'
echo P_MERGEDAT | ${P_GAWK} '{print $1"=${BIN}/mergedat"}'
echo P_ROTATECDMATRIX | ${P_GAWK} '{print $1"=${BIN}/rotate_cdmatrix"}'
echo P_BACKGROUNDDYNAMIC | ${P_GAWK} '{print $1"=${BIN}/background_dynamic"}'
echo P_BACKGROUNDSTATIC | ${P_GAWK} '{print $1"=${BIN}/background_static"}'
echo P_MJD | ${P_GAWK} '{print $1"=${BIN}/mjd"}'
echo P_LST | ${P_GAWK} '{print $1"=${BIN}/lst"}'
echo P_IMALYZER | ${P_GAWK} '{print $1"=${BIN}/imalyzer"}'
echo P_E2ELL | ${P_GAWK} '{print $1"=${BIN}/e2ell"}'
echo P_FITSSMOOTHEDGE | ${P_GAWK} '{print $1"=${BIN}/fitssmoothedge"}'
echo P_FITSEXTRACTEXT | ${P_GAWK} '{print $1"=${BIN}/fitsextractext"}'
echo P_ERRTEST | ${P_GAWK} '{print $1"=${BIN}/errtest"}'
echo P_BUILDINDEX | ${P_GAWK} '{print $1"=${BIN_ANET}/build-astrometry-index"}'
echo P_SOLVEFIELD | ${P_GAWK} '{print $1"=${BIN_ANET}/solve-field"}'
echo P_XCORR | ${P_GAWK} '{print $1"=${BIN}/xcorr"}'
echo P_ZPABS | ${P_GAWK} '{print $1"=${BIN}/zpabs"}'
echo "#"
echo "# load the parameter files"
echo "#"
echo . "~"/.theli/param_set1.ini
echo . "~"/.theli/param_set2.ini
echo . "~"/.theli/param_set3.ini

} >> progs.ini

\rm progsini_tmp

####################################################
# update the scripts with the bash executable
####################################################

BASH=`which bash | ${P_GAWK} 'BEGIN {FS="/"; i=1} 
     {while (i<=NF) {f[i]=$i; i++}} 
     END {i=2; final=""; 
          while (i<=NF) {final=final"\\\/"f[i]; i++}; print final}'`

ls *.sh > scriptlist_$$
cat scriptlist_$$ |\
{
  while read file
  do
    sed 's/BASHPATH/#!'"${BASH}"'/g' ${file} > ${file}_tmp
    mv ${file}_tmp ${file}
    chmod +x ${file}
  done
}

chmod +x *.py

\rm scriptlist_$$

####################################################
# update the installation path
####################################################


${P_GAWK} '{if ($0 ~ /QString MAINGUIPATH=/) {
          print "QString MAINGUIPATH=\"'"${thelipath}"'/\";"}
      else print}' ${guipath}/globalvariables.h >\
     ${guipath}/globalvariables.h_$$
mv ${guipath}/globalvariables.h_$$ \
   ${guipath}/globalvariables.h
${P_GAWK} '{if ($0 ~ /QString bindir=/) {
          print "QString bindir=\"'"${bindir}"'/\";"}
      else print}' ${guipath}/globalvariables.h >\
     ${guipath}/globalvariables.h_$$
mv ${guipath}/globalvariables.h_$$ \
   ${guipath}/globalvariables.h

cd ${packagepath}

test -d ${packagepath}/lib && rm -rf ${packagepath}/lib
test -d ${packagepath}/include && rm -rf ${packagepath}/include

mkdir lib include

####################################################
# install the various packages
####################################################

echo " "
echo "####################################################"
echo "# Installing the CDS client"
echo "####################################################"
echo " "

sleep ${delay}

VERSION=3.80
tar xfz cdsclient-${VERSION}.tar.gz
cd cdsclient-${VERSION}
mkdir -p tmp tmp/bin tmp/man
./configure -prefix=${packagepath}/cdsclient-${VERSION}/tmp/
make -j $ncpu
make install

cd  tmp/bin/
# replace /bin/sh with /bin/bash
ls -ltr | ${P_GAWK} '($1~/-x/ && $1 !~ /d/) {print $9}' > scriptlist_$$
cat scriptlist_$$ |\
{
  while read file
  do
    sed 's/#!\/bin\/sh/#!'"${BASH}"'/g' ${file} > ${file}_tmp
    mv ${file}_tmp ${file}
    chmod +x ${file}
  done
}
\rm scriptlist_$$
cd ../../

cp -f tmp/bin/* ${bindir}
mv tmp/man .
\rm -rf tmp
make clean
cd ${packagepath}
rm -rf cdsclient-${VERSION}

echo " "
echo "####################################################"
echo "# Installing the fitstools"
echo "####################################################"
echo " "

sleep ${delay}

VERSION=1.3.6

tar xfz fitstools-${VERSION}.tgz

cd fitstools-${VERSION}

make clean
make  -j $ncpu 2> fitstools.log
# abort if the fitstools fail!
check=`grep "rror" fitstools.log`
if [ ! "${check}"_A = "_A" ]; then
    cat fitstools.log
    echo " "
    echo "*************************************************"
    echo " "
    echo "ERROR while compiling fitstools." 
    echo "Check the output for missing libraries."
    echo " "
    echo "*************************************************"
    echo " "
    exit
fi

rm fitstools.log
mv bin/* ${bindir}
make clean
cd ..

cd ${packagepath}

sleep ${delay}

echo " "
echo "####################################################"
echo "# Installing the WCS tools"
echo "####################################################"
echo " "

sleep ${delay}

if [ "${DO_SCISOFT}" = "N" ]; then
    tar xfz wcstools-3.9.2.tar.gz
    cd wcstools-3.9.2
    make sky2xy
    make xy2sky
    make isfits
    mv bin/sky2xy bin/xy2sky bin/isfits ${bindir}
    cd ${packagepath}
    rm -rf wcstools-3.9.2
else
    ln -s /scisoft/bin/sky2xy  ${bindir}/sky2xy
    ln -s /scisoft/bin/xy2sky  ${bindir}/xy2sky
    ln -s /scisoft/bin/isfits  ${bindir}/isfits
fi


sleep ${delay}

echo " "
echo "####################################################"
echo "# Installing missfits"
echo "####################################################"
echo " "

sleep ${delay}

VERSION=2.8.0
tar xfz missfits-${VERSION}.tar.gz
cd missfits-${VERSION}
./configure --prefix=${packagepath}/missfits-${VERSION} --bindir=${bindir}
make -j $ncpu
make install
cd ${packagepath}
rm -rf missfits-${VERSION}

echo " "
echo "####################################################"
echo "# Installing stiff"
echo "####################################################"
echo " "

sleep ${delay}

VERSION=2.4.0
tar xfz stiff-${VERSION}.tar.gz
cd stiff-${VERSION}
./configure --prefix=${packagepath}/stiff-${VERSION} --bindir=${bindir}
make -j $ncpu
make install
cd ${packagepath}
rm -rf stiff-${VERSION}

echo " "
echo "####################################################"
echo "# Installing gifsicle"
echo "####################################################"
echo " "

VERSION=1.84
sleep ${delay}

tar xfz gifsicle-${VERSION}.tar.gz
cd gifsicle-${VERSION}
./configure --prefix=${packagepath}/gifsicle-${VERSION}
make
cp src/gifsicle ${bindir}
cd ${packagepath}
rm -rf gifsicle-${VERSION}

cd ${guipath}

####################################################"
# Some python settings"
####################################################"

if [ "${DO_SCISOFT}" = "N" ]; then
    # check the python version
    pyv=`which python`
    if [ "${pyv}_A" = "_A" ]; then
	echo " "
	echo "###################################################"
	echo "     COULD NOT FIND PYTHON ON YOUR MACHINE!"
	echo "     PLEASE INSTALL PYTHON V2.5 OR LATER" 
	echo "###################################################"
	echo " "
	exit
    else
	python --version >& pyv.test
	pyversion=`cat pyv.test`
	pv1=`${P_GAWK} '{print $2}' pyv.test | ${P_GAWK} 'BEGIN{FS="."} {print $1}'`
	pv2=`${P_GAWK} '{print $2}' pyv.test | ${P_GAWK} 'BEGIN{FS="."} {print $2}'`
        if [ ${pv1} -eq 3 ]; then
	    echo " "
	    echo "###################################################"
	    echo " THELI needs python v2.5 or later, but not v3"
	    echo "###################################################"
	    exit
	else
            if [ ${pv2} -le 4 ]; then
		echo " "
		echo "###################################################"
		echo " THELI needs python v2.5 or later, but not v3."
		echo "You are running ${pyversion}"
		echo "###################################################"
		exit
	    fi
	fi
	rm pyv.test
    fi

#    cd ${packagepath}

#    cd ${guiscriptpath}
    
#    if [ "${PYTHONPATH}_A" = "_A" ]; then
#	echo export PYTHONPATH=${pythondir} >> progs.ini
#    fi
#    if [ "${PYTHONPATH}_A" != "_A" ]; then
#	echo export PYTHONPATH=${pythondir}/:\$\{PYTHONPATH\} >> progs.ini
#    fi

    cd ${guipath}
fi

echo " "
echo "####################################################"
echo "# Installing other useful stuff"
echo "####################################################"
echo " "

cd ${guipath}/stuff
echo "char bindir[1000]=\"${bindir}\";" > include/sky2xy_helper.h 
make
mv bin/* ${bindir}/
cd ${guipath}

echo " "
echo "####################################################"
echo "# Installing astrometry.net"
echo "####################################################"
echo " "

VERSION=0.67
cd ${guipath}/packages
tar xvfz astrometry.net-${VERSION}.tar.gz
mv astrometry.net-${VERSION} astrometry
cd astrometry
make -j $ncpu 
make install INSTALL_DIR=`pwd`/build/
make clean

cd 
homedir=`pwd`
cd ${guipath}/reduction
{
echo inparallel
echo depths 10 20 30 40 50 60 70 80 90 100
echo cpulimit 300
echo add_path ~/.theli/scripts/
echo index theli_mystd_anet.index
} > anet.backend.cfg

cd ${guipath}

#echo " "
#echo "####################################################"
#echo "# Installing the THELI GUI"
#echo "####################################################"
#echo " "

## compile the splash screen
#${CC} hex2lib.c -o hex2lib
#./hex2lib theli_splash.xpm > image.h

## compile the GUI
#\rm -rf Makefile makefile .obj .ui .moc
#${QMAKE} -o Makefile theli.pro
#make -j $ncpu


echo " "
echo " "
echo " "
echo "###################################################################"
echo "# "

echo "#         Installation finished."
echo "# "
if [ ! -f ${bindir}/scamp ]; then
echo "#   TODO: You still have to copy the 'scamp' executable to"
echo "#         ${bindir}"
echo "#    "
fi
counter=`printenv PATH | ${P_GAWK} '{n=split($0,a,":")} END {
    count=0
    for(i=1;i<=n;i++) {
    m=split(a[i],b,"")
    if (b[m]!="/") a[i]=a[i]"/"
        if (a[i]=="'${bindir}'") count=1
    }
    print count}'`
if [ "${counter}" = "0" ]; then
echo "#   TODO: You still have to include the directory"
echo "#         ${bindir}"
echo "#         in your PATH variable."
echo "# "
fi
echo "#   Your 'theli' executable is:"
echo "#   ${mainpath}/gui/theli"
echo "#   If you 'alias' it, you can launch THELI from anywhere."
echo "# "
echo "#   Please acknowledge the following two papers when"
echo "#   using THELI for your scientific work. Thank you!"
echo "# "
echo "#   Schirmer M. 2013, ApJS, 209, 21"
echo "#   Erben T. et al., 2005, AN, 326, 432 "
echo "# "
echo "#   Have fun :-)"
echo "# "
echo "# "
echo "###################################################################"
echo " "

