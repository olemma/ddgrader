from nose.tools import *
from .. import ddgrader


def test_config_set():
    c = ddgrader.Configger()
    rt = c.report_thresh
    c.report_thresh = rt * 2

    eq_(c.report_thresh, rt * 2)

