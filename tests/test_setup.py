from collections import namedtuple
import os
import shutil

__author__ = 'awknaust'

from nose.tools import *

import tempfile

from tests.util import reset_config, mock_config

def make_files(root, l):
    """create a list of files under root including any parent directories,
    cannot create empty directories"""
    for f in l:
        path = os.path.join(root, f)
        os.makedirs(os.path.dirname(f))
        with open(path, 'w') as filename:
            pass

class TestSetup(unittest.TestCase):

    def setUp(self):
        self.testdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.testdir)


    def test_link_group(self):
        make_files(self.testdir, [
            'link_fromA/dd.txt',
            'link_fromA/feedbackA.txt',
            'link_fromA/feedbackB.txt',
            'link_fromB/dd.txt'
            'link_fromB/feedbackA.txt',
            'link_fromB/feedbackB.txt'
            'link_into/tmp'
        ])


