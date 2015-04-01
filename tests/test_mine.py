from nose.tools import *
from .. import ddgrader
import os


student_ex1 = """Name1: Wellow Yu
EID1: wy51326
CS login: pajamaa
Email: google@google.com
Unique Number: 5345

Your partner's ranking (scale below): Satisfactory
"""

student_ex2 = """Name: Alex Knaust
EID1:awk333
CS login: awknaust
Email: zipzap@gmail.com
Unique Number: 342134
Ranking (scale below): Very good
"""

student_ex3 = """################
YOUR INFO
################
Name1: Jeff White
EID1: jw351323
CS login: jwhite
Email: jwhite@community.org
Unique Number: 999

Slip days used: 0

****EACH student submits a (unique) design document.****

################
YOUR PARTNER'S INFO
################
Name1: Allie Brie
EID1: ab39421
CS login: abrieson
Email: brunette@hair.com
Unique Number: 17

Your partner's ranking (scale below): Excellent

###############

"""


def student_matches():
    s1 = ddgrader.Student('alex', 'awk5', 'awknaust', 'awknaust@gmail.com', 7)
    s2 = ddgrader.Student('alex', 'awk5', 'awknaust', 'awknaust@gmail.com', 3)
    s3 = ddgrader.Student('jemma', 'jt7', 'jteller', 'jteller@gmail.com', 9)
    assert s1.matches(s2)
    assert s2.matches(s1)
    assert s1.matches(s1)
    assert not s3.matches(s1)
    assert not s1.matches(s3)


def test_student_one():
    s = ddgrader.Student.from_sb_match(ddgrader.studentblock_regex.search(student_ex1))
    eq_(s.name, 'wellow yu')
    eq_(s.eid, 'wy51326')
    eq_(s.cslogin, 'pajamaa')
    eq_(s.email, 'google@google.com')
    eq_(s.num, '5345')
    eq_(s.ranking, 'satisfactory')


def test_student_two():
    s = ddgrader.Student.from_sb_match(ddgrader.studentblock_regex.search(student_ex2))
    eq_(s.name, 'alex knaust')
    eq_(s.eid, 'awk333')
    eq_(s.cslogin, 'awknaust')
    eq_(s.email, 'zipzap@gmail.com')
    eq_(s.num, '342134')
    eq_(s.ranking, 'very good')


def check_student_three_one(s):
    eq_(s.name, 'jeff white')
    eq_(s.eid, 'jw351323')
    eq_(s.cslogin, 'jwhite')
    eq_(s.email, 'jwhite@community.org')
    eq_(s.num, '999')
    eq_(s.ranking, None)


def check_student_three_two(s):
    eq_(s.name, 'allie brie')
    eq_(s.eid, 'ab39421')
    eq_(s.cslogin, 'abrieson')
    eq_(s.email, 'brunette@hair.com')
    eq_(s.num, '17')
    eq_(s.ranking, 'excellent')


def test_regex_multistudent():
    students = []

    for match in ddgrader.studentblock_regex.finditer(student_ex3):
        students.append(ddgrader.Student.from_sb_match(match))

    eq_(len(students), 2)
    check_student_three_one(students[0])
    check_student_three_two(students[1])


def test_design_doc_read():
    txt = None
    for x in os.listdir(os.path.join('files', 'dds')):
        path = os.path.join('files', 'dds', x)
        assert ddgrader.read_design_doc(path) is not None


def test_double_student_dd():
    path = os.path.join('files', 'dds', 'double_self.txt')
    dd = ddgrader.DesignDocument.from_design_doc(path, ddgrader.read_design_doc(path))
    assert dd is not None
    eq_(len(dd.group), 1)
    eq_(dd.group[0].cslogin, 'frobo')


def test_space_first_dd():
    path = os.path.join('files', 'dds', 'space_first.txt')
    dd = ddgrader.DesignDocument.from_design_doc(path, ddgrader.read_design_doc(path))
    assert dd is not None
    eq_(len(dd.group), 3)


@nottest
def test_three_group():
    path = os.path.join('files', 'dds', 'three_group.txt')
    dd = ddgrader.DesignDocument.from_design_doc(path, ddgrader.read_design_doc(path))
    assert dd is not None
    eq_(len(dd.group), 3)
