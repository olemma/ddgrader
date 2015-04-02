#!/usr/bin/python3
import argparse

import re, os, sys, shutil, pickle
import subprocess
import configparser
import zipfile
import csv

import logging

CONFIG_NAME = 'ddgrader.cfg'

rank_order = {
'no show': 0,
'superficial': 1,
'unsatisfactory': 2,
'deficient': 3,
'marginal': 4,
'satisfactory': 5,
'very good': 6,
'excellent': 7
}

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


#singleton class for configuration information. This is weird and stolen from stackoverflow
class Configger(metaclass=Singleton):
    def __init__(self, fname=None):
        if fname is None:
            fname = CONFIG_NAME
        self.config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        if (os.path.exists(fname)):
            self.config.read(fname)


    def report_thresh(self):
        return self.config.get('setup', 'report_thresh', fallback='unsatisfactory')

    def design_doc_name(self):
        return self.config.get('setup', 'design_doc_name', fallback='design_doc.txt')

    def student_dir(self):
        return self.config.get('setup', 'student_dir', fallback='students')

    def feedback_name(self):
        return self.config.get('setup', 'feedback_name', fallback='feedback.txt')

    def feedback_template(self):
        return self.config.get('setup', 'feedback_template', fallback='template.txt')

    def code_name(self):
        return self.config.get('setup', 'code_name', fallback='code')

    def dds_pickle_name(self):
        return self.config.get('setup', 'dds_pickle_name', fallback='dds.pkl')

    def partner_pattern(self):
        return self.config.get('setup', 'partner_pattern', fallback='group%d_doc.txt')

    def editor(self):
        return self.config.get('grader', 'editor', fallback='vim')

    def editor_args(self):
        return self.config.get('grader', 'editor_args', fallback='-p')

    def editor_rel_files(self):
        return self.config.get('grader', 'editor_rel_files', fallback='')

    def editor_abs_files(self):
        return self.config.get('grader', 'editor_abs_files', fallback='')

    def grader_pickle_name(self):
        return self.config.get('grader', 'grader_pickle_name', fallback='grader.pkl')

    def grade_regex(self):
        return self.config.get('grader', 'grade_regex', fallback='')

    def grade_column(self):
        return int(self.config.get('grader', 'grade_column', fallback=-1))



class DesignDocParseError(Exception):
    def __init__(self, message):
        super(Exception, self).__init__(message)


class Student:
    name_regex = re.compile(r'''name\d*[\t ]*:\s*(?P<name>.+)''', re.I)
    eid_regex = re.compile(r'''eid\d*[\t ]*:[\t ]*(?P<eid>\w+)''', re.I)
    cslogin_regex = re.compile(r'''cs[ \t]*login\d*[ \t]*:[ \t]*(?P<cslogin>\w+)''', re.I)
    email_regex = re.compile(r'''email\d*[ \t]*:[ \t]*(?P<email>.+)''', re.I | re.M)
    num_regex = re.compile(r'''unique[ \t]*number\d*[ \t]*:[ \t]*(?P<num>\d+)''', re.I)
    ranking_regex = re.compile(r'''^[\w\s\(\)']*(ranking|rating)['\(\)\w\s]*:\s*(?P<ranking>\w+[ \t]*\w+)''',
                               re.I | re.M)

    # important non-ranking attrs
    attr_list = ['name', 'eid', 'cslogin', 'email', 'num']

    def __init__(self, name, eid, cslogin, email, num, ranking=None):
        self.name = name
        self.eid = eid
        self.cslogin = cslogin
        self.email = email
        self.num = num
        self.ranking = ranking

    def hasRanking(self):
        return self.ranking is not None

    def getDirectoryName(self):
        return self.eid

    @staticmethod
    def from_text(text, pos=0, endpos=None):
        """Find the first student in a chunk of text"""

        if endpos is None:
            endpos = len(text)

        def empty_student(m):
            if m and m.group('name'):
                return (':' in m.group('name'))
            return False

        def get_attribute(attr_name):
            rex = getattr(Student, '%s_regex' % attr_name)
            match = rex.search(text, pos, endpos)
            if match and match.group(attr_name):
                return match.group(attr_name).strip().lower()
            else:
                logging.debug("Student Missing Attribute %s" % attr_name)
                return None

        if empty_student(Student.name_regex.search(text, pos, endpos)):
            return None

        name = get_attribute('name')
        eid = get_attribute('eid')
        cslogin = get_attribute('cslogin')
        email = get_attribute('email')
        num = get_attribute('num')
        ranking = get_attribute('ranking')

        return Student(name, eid, cslogin, email, num, ranking)


    @staticmethod
    def all_from_text(text, path):
        """Get a list of students from a design document
        :param path:
        """
        students = []


        # get all matches for student blocks that at least have a name
        matches = [m for m in Student.name_regex.finditer(text)]

        for i, m in enumerate(matches):
            endpos = matches[i + 1].start() if i < len(matches) - 1 else None
            s = Student.from_text(text, m.start(), endpos)

            if s is not None:
                students.append(s)
            elif s is not None and s.eid is None:
                logging.warning("'%s': Student '%s' without eid" % (path, s.name))
                students.append(s)
            elif s is None:
                logging.info("Skipping empty student")

        return students

    def is_valid(self):
        return self.eid is not None

    def matches(self, other):
        """Check if any of the student unique information matches another student's unique info"""
        return self.eid == other.eid or self.cslogin == other.cslogin or self.email == other.email

    def _common_attrs(self, other):
        """Return a list of attributes these two students have in common, other than ranking"""

        cattrs = []

        for attr_name in Student.attr_list:
            attr = getattr(self, attr_name)
            o_attr = getattr(other, attr_name)
            if attr is not None and attr == o_attr:
                cattrs.append(attr_name)

        return cattrs

    def update_other(self, other):
        """If we have any common attributes with another student,
        update the remaining ones for us
        """
        cattrs = self._common_attrs(other)
        if cattrs:
            for attr_name in Student.attr_list:
                attr = getattr(self, attr_name)
                o_attr = getattr(other, attr_name)

                if attr is None and o_attr is not None:
                    setattr(self, attr_name, o_attr)
                if attr is not None and o_attr is not None and attr != o_attr:
                    logging.debug("Partial match, but different info \nThis:\n%s\nOther:\n%s" % (str(self), str(other)))


    def __str__(self):
        return '(' + ', '.join(['%s:%s' % (a, getattr(self, a)) for a in Student.attr_list]) + ')'

    def __eq__(self, other):
        if not isinstance(other, Student):
            return NotImplemented
        for a_name in Student.attr_list:
            if getattr(self, a_name) != getattr(other, a_name):
                return False
        return True

    def __ne__(self, other):
        if not isinstance(other, Student):
            return NotImplemented
        return not self == other


