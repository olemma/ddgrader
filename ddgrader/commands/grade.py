import os
import pickle
import subprocess

from ddgrader.commands.command import Command
from ddgrader.configger import Configger


__author__ = 'awknaust'


class GradeCommand(Command):
    cmd = 'grade'

    def do_cmd(self, parsed):
        direc = Configger().student_dir
        if parsed.gradedb:
            Configger().grader_pickle_name = parsed.gradedb
        g = Grader(direc)

        if parsed.student is not None:
            g.grade(parsed.student.lower())
        else:
            g.loop()


    def add_parser(self, subparser):
        parser = subparser.add_parser(self.cmd, help='opens all files for grading design documents in a loop')
        parser.add_argument('-s', '--student', help='eid of a specific student to grade')
        parser.add_argument('--gradedb', help='path to pickled database of grader information')


class Grader:
    graded = list()


    def __init__(self, directory):
        self.directory = directory
        if os.path.exists(Configger().grader_pickle_name):
            with open(Configger().grader_pickle_name, 'rb') as f:
                self.graded = pickle.load(f)

    def next(self):
        folders = os.listdir(self.directory)
        ungraded = sorted(list(set(folders) - set(self.graded)))
        if len(ungraded) > 0:
            return ungraded[0]
        else:
            return None

    def done(self, eid):
        if not eid in self.graded:
            self.graded.append(eid)
            self.store()

    def undo(self, eid):
        if eid in self.graded:
            self.graded.remove(eid)
        self.store()

    def store(self):
        with open(Configger().grader_pickle_name, 'wb') as f:
            pickle.dump(self.graded, f)

    def grade(self, student):
        if os.path.exists(os.path.join(self.directory, student)):
            self.edit(student)
            x = input('Count as graded (y/n)?: ')
            if x.strip().lower() == 'y':
                self.done(student)
            else:
                self.undo(student)
        else:
            print("No such student?")

    def edit(self, student):
        """Build the editor command line and open the editor for a file"""
        path = os.path.join(self.directory, student)

        args = [Configger().editor, ]
        args += [x.strip() for x in Configger().editor_args.split(',')]
        args += [
            os.path.join(path, Configger().feedback_template[0]),
            os.path.join(path, Configger().design_doc_name),
        ]

        # hacky way to any symlinks to partners' design docs
        for i, f in enumerate(os.listdir(path)):
            group_dd = os.path.join(path, Configger().partner_pattern % i)
            if os.path.exists(group_dd):
                args.append(group_dd)

        args += [os.path.join(path, x) for x in Configger().editor_rel_files]
        args += Configger().editor_abs_files

        #do work son
        subprocess.call(args)


    def loop(self):
        student = self.next()
        print("Typing 'u' will not count the last opened student as graded")
        last = None
        count = 0
        while (student is not None):
            cmd = input("Grading %s (+%d), (u/x) 'x' to stop..." % (student, count))
            if cmd.strip().lower() == 'x':
                break
            elif cmd.strip().lower() == 'u':
                if not last:
                    print('No last student to undo')
                else:
                    self.undo(last)
                    student = last
            else:
                count += 1
                self.edit(student)
                self.done(student)
                last = student
                student = self.next()

        print("Finished grading (+%d %d/%d)" % (count, len(self.graded), len(os.listdir(self.directory))))


