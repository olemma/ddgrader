from nose.tools import *

from ddgrader.configger import Configger


def test_config_set():
    c = Configger()
    rt = c.report_thresh
    c.report_thresh = rt * 2

    eq_(c.report_thresh, rt * 2)