class DesignDocument:
    slip_regex = re.compile(r"""slip[^:]*:\s*(?P<slip>\d+)\s*""", re.I)

    def __init__(self, path, student, group, slip):
        self.path = path
        self.slip = slip
        self.student = student
        self.group = group

    def all_students(self):
        return [self.student, ] + self.group

    @staticmethod
    def find_slip_days(path, doc_string):
        """Find the reported number of slip days used, as well as whether it was really found
        """
        slip_match = DesignDocument.slip_regex.search(doc_string)

        # check slip validity
        if slip_match and slip_match.group('slip'):
            return int(slip_match.group('slip')), True
        else:
            logging.info("'%s': Couldn't find slip days, defaulting to 0" % path)
            return 0, False


    @staticmethod
    def from_design_doc(path, doc_string):
        """Create a design document from the contents of a file given by doc_string"""

        group = []

        #this is pretty hacky
        processed = doc_string.replace('\r\n', '\n')
        processed = processed.replace('\r', '')
        assert not '\r' in processed

        students = Student.all_from_text(processed, path)
        for s in students:
            duplicate = False
            for other_s in group:
                if s.is_valid() and s.matches(other_s):
                    duplicate = True
                    logging.info("'%s': Duplicate student found in group" % path)
                    break

            if not duplicate:
                group.append(s)

        slip, found = DesignDocument.find_slip_days(path, processed)

        #check group size
        if len(group) == 0:
            # document must be fixed and rerun
            logging.critical("'%s': No students/bad design document" % path)

        elif len(group) < 2:
            # this usually indicates an error in parsing
            logging.error("'%s': Singleton group" % path)
            return DesignDocument(os.path.abspath(path), group[0], [], slip)

        elif len(group) >= 2:
            #check rankings
            for s in group[1:]:
                if not s.hasRanking() or s.ranking not in rank_order:
                    logging.warning("'%s': Bad/Missing Ranking (eid:%s, ranking:'%s')" % (path, s.eid, s.ranking))

                # TODO move to a report generator
                elif rank_order[s.ranking] <= rank_order[Configger().report_thresh()]:
                    logging.error("%s Ranked %s as %s" % (group[0].eid, s.eid, s.ranking))

            return DesignDocument(os.path.abspath(path), group[0], group[1:], slip)

        return None


def link_code(dest, eids, impl_dir):
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

    if cnt != 1:
        print("Error: student in multiple groups or missing implementation for '%s'" % dest)
    else:
        target = os.path.join(dest, Configger().code_name())
        if not os.path.lexists(target):
            os.symlink(os.path.abspath(os.path.join(impl_dir, goal)), target)


