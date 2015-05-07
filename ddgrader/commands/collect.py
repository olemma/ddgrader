import csv
import os
import re
import zipfile

from ddgrader.commands.command import Command
from ddgrader.configger import Configger
from ddgrader.designdocument import load_dds


__author__ = 'awknaust'


class CollectCommand(Command):
    cmd = 'collect'


    def fetch_grade(self, rex, path):
        with open(path, 'r') as f:
            for line in f:
                res = rex.search(line)
                if res:
                    return int(res.group('grade'))
        print("Couldnt get grade for %s... " % path)

    def update_grade(self, lines, eid, grade, column):
        for l in lines:
            if l[2].strip().lower() == eid:
                l[column] = str(grade)
                return
        print("Missing student %s in gradefile!" % eid)

    def collect_grades(self, grade_file, oput):
        raw_regex = Configger().grade_regex
        rex = re.compile(raw_regex, re.I)
        column = Configger().grade_column

        rows = []
        with open(grade_file, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = [l for l in reader]

        dds = load_dds()
        for dd in dds:
            path = os.path.join(Configger().student_dir, dd.student.getDirectoryName(),
                                Configger().feedback_template[0])
            g = self.fetch_grade(rex, path)
            self.update_grade(rows, dd.student.eid, g, column)

        with open(oput, 'w') as f:
            writer = csv.writer(f)
            writer.writerows(rows)


    def collect_files(self, fname):
        dds = load_dds()
        sub_file = zipfile.ZipFile(fname, mode='w')

        for dd in dds:
            path = os.path.join(Configger().student_dir, dd.student.getDirectoryName(),
                                Configger().feedback_template[0])
            sub_file.write(path, os.path.basename(dd.path))

        sub_file.close()

        print("Created %s to submit" % fname)

    def do_cmd(self, parsed):
        self.collect_files(parsed.zip)
        self.collect_grades(parsed.gradescsv, parsed.csv)

    def add_parser(self, subparser):
        parser = subparser.add_parser(self.cmd, help='generate grades and prepare submission to canvas')

        parser.add_argument('gradescsv', help='csv of grades exported from canvas')
        parser.add_argument('-z', '--zip', default='feedbacks.zip',
                            help='name of zipfile for feedbacks, defaults to <feedbacks.zip>')
        parser.add_argument('-c', '--csv', default='output.csv',
                            help='name of generated grade csv to import, defaults to <output.csv>')