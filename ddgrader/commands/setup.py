import logging
import os
import shutil

from ddgrader.commands.command import Command
from ddgrader.configger import Configger
from ddgrader.designdocument import load_dds


__author__ = 'awknaust'


class SetupCommand(Command):
    """Sets up the grading structure arguments should be
        setup <implementations>
    """
    cmd = 'setup'

    def do_cmd(self, parsed):
        docs = load_dds()
        dest_dir = Configger().student_dir
        impl_dir = parsed.impl_dir
        feedback_templ = Configger().feedback_template

        if not os.path.exists(dest_dir):
            os.mkdir(dest_dir)

        self.make_directories(dest_dir, docs)
        self.setup_grading(dest_dir, docs, impl_dir, feedback_templ)

    def add_parser(self, subparser):
        parser = subparser.add_parser(self.cmd,
                                      help='creates grading directory structure using parsed design doc information')
        parser.add_argument('impl_dir', help='directory of group code implementations made with project_prepare')


    @classmethod
    def setup_grading(cls, dest, design_docs, impl_dir, template):
        """Symlink each groups code into each students design document directory"""
        for doc in design_docs:
            student_folder = os.path.join(dest, doc.student.getDirectoryName())
            # link to group's code
            cls.link_code(student_folder,
                      [doc.student.eid],
                      impl_dir
                      )

            #link to student's design_doc
            cls.link_dd(student_folder, doc)

            #copy in the grading template
            cls.copy_template(student_folder, doc, template)

            #link group members design docs that come first
            cls.link_group(dest, student_folder, doc)


    @classmethod
    def copy_template(cls, dest, design_doc, template):
        """Copy the grading template into each student's directory"""
        target = os.path.join(dest, Configger().feedback_template[0])
        if not os.path.exists(target):
            shutil.copyfile(template, target)


    @classmethod
    def make_directories(cls, dest, design_docs):
        """Create a folder for each student by their eid in the destination directory"""
        for doc in design_docs:
            path = os.path.join(dest, doc.student.getDirectoryName())
            if not os.path.exists(path):
                os.mkdir(path)


    @classmethod
    def link_dd(cls, dest, dd):
        """Create a symlink to the student's design doc in their new folder
        """
        target = os.path.join(dest, Configger().design_doc_name)

        if not os.path.exists(target):
            os.symlink(dd.path, target)

    @classmethod
    def link_group(cls, root, dest, dd):
        """Symlink to each group members design document if theirs would have been graded first
        Assumes alphabetical grading
        """
        for i, member in enumerate(dd.group):
            if member.eid < dd.student.eid:
                target = os.path.join(dest, Configger().partner_pattern % (i))
                if os.path.lexists(target) or os.path.exists(target):  # remove broken links
                    os.unlink(target)
                os.symlink(os.path.abspath(os.path.join(root,
                                                        member.getDirectoryName(), Configger().feedback_template[0])),
                           target)

    @classmethod
    def link_code(cls, dest, eids, impl_dir):
        """Create a symlink to an implementation directory in dest matching
        some eid from eids
        """
        alldirs = os.listdir(impl_dir)

        cnt = 0
        goal = None
        for d in alldirs:
            if len((set([x.lower() for x in d.split('_')]) & set(eids))) >= 1:
                goal = d
                cnt = cnt + 1

        if cnt == 0:
            logging.error("missing implementation for '%s'" % dest)
        else:
            target = os.path.join(dest, Configger().code_name)
            if not os.path.lexists(target):
                os.symlink(os.path.abspath(os.path.join(impl_dir, goal)), target)