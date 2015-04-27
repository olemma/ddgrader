import os
from nose.tools import ok_
from tests.util import get_dd, DDS_DIR

__author__ = 'awknaust'


def test_get_dd():
    for x in os.listdir(DDS_DIR):
        ok_(get_dd(x) is not None)