def link_group(root, dest, dd):
    """Symlink to each group members design document if theirs would have been graded first
    Assumes alphabetical grading
    """
    for i, member in enumerate(dd.group):
        if member.eid < dd.student.eid:
            target = os.path.join(dest, Configger().partner_pattern() % (i))
            if os.path.lexists(target) or os.path.exists(target):  #remove broken links
                os.unlink(target)
            os.symlink(os.path.abspath(os.path.join(root,
                member.getDirectoryName(), Configger().feedback_name())), target)


def link_dd(dest, dd):
    """Create a symlink to the student's design doc in their new folder
    """
    target = os.path.join(dest, Configger().design_doc_name())

    if not os.path.exists(target):
        os.symlink(dd.path, target)


def make_directories(dest, design_docs):
    """Create a folder for each student by their eid in the destination directory"""
    for doc in design_docs:
        path = os.path.join(dest, doc.student.getDirectoryName())
        if not os.path.exists(path):
            os.mkdir(path)


def copy_template(dest, design_doc, template):
    """Copy the grading template into each student's directory"""
    target = os.path.join(dest, Configger().feedback_name())
    if not os.path.exists(target):
        shutil.copyfile(template, target)


def setup_grading(dest, design_docs, impl_dir, template):
    """Symlink each groups code into each students design document directory"""
    for doc in design_docs:
        student_folder = os.path.join(dest, doc.student.getDirectoryName())
        #link to group's code
        link_code(student_folder,
                  [doc.student.eid],
                  impl_dir
                  )

        #link to student's design_doc
        link_dd(student_folder, doc)

        #copy in the grading template
        copy_template(student_folder, doc, template)

        #link group members design docs that come first
        link_group(dest, student_folder, doc)


def store_dds(design_docs):
    """Pickle the design_docs list"""
    with open(Configger().dds_pickle_name(), 'wb') as f:
        pickle.dump(design_docs, f)
        f.flush()


class MissingDDSException(Exception):
    pass


def load_dds():
    """Unpickle the design_docs list"""
    if not os.path.exists(Configger().dds_pickle_name()):
        raise MissingDDSException()

    with open(Configger().dds_pickle_name(), 'rb') as f:
        return pickle.load(f)


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


def read_design_doc(path):
    """Read a design doc file into a string, wrapper to handle encoding problems"""
    # TODO maybe use chardet to get the encoding here instead
    try:
        with open(path, 'r', encoding="utf-8", errors="surrogateescape") as dd_file:
            logging.debug("Reading Design Doc %s..." % path)
            return dd_file.read()

    except Exception as e:
        logging.error(e)
        logging.error("cannot read path '%s'" % path)


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


class InvalidCommandException(Exception):
    pass


class Command:
    def do_cmd(self, args):
        """args should be the name of the command, followed by any parameters"""
        raise NotImplementedError()

    def short_help(self):
        raise NotImplementedError()

    def usage(self):
        raise NotImplementedError()


class MineCommand(Command):
    """MineCommand creates the initial design document database"""
    cmd = 'mine'

    def do_cmd(self, args):
        if len(args) == 1:
            raise InvalidCommandException()
        else:
            docs = create_design_docs(args[1])
            print("Created %d Design Document Objects" % len(docs))
            store_dds(docs)

    def short_help(self):
        return "Create a DB of design documents from submissions"

    def usage(self):
        return "mine <unpacked_dir>"


class SetupCommand(Command):
    """Sets up the grading structure arguments should be
        setup <implementations>
    """
    cmd = 'setup'

    def do_cmd(self, args):
        if len(args) < 2:
            print(self.usage())
            raise InvalidCommandException()
        else:
            docs = load_dds()
            dest_dir = Configger().student_dir()
            impl_dir = args[1]
            feedback_templ = Configger().feedback_template()

            if not os.path.exists(dest_dir):
                os.mkdir(dest_dir)

            make_directories(dest_dir, docs)
            setup_grading(dest_dir, docs, impl_dir, feedback_templ)

    def short_help(self):
        return "Sets up directories for each student and links their dd, implentation, and template"

    def usage(self):
        return ("setup <impl_dir>")


