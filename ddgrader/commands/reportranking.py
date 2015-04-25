from collections import defaultdict, namedtuple
import logging

from ddgrader.commands.command import Command
from ddgrader.designdocument import load_dds, rank_order


__author__ = 'awknaust'


class ReportRankingCommand(Command):
    cmd = 'ranking'

    def poorly_ranked(self, s, thresh):
        """Return if they have a poor ranking"""
        return s.ranking in rank_order and rank_order[s.ranking] <= rank_order[thresh]

    def generate_report(self, docs, threshold, report_all=False):
        """Generate reports about who was ranked badly
        returns a dict of eid => RREntry(student, bad_rankers(list), pos_rankers(list)
        """

        bad_eid_reporters = defaultdict(list)
        other_eid_reporters = defaultdict(list)
        bad_eid_student = dict()

        # get all bad students
        for dd in docs:
            if not dd.group:
                logging.warning("%s listed no group members" % dd.student)
            for s in dd.group:
                if self.poorly_ranked(s, threshold):
                    bad_eid_student[s.eid] = s
                    bad_eid_reporters[s.eid].append((dd.student, s.ranking))

        # second pass to get all ratings for bad students
        if report_all:
            for dd in docs:
                for s in dd.group:
                    if s.eid in bad_eid_student and not self.poorly_ranked(s, threshold):
                        other_eid_reporters[s.eid].append((dd.student, s.ranking))

        res = {}
        RREntry = namedtuple('RREntry', ['student', 'bad_rankers', 'pos_rankers'])
        for eid in bad_eid_student:
            res[eid] = RREntry(bad_eid_student[eid], bad_eid_reporters[eid], other_eid_reporters[eid])

        return res


    def print_report(self, report):
        """Pretty print a report made by generate_report"""
        for eid in report:
            print("%s ranked poorly by %d student(s):" % (report[eid].student.short(), len(report[eid].bad_rankers)))

            for s, rank in report[eid].bad_rankers:
                print("\t%s\t==> %s" % (s.short(), rank.title()))

            if report[eid].pos_rankers:
                print("Other group members:")

                for s, rank in report[eid].pos_rankers:
                    print("\t%s\t==> %s" % (s.short(), rank.title()))

            print()

    def do_cmd(self, parsed):
        parsed.ranking = parsed.thresh.replace('_', ' ')
        dds = load_dds()
        report = self.generate_report(dds, parsed.thresh, parsed.all)
        self.print_report(report)

    def add_parser(self, subparser):
        parser = subparser.add_parser(self.cmd, help='report students who were ranked poorly')
        parser.add_argument('--thresh', default='marginal', help='the minimum ranking to count as poorly ranked',
                            choices=[s.replace(' ', '_') for s in rank_order.keys()])
        parser.add_argument('--all', action='store_true', help="also report every other group members ranking")
        # parser.add_argument('--missing', '-m', action="store_true", help="report students that have no ranking")