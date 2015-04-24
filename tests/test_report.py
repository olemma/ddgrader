from nose.tools import *
from .. import ddgrader
import os

def get_dd(name):
    path = os.path.join('files', 'dds', name)
    dd = ddgrader.DesignDocument.from_design_doc(path, ddgrader.read_design_doc(path))
    ok_(dd is not None)
    return dd

def test_ranking_generate_report_one():
    """Report poorly ranked students in one design document"""

    dds = [get_dd('bad_rank_one.txt'), ]
    rrc = ddgrader.ReportRankingCommand()
    report = rrc.generate_report(dds, 'marginal', False)

    eq_(len(report), 2)
    ok_('e35252' in report)
    eq_(len(report['e35252'].bad_rankers), 1)
    eq_(report['e35252'].bad_rankers[0][0].eid, 'cs23142')
    eq_(report['e35252'].bad_rankers[0][1], 'marginal')

    ok_('cs23142' not in report)

def test_ranking_generate_report_thresh():
    """Report poorly ranked students with a non-default threshold"""
    dds = [get_dd('bad_rank_one.txt'), ]
    rrc = ddgrader.ReportRankingCommand()
    report = rrc.generate_report(dds, 'no show', False)

    eq_(len(report), 1)
    ok_('ax634563' in report)
    eq_(len(report['ax634563'].bad_rankers), 1)
    eq_(report['ax634563'].bad_rankers[0][0].eid, 'cs23142')
    eq_(report['ax634563'].bad_rankers[0][1], 'no show')

def has_eid_rank(l, eid, rank):
    """Search for a student with given eid and ranking in a list of (student, ranking) pairs"""
    for s, r in l:
        if s.eid == eid and r == rank:
            return True
    return False

def test_ranking_generate_report_multi():
    """Report generation from multiple design documents"""
    dds = list(map(get_dd, ['bad_rank_one.txt', 'bad_rank_two.txt']))
    rrc = ddgrader.ReportRankingCommand()
    report = rrc.generate_report(dds, 'marginal', False)
    eq_(len(report), 3)
    ok_('e35252' in report)
    eq_(len(report['e35252'].bad_rankers), 2)
    ok_(has_eid_rank(report['e35252'].bad_rankers, 'cs23142', 'marginal'))
    ok_(has_eid_rank(report['e35252'].bad_rankers, 'ax634563', 'deficient'))

def test_ranking_generate_report_multi_all():
    """Report generation from multiple design documents showing all groupmembers"""
    dds = list(map(get_dd, ['bad_rank_one.txt', 'bad_rank_two.txt']))
    rrc = ddgrader.ReportRankingCommand()
    report = rrc.generate_report(dds, 'marginal', True)
    eq_(len(report), 3)
    ok_('e35252' in report)
    eq_(len(report['jb19'].bad_rankers), 1)
    eq_(len(report['jb19'].pos_rankers), 1)
    ok_(has_eid_rank(report['jb19'].pos_rankers, 'cs23142', 'satisfactory'))
    ok_(has_eid_rank(report['jb19'].bad_rankers, 'ax634563', 'marginal'))


def test_slip_generate_report_multi():
    """Report generation for slip days across multiple reports"""
    dds = list(map(get_dd, ['cref1.txt', 'cref2.txt']))
    rsc = ddgrader.ReportSlipCommand()
    report = rsc.generate_report(dds, False)
    eq_(len(report), 1)
    eq_(report[0].slip, 1)
    eq_(report[0].student.eid, 'tcrom')

def test_slip_generate_report_multi_all():
    """Report generation for slip days"""
    dds = list(map(get_dd, ['cref1.txt', 'cref2.txt']))
    rsc = ddgrader.ReportSlipCommand()
    report = rsc.generate_report(dds, True)
    eq_(len(report), 2)
    s1, s2 = report[0].slip, report[1].slip
    st1, st2 = report[0].student, report[1].student
    eq_(min(s1, s2), 0)
    eq_(max(s1,s2), 1)
    ok_(st1.eid != st2.eid)
    ok_(st1.eid in ['tcrom', 'jr19'])
    ok_(st2.eid in ['tcrom', 'jr19'])
