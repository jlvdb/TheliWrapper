#!/usr/bin/env python3
import theli


THELI = theli.Reduction(
    "ACAM@WHT", "/home/janluca/THELI_TRAINING/ACAM",
    "SCIENCE", biasdir="BIAS", flatdir="FLAT",
    title="testrun", verbosity="normal")
# THELI.biasdir.restore()
# THELI.flatdir.restore()
THELI.sciencedir.restore()
# THELI.skydir.restore()
# THELI.stddir.restore()
THELI.split_FITS_correct_header()
THELI.process_biases()
# THELI.process_darks()
THELI.process_flats()
THELI.calibrate_data()
THELI.background_model_correction()
# THELI.collapse_correction()
# THELI.debloom_images()
# THELI.create_binned_preview()
THELI.create_global_weights()
THELI.create_weights()
THELI.get_reference_catalog()
THELI.create_source_cat()
THELI.astro_and_photometry()
THELI.sky_subtraction()
THELI.coaddition()
