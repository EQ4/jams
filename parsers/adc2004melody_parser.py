#!/usr/bin/env python
"""
Translates the ADC2004 melody f0 annotations to a set of JAMS files.

The original data is found online at the following URL:
    http://www.iua.upf.es/mtg/ismir2004/contest/melodyContest/FullSet.zip

To parse the entire dataset, you simply need to provide the path to the
unarchived folder.

Example:
./adc2004melody_parser.py ~/FullSet -o ~/adc2004_jams/

"""

__author__ = "J. Salamon"
__copyright__ = "Copyright 2014, Music and Audio Research Lab (MARL)"
__license__ = "GPL"
__version__ = "1.0"
__email__ = "justin.salamon@nyu.edu"

import argparse
import json
import logging
import os
import sys
import time

sys.path.append("..")
import pyjams


def fill_file_metadata(jam, lab_file):
    """Fills the global metada into the JAMS jam."""
    jam.file_metadata.artist = ""
    jam.file_metadata.title = os.path.basename(lab_file).replace("REF.txt", "")


def fill_annotation_metadata(annot):
    """Fills the annotation metadata."""
    annot.annotation_metadata.corpus = "ADC2004"
    annot.annotation_metadata.version = "1.0"
    annot.annotation_metadata.annotation_tools = "SMSTools"
    annot.annotation_metadata.annotation_rules = ""
    annot.annotation_metadata.validation = "TODO"
    annot.annotation_metadata.data_source = ""
    annot.annotation_metadata.curator = pyjams.Curator(name="Emilia Gomez",
                                                       email="emilia.gomez"
                                                             "@upf.edu")
    annot.annotation_metadata.annotator = {}


def create_JAMS(lab_file, out_file):
    """
    Creates a JAMS file given the adc2004 annotation file (*.REF.txt).
    Note: the melody f0 annotations are provided in the *REF.txt files,
    not the .lab files (which contain quantized note annotations).
    """

    # New JAMS and annotation
    jam = pyjams.JAMS()

    # Global file metadata
    fill_file_metadata(jam, lab_file)

    # Create Melody annotation
    times, values = pyjams.util.read_lab(lab_file, 2)
    melody_annot = jam.melody.create_annotation()
    pyjams.util.fill_timeseries_annotation_data(times, values, None,
                                                melody_annot)
    fill_annotation_metadata(melody_annot)

    # Save JAMS
    with open(out_file, "w") as fp:
        json.dump(jam, fp, indent=2)


def process_folder(in_dir, out_dir):
    """Converts the original f0 annotations into the JAMS format, and saves
    them in the out_dir folder."""

    # Collect all melody f0 annotations.
    f0_files = list()
    f0_files += pyjams.util.find_with_extension(in_dir, '.txt', depth=1)

    for f0_file in f0_files:
        jams_file = os.path.join(out_dir,
                            os.path.basename(f0_file).replace('.txt', '.jams'))
        pyjams.util.smkdirs(os.path.split(jams_file)[0])
        # Create a JAMS file for this track
        create_JAMS(f0_file, jams_file)


def main():
    """Main function to convert the dataset into JAMS."""
    parser = argparse.ArgumentParser(
        description="Converts the ADC2004 dataset to the JAMS format",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("in_dir",
                        action="store",
                        help="ADC2004 main folder")
    parser.add_argument("-o",
                        action="store",
                        dest="out_dir",
                        default="adc2004_jams",
                        help="Output JAMS folder")
    args = parser.parse_args()
    start_time = time.time()

    # Setup the logger
    logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.INFO)

    # Run the parser
    process_folder(args.in_dir, args.out_dir)

    # Done!
    logging.info("Done! Took %.2f seconds.", time.time() - start_time)

if __name__ == '__main__':
    main()