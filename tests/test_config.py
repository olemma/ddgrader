from nose.tools import *

from ddgrader.configger import Configger, Singleton
from tests.util import cfg_path



# TODO this singleton stuff is hardly testable
def clear_singleton():
    Singleton._instances = {}


@with_setup(clear_singleton)
def test_config_set():
    c = Configger()
    rt = c.report_thresh
    c.report_thresh = rt * 2

    eq_(c.report_thresh, rt * 2)


@with_setup(clear_singleton)
def test_config_get():
    c = Configger(cfg_path('test1.cfg'))

    eq_(c.feedback_template, ['feedback.txt', 'cats.txt'])
    eq_(c.editor_abs_files, [])
    eq_(c.editor_rel_files, ['code/msh.c', ])
