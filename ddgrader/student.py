import logging
import re

__author__ = 'awknaust'


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

    def short(self):
        return 'name:%s, eid:%s' % (self.name.title(), self.eid)

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