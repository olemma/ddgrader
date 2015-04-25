import logging
import os
from ddgrader.commands.command import Command
from ddgrader.designdocument import store_dds, DesignDocument

__author__ = 'awknaust'


class MineCommand(Command):
    """MineCommand creates the initial design document database"""
    cmd = 'mine'

    def do_cmd(self, parsed):
        docs = create_design_docs(parsed.unpacked)
        print("Created %d Design Document Objects" % len(docs))
        store_dds(docs)

    def add_parser(self, subparser):
        parser = subparser.add_parser(self.cmd, help='parses student design documents')
        parser.add_argument('unpacked', help='Directory of unpacked design documents')


def create_design_docs(src, subset=None):
    """Create a list of design docs from all files in a directory"""
    docs = []
    if subset is None:
        subset = sorted(os.listdir(src))

    for f in subset:
        path = os.path.join(src, f)
        name, ext = os.path.splitext(path)

        # TODO gather associated files (jpgs, see project 1)??
        # Either they left off the extension or it must be a txt file
        # accidentally reading jpgs can be bad
        if not ext or ext == '.txt':
            dd = DesignDocument.from_design_doc(path, read_design_doc(path))
            if dd is not None:
                docs.append(dd)

    cross_reference(docs)
    clean_empty_students(docs)
    return docs


def read_design_doc(path):
    """Read a design doc file into a string, wrapper to handle encoding problems"""
    # TODO maybe use chardet to get the encoding here instead
    try:
        with open(path, 'r', encoding="utf-8", errors="surrogateescape") as dd_file:
            logging.debug("Reading Design Doc %s..." % path)
            return dd_file.read()

    except Exception as e:
        logging.critical(e)
        logging.critical("cannot read path '%s'" % path)


def clean_empty_students(docs):
    """Remove invalid students from all groups in a list of docs"""
    for d in docs:
        ng = []
        for s in d.group:
            if not s.is_valid():
                logging.debug("Removing invalid student %s from %s" % (s, d.path))
            else:
                ng.append(s)
        if not ng:
            logging.critical("Removed all students from %s" % (d.path))
        d.group = ng


def cross_reference(docs):
    """Try to update all students with info from other groups
    O(n^2) at least
    """
    for i, doc in enumerate(docs):
        for odoc in docs[i + 1:]:
            for s in odoc.group:
                s.update_other(doc.student)
            if doc.student.matches(odoc.student):
                logging.error("Double design document detected '%s' and '%s'" % (doc.path, odoc.path))