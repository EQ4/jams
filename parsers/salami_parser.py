#!/usr/bin/env python
"""
This script parses the SALAMI v1.2 dataset into the JAMS format.

Usage:
    ./salami_parser.py SALAMIv1.2/ [-o SalamiJAMS/]
"""

__author__ = "Oriol Nieto"
__copyright__ = "Copyright 2014, Music and Audio Research Lab (MARL)"
__license__ = "GPL"
__version__ = "1.0"
__email__ = "oriol@nyu.edu"

import argparse
import csv
import json
import logging
import os
import sys
import time
import zipfile

sys.path.append("..")
import pyjams


def unzip(source_filename, dest_dir):
    """Unzips a zip file and puts it into the dest_dir. Copied from:
        http://stackoverflow.com/questions/12886768/
            simple-way-to-unzip-file-in-python-on-all-oses

    Parameters
    ----------
    source_filename : str
        Path to the zip file.
    dest_dir : str
        Output directory to save the contents of the zipped file.
    """
    with zipfile.ZipFile(source_filename) as zf:
        for member in zf.infolist():
            # Path traversal defense copied from
            # http://hg.python.org/cpython/file/tip/Lib/http/server.py#l789
            words = member.filename.split('/')
            path = dest_dir
            for word in words[:-1]:
                drive, word = os.path.splitdrive(word)
                head, word = os.path.split(word)
                if word in (os.curdir, os.pardir, ''):
                    continue
                path = os.path.join(path, word)
            zf.extract(member, path)


def parse_annotation_level(annot, path, annotation_id, level):
    """Parses one specific level of annotation and puts it into annot.

    Parameters
    ----------
    annot: Annotation
    path: str
        path to the track in the SALAMI dataset
    annotation_id: int
        Whether to use the first or the second annotation
    level: str
        Level of annotation
    """
    level_dict = {
        "function": "_functions",
        "large_scale": "_uppercase",
        "small_scale": "_lowercase"
    }

    # File to open
    file_path = os.path.join(path, "parsed", "data", os.path.basename(path),
                             "parsed", "textfile" + str(annotation_id + 1) +
                             level_dict[level] + ".txt")

    # Open file
    try:
        f = open(file_path, "r")
    except IOError:
        logging.warning("Annotation missing in %s", file_path)
        return

    # Parse file
    lines = f.readlines()
    for i, line in enumerate(lines[:-1]):
        start_time, label = line.strip("\n").split("\t")
        end_time = lines[i + 1].split("\t")[0]
        if float(start_time) - float(end_time) == 0:
            continue
        segment = annot.create_datapoint()
        segment.start.value = float(start_time)
        segment.start.confidence = 1.0
        segment.end.value = float(end_time)
        segment.end.confidence = 1.0
        segment.label.value = label
        segment.label.confidence = 1.0
        segment.label.secondary_value = level
        #print start_time, end_time, label
        #print segment

    f.close()


def fill_global_metadata(jam, metadata):
    """Fills the global metada into the JAMS jam."""
    if metadata[5] == "":
        metadata[5] = -1
    jam.file_metadata.artist = metadata[8]
    jam.file_metadata.duration = float(metadata[5])  # In seconds
    jam.file_metadata.title = metadata[7]

    # TODO: extra info
    #jam.file_metadata.genre = metadata[14]


def fill_annotation(path, annot, annotation_id, metadata):
    """Fills the JAMS annot annotation given a path to the original
    SALAMI annotations. The variable "annotator" let's you choose which
    SALAMI annotation to use.

    Parameters
    ----------

    annotation_id: int
        0 or 1 depending on which annotation to use

    """

    # Annotation Metadata
    annot.annotation_metadata.corpus = "SALAMI"
    annot.annotation_metadata.version = "1.2"
    annot.annotation_metadata.annotation_tools = "Sonic Visualizer"
    annot.annotation_metadata.annotation_rules = "TODO"  # TODO
    annot.annotation_metadata.data_source = metadata[1]
    annot.annotation_metadata.annotator.name = metadata[annotation_id + 2]
    annot.annotation_metadata.annotator.email = "TODO"  # TODO
    #TODO:
    #time = metadata[annotation_id + 15]

    # Parse all level annotations
    levels = ["function", "large_scale", "small_scale"]
    [parse_annotation_level(annot, path, annotation_id, level)
        for level in levels]


def create_JAMS(in_dir, metadata, out_file):
    """Creates a JAMS file given the path to a SALAMI track.

    Parameters
    ----------
    in_dir : str
        Path to the input directory
    metadata : str
        Metadata read from the CSV file
    out_file : str
        Output JAMS file
    """
    path = os.path.join(in_dir, "data", metadata[0], )

    # Sanity check
    if not os.path.exists(path):
        logging.warning("Path not found %s", path)
        return

    # New JAMS and annotation
    jam = pyjams.JAMS()

    # Global file metadata
    fill_global_metadata(jam, metadata)

    # Create Annotations if they exist
    # Maximum 3 annotations per file
    for possible_annot in xrange(3):
        if os.path.isfile(
            os.path.join(path, "data", metadata[0],
                         "textfile" + str(possible_annot + 1) + ".txt")):
            annot = jam.segment.create_annotation()
            fill_annotation(path, annot, possible_annot, metadata)

    # Save JAMS
    with open(out_file, "w") as f:
        json.dump(jam, f, indent=2)


def process(in_dir, out_dir):
    """Converts the original SALAMI files into the JAMS format, and saves
    them in the out_dir folder."""

    # Check if output folder and create it if needed:
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Check if the "data" folder exists. If not, unzip the data.zip.
    if not os.path.exists(os.path.join(in_dir, "data")):
        data_zip = os.path.join(in_dir, "data.zip")
        if not os.path.exists(data_zip):
            raise Exception("Data folder and data.zip not found! Make sure "
                            "you are trying to parse SALAMIv1.2")
        logging.info("Unzipping the data.zip file...")
        unzip(data_zip, in_dir)

    # Open CSV with metadata
    with open(os.path.join(in_dir, "metadata.csv")) as fh:
        csv_reader = csv.reader(fh)

        for metadata in csv_reader:
            # Create a JAMS file for this track
            create_JAMS(in_dir, metadata,
                        os.path.join(out_dir,
                            os.path.basename(metadata[0]) + ".jams"))


def main():
    """Main function to convert the dataset into JAMS."""
    parser = argparse.ArgumentParser(description=
        "Converts the SALAMI dataset to the JAMS format",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("in_dir",
                        action="store",
                        help="SALAMI main folder")
    parser.add_argument("-o",
                        action="store",
                        dest="out_dir",
                        default="SalamiJAMS",
                        help="Output JAMS folder")
    args = parser.parse_args()
    start_time = time.time()

    # Setup the logger
    logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.INFO)

    # Run the parser
    process(args.in_dir, args.out_dir)

    # Done!
    logging.info("Done! Took %.2f seconds." % (time.time() - start_time))

if __name__ == '__main__':
    main()
