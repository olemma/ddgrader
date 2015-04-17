#!/usr/bin/python3

'''
This script prepares a canvas submission zip for grading. To do this, it:
    1) Unzips the master zip (from canvas) into a directory argv[2]
    2) Untars each individual project tarball into it's own directory
    3) Renames that directory to <eid1>_<eid2> based off the README

Notes:
    1) tmp_* directories are ones that the script could not process because
       of some failure to follow submission guidelines. This can include:
        a) No README in the root of the submission
        b) README is not filled out
        c) Invalid tarball submitted
       check grading_log.txt for more information
    2) optimized so it works for Project 0 
    	a) copies in the mshref, sdriver.pl and all the trace files

Written by Robert with love <3

also supports additional README search paths via -r or --readme i.e.
./project_prepare submissions.zip implementations -r userprog/README -r userprog/README.userprog
    --Alex K 2015-03-31

Changed to use ddgrader parser instead + python3
    --Alex K 2015-04-11
'''

import os
from multiprocessing import Pool
import subprocess
import sys, traceback
import re

import argparse
import ddgrader


def makePrepare(tarball, readme_paths):
    # Create the tmp directory and untar
    tmpdir = "tmp_" + tarball
    os.makedirs(tmpdir)
    p = subprocess.Popen(["tar", "zxf", tarball, "-C", tmpdir])
    p.communicate()
    os.remove(tarball)

    # Create the log
    log = open(tmpdir + "/grading_log.txt", "a")
    log.write("Starting Grading\n")

    any_found = False
    real_readme = ''
    # Try all passed readme_paths, and use the first one found
    for readme_path in readme_paths:
        # Get the text from the README
        log.write("Reading %s\n" % readme_path)
        if os.path.isfile(os.path.join(tmpdir, readme_path)):
            real_readme = os.path.join(tmpdir, readme_path)
            any_found = True
            break
        else:
            # This README didn't exist
            log.write("Readme %s not found\n" % readme_path)

    if not any_found:
        log.write("No READMEs found\n")
        log.close()
        return None

    # Get the students from the README
    readme_txt = ddgrader.read_design_doc(real_readme)
    if not readme_txt:
        print("Failed to read README?")
        return None

    dd = ddgrader.DesignDocument.from_design_doc(real_readme, readme_txt)

    eids = sorted([s.eid for s in dd.all_students() if s.eid])

    # The README wasn't filled out
    if len(eids) == 0:
        log.write("Found no EIDs in README\n")
        log.close()
        return set()


    # Change the name of the directory to <eid1>_<eid2>
    newdir = "_".join(eids)
    try:
        os.rename(tmpdir, newdir)
    except:
        log.write("Folder " + newdir + " exists\n")

    # TODO this is done no matter what :(?
    p = subprocess.Popen(["cp", "-a", "/projects/cs439-norman/grading/Project0_files/.", newdir])
    p.communicate()

    log.close()

    return eids


def parse_args():
    parser = argparse.ArgumentParser(description="Unzip submissions tarfile and rename code directories to {eid_}*",
                                     epilog="Example: ./project_prepare submissions.zip implementations -r userprog/README -r userprog/README.userprog")
    parser.add_argument('zipfile', help="submissions.zip with student code from canvas")
    parser.add_argument('dest', help="destination directory to unpack to")
    parser.add_argument('-r', '--readme', help="relative paths to try as README, (README always tried first)",
                        action='append',
                        default=['README', ])
    return parser.parse_args()


# Driver method
def main():
    # Verify inputs
    parsed = parse_args()

    # Verify output directory doesn't exist
    if os.path.exists(parsed.dest):
        print("output directory already exists")
        sys.exit(1)

        # Create and setup output directory
    os.makedirs(parsed.dest)
    p = subprocess.Popen(["unzip", parsed.zipfile, "-d", parsed.dest])
    p.communicate()
    os.chdir(parsed.dest)

    # Begin the grading
    files = os.listdir(".")
    all_eids = set()
    cnt = 0
    for file in files:
        eids = makePrepare(file, parsed.readme)
        if eids:
            if set(eids) & all_eids:
                print("Student in multiple groups?")
            if len(set(eids)) == 1:
                print("Student in solo group %s" % str(eids))
            all_eids.update(eids)
        cnt += 1

    print("Successfully unpacked %d groups, found %d eids" % (cnt, len(all_eids)))


if __name__ == "__main__":
    main()
