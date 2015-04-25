from ddgrader.commands.command import Command
from ddgrader.commands.reportranking import ReportRankingCommand
from ddgrader.commands.reportslip import ReportSlipCommand

__author__ = 'awknaust'


class ReportCommand(Command):
    cmd = 'report'
    subcmds = [ReportRankingCommand(), ReportSlipCommand()]

    def do_cmd(self, parsed):
        for sc in self.subcmds:
            if parsed.report_subparser_name == sc.cmd:
                sc.do_cmd(parsed)
                return

    def add_parser(self, subparser):
        parser = subparser.add_parser(self.cmd, help='generates a report ')
        report_subparsers = parser.add_subparsers(dest='report_subparser_name', help='report types')
        report_subparsers.required = True

        for sc in self.subcmds:
            sc.add_parser(report_subparsers)