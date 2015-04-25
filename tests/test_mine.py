import os

from nose.tools import *

from ddgrader.designdocument import DesignDocument
from ddgrader.commands.mine import read_design_doc, clean_empty_students, cross_reference
from ddgrader.student import Student


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

student_ex4 = """Name: Alex Knaust
EID1:
CS login:
Email:
Unique Number:
Ranking (scale below):
"""

slip_string1 = """
Slip days used:0
****EACH student submits a (unique) design document.****
"""

slip_string2 = """
Slip days used:
"""

slip_string3 = """
Slip days used:  3
"""


def test_student_eq():
    s1 = Student('alex', 'awk5', 'awknaust', 'awknaust@gmail.com', 5)
    s2 = Student('alex', 'awk5', 'awknaust', 'awknaust@gmail.com', 2)
    s3 = Student('alex', 'awk5', 'awknaust', 'awknaust@gmail.com', 5)
    s4 = Student('alex', 'awk8', 'awknaust', 'awknaust@gmail.com', 5)

    assert s1 == s1
    assert s1 == s3
    assert s2 != s3
    assert s2 != s4
    assert s3 != s4


def test_slip_days():
    """Test slip day regex"""
    eq_(DesignDocument.find_slip_days('fake', slip_string1), (0, True))
    eq_(DesignDocument.find_slip_days('fake', slip_string2), (0, False))
    eq_(DesignDocument.find_slip_days('fake', slip_string3), (3, True))


def test_student_update_other():
    s1 = Student('alex', None, 'awknaust', None, 5)
    s2 = Student('alex', 'awk5', None, 'awknaust@gmail.com', 5)
    s3 = Student('alex', 'awk5', 'awknaust', 'awknaust@gmail.com', 5)

    s4 = Student('None', None, None, None, None)
    s5 = Student('None', None, None, None, None)

    # test if overwrites info if they are notnone and different
    s6 = Student('alex', 'eid19', None, None, None)
    s7 = Student('alex', 'eid19', None, None, None)
    s8 = Student('alex', 'hello', None, None, None)

    s7.update_other(s8)
    eq_(s7, s6)

    s4.update_other(s5)
    eq_(s4.eid, None)

    s1.update_other(s2)
    eq_(s1, s3)



def test_student_matches():
    s1 = Student('alex', 'awk5', 'awknaust', 'awknaust@gmail.com', 7)
    s2 = Student('alex', 'awk5', 'awknaust', 'awknaust@gmail.com', 3)
    s3 = Student('jemma', 'jt7', 'jteller', 'jteller@gmail.com', 9)
    assert s1.matches(s2)
    assert s2.matches(s1)
    assert s1.matches(s1)
    assert not s3.matches(s1)
    assert not s1.matches(s3)


def test_student_one():
    s = Student.from_text(student_ex1)
    eq_(s.name, 'wellow yu')
    eq_(s.eid, 'wy51326')
    eq_(s.cslogin, 'pajamaa')
    eq_(s.email, 'google@google.com')
    eq_(s.num, '5345')
    eq_(s.ranking, 'satisfactory')


def test_student_two():
    s = Student.from_text(student_ex2)
    eq_(s.name, 'alex knaust')
    eq_(s.eid, 'awk333')
    eq_(s.cslogin, 'awknaust')
    eq_(s.email, 'zipzap@gmail.com')
    eq_(s.num, '342134')
    eq_(s.ranking, 'very good')


def test_student_empty_fields():
    s = Student.from_text(student_ex4)
    eq_(s.name, 'alex knaust')
    eq_(s.ranking, None)

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
    students = Student.all_from_text(student_ex3, 'test')

    eq_(len(students), 2)
    check_student_three_one(students[0])
    check_student_three_two(students[1])


def test_design_doc_read():
    txt = None
    for x in os.listdir(os.path.join('files', 'dds')):
        path = os.path.join('files', 'dds', x)
        assert read_design_doc(path) is not None


def check_slip_day(name, slip):
    path = os.path.join('files', 'dds', name)
    dd = DesignDocument.from_design_doc(path, read_design_doc(path))
    eq_(dd.slip, slip)

def test_slip_parsing():
    """Test slip day parsing on entire document"""
    name_slip_pairs = [
        ('cref1.txt', 1),
        ('cref2.txt', 0),
        ('project1_0.txt', 2),
        ('partial.txt', 0),
        ('space_first.txt', 2)
    ]
    for name, slip in name_slip_pairs:
        yield check_slip_day, name, slip

def test_double_student_dd():
    path = os.path.join('files', 'dds', 'double_self.txt')
    dd = DesignDocument.from_design_doc(path, read_design_doc(path))
    assert dd is not None
    eq_(len(dd.group), 1)
    eq_(dd.group[0].cslogin, 'frobo')


def test_space_first_dd():
    path = os.path.join('files', 'dds', 'space_first.txt')
    dd = DesignDocument.from_design_doc(path, read_design_doc(path))
    assert dd is not None
    eq_(len(dd.group), 3)


def test_project0_1():
    path = os.path.join('files', 'dds', 'project0_1.txt')
    dd = DesignDocument.from_design_doc(path, read_design_doc(path))
    assert dd is not None
    eq_(dd.student.cslogin, 'srio')
    assert dd.student.ranking is None

    eq_(len(dd.group), 1)
    eq_(dd.group[0].email, 'the_rock@yahoo.com')
    eq_(dd.group[0].ranking, 'satisfactory')


def test_project1_0():
    """Skip blank students"""
    path = os.path.join('files', 'dds', 'project1_0.txt')
    dd = DesignDocument.from_design_doc(path, read_design_doc(path))
    assert dd is not None
    eq_(len(dd.group), 3)
    assert dd.student.ranking is None


def test_project0_2():
    path = os.path.join('files', 'dds', 'project0_2.txt')
    dd = DesignDocument.from_design_doc(path, read_design_doc(path))
    assert dd is not None
    eq_(dd.student.cslogin, 'ckent')
    assert dd.student.ranking is None

    eq_(len(dd.group), 1)
    eq_(dd.group[0].email, 'the_boss@utexas.edu')
    eq_(dd.group[0].ranking, 'excellent')



def test_cross_reference():
    path = os.path.join('files', 'dds', 'double_self.txt')
    dd1 = DesignDocument.from_design_doc(path, read_design_doc(path))

    path2 = os.path.join('files', 'dds', 'partial.txt')
    dd2 = DesignDocument.from_design_doc(path, read_design_doc(path2))

    dds = [dd1, dd2]
    cross_reference(dds)
    eq_(dd2.group[0].eid, dd1.student.eid)
    eq_(len(dd2.group), 1)
    eq_(len(dd1.group), 1)


def test_cross_reference_again():
    path = os.path.join('files', 'dds', 'cref1.txt')
    dd1 = DesignDocument.from_design_doc(path, read_design_doc(path))

    path2 = os.path.join('files', 'dds', 'cref2.txt')
    dd2 = DesignDocument.from_design_doc(path, read_design_doc(path2))

    dds = [dd1, dd2]
    cross_reference(dds)

    eq_(len(dd2.group), 3)
    eq_(dd2.group[0].eid, dd1.student.eid)


def test_clean_empty_students():
    path = os.path.join('files', 'dds', 'project1_0.txt')
    dd = DesignDocument.from_design_doc(path, read_design_doc(path))
    assert dd is not None
    eq_(len(dd.group), 3)
    clean_empty_students([dd, ])
    eq_(len(dd.group), 2)

    for s in dd.group:
        assert s.name != 'none'
