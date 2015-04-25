from collections import namedtuple
from ddgrader.commands.command import Command
from ddgrader.designdocument import load_dds

__author__ = 'awknaust'


class ReportSlipCommand(Command):
    cmd = 'slip'

    def generate_report(self, docs, report_all=True):

        slips = []
        StudentSlip = namedtuple('StudentSlip', ['student', 'slip'])
        for dd in docs:
            if dd.slip > 0 or report_all:
                slips.append(StudentSlip(dd.student, dd.slip))

        return sorted(slips, key=lambda s: s.student.eid)


    def print_report(self, report):
        print("Slip days report (sorted by eid):")
        for s, days in report:
            print("%s\t==> %d" % (s.short(), days))

    def do_cmd(self, parsed):
        report = self.generate_report(load_dds(), parsed.all)
        self.print_report(report)

    def add_parser(self, subparser):
        parser = subparser.add_parser(self.cmd, help='report student-reported non-zero slip days for design documents')
        parser.add_argument('--all', action='store_true', help="Also report zero slip days")