class Grader:
    graded = list()


    def __init__(self, directory):
        self.directory = directory
        if os.path.exists(Configger().grader_pickle_name()):
            with open(Configger().grader_pickle_name(), 'rb') as f:
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
        with open(Configger().grader_pickle_name(), 'wb') as f:
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

        args = [Configger().editor()]
        args += [x.strip() for x in Configger().editor_args().split(',')]
        args += [
            os.path.join(path, Configger().feedback_name()),
            os.path.join(path, Configger().design_doc_name()),
        ]

        #hacky way to any symlinks to partners' design docs
        for i, f in enumerate(os.listdir(path)):
            group_dd = os.path.join(path, Configger().partner_pattern() % i)
            if os.path.exists(group_dd):
                args.append(group_dd)

        args += [os.path.join(path, x.strip()) for x in Configger().editor_rel_files().split(',')]
        args += [x.strip() for x in Configger().editor_abs_files().split(',')]

        #do work son
        subprocess.call(args)


    def loop(self):
        student = self.next()
        print("Typing 'u' will not count the last opened student as graded")
        last = None
        while (student is not None):
            cmd = input("Grading %s, (u/x) 'x' to stop..." % student)
            if cmd.strip().lower() == 'x':
                break
            elif cmd.strip().lower() == 'u':
                if not last:
                    print('No last student to undo')
                else:
                    self.undo(last)
                    student = last
            else:
                self.edit(student)
                self.done(student)
                last = student
                student = self.next()

        print("Finished grading (%d/%d)" % (len(self.graded), len(os.listdir(self.directory))))


class GradeCommand(Command):
    cmd = 'grade'

    def do_cmd(self, args):
        direc = Configger().student_dir()
        g = Grader(direc)

        if len(args) > 1:
            g.grade(args[1].lower())
        else:
            g.loop()

    def short_help(self):
        return "grade design documents in alphabetical order. Open the editor for each one"

    def usage(self):
        return ("grade")


class EditCommand(Command):
    cmd = 'edit'

    def do_cmd(self, args):
        pass


class CollectCommand(Command):
    cmd = 'collect'

    def __init__(self):
        pass

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
        raw_regex = Configger().grade_regex()
        rex = re.compile(raw_regex, re.I)
        column = Configger().grade_column()

        rows = []
        with open(grade_file, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = [l for l in reader]

        dds = load_dds()
        for dd in dds:
            path = os.path.join(Configger().student_dir(), dd.student.getDirectoryName(), Configger().feedback_name())
            g = self.fetch_grade(rex, path)
            self.update_grade(rows, dd.student.eid, g, column)

        with open(oput, 'w') as f:
            writer = csv.writer(f)
            writer.writerows(rows)


    def collect_files(self, fname):
        dds = load_dds()
        sub_file = zipfile.ZipFile(fname, mode='w')

        for dd in dds:
            path = os.path.join(Configger().student_dir(), dd.student.getDirectoryName(), Configger().feedback_name())
            sub_file.write(path, os.path.basename(dd.path))

        sub_file.close()

        print("Created %s to submit" % fname)

    def do_cmd(self, args):
        name = 'feedbacks.zip'
        grade_file = ''
        grade_out = 'output.csv'
        if len(args) > 1:
            grade_file = args[1]
        else:
            print(self.usage())
            return

        if len(args) > 2:
            grade_out = args[2]
        if len(args) > 3:
            name = args[3]

        self.collect_files(name)
        self.collect_grades(grade_file, grade_out)

    def short_help(self):
        return "collect feedback forms, rename them and zip them up"

    def usage(self):
        return "collect <grade.csv> [name]"


class HelpCommand(Command):
    cmd = 'help'

    def __init__(self, cmds=[]):
        self.cmds = cmds

    def do_cmd(self, args):
        if len(args) == 1:
            print("Usage: ddgrader <cmd> [args]")
            for cmd in self.cmds:
                print("%s:\t\t%s" % (cmd.cmd, cmd.short_help()))
        else:
            found = False
            for cmd in self.cmds:
                if args[1] == cmd.cmd:
                    print('%s\n%s' % (cmd.usage(), cmd.short_help()))
                    found = True
                    break
            if not found:
                print("No such command")

    def short_help(self):
        return "Prints a help message, pass command for specific help"

    def usage(self):
        return "help [cmd]"

# entry point
if __name__ == '__main__':
    cmds = [MineCommand(), SetupCommand(), GradeCommand(), CollectCommand()]

    hlp = HelpCommand(cmds)
    cmds.append(hlp)

    root_parser = argparse.ArgumentParser()
    # TODO this should be done with subparsers instead
    root_parser.add_argument('command', help="command to execute", choices=[c.cmd for c in cmds])
    root_parser.add_argument('-l', '--logfile', help="Path of file to log to, default to stdout")
    root_parser.add_argument('-L', '--loglevel', help="Logging level", default='warning',
                             choices=['info', 'warning', 'error', 'critical', 'debug'])
    root_parser.add_argument('args', nargs=argparse.REMAINDER)
    parsed = root_parser.parse_args()

    # setup logging
    numeric_level = getattr(logging, parsed.loglevel.upper(), None)
    if parsed.logfile is not None:
        logging.basicConfig(level=numeric_level)
    else:
        logging.basicConfig(level=numeric_level, filename=parsed.logfile)

    for c in cmds:
        if c.cmd == parsed.command:
            c.do_cmd([parsed.command, ] + parsed.args)

    logging.shutdown()

