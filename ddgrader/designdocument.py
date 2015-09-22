from collections import OrderedDict
import logging
import os
import pickle
import re

from ddgrader.configger import Configger
from ddgrader.student import Student


__author__ = 'awknaust'

rank_order = OrderedDict([
    ('no show', 0),
    ('superficial', 1),
    ('unsatisfactory', 2),
    ('deficient', 3),
    ('marginal', 4),
    ('satisfactory', 5),
    ('very good', 6),
    ('excellent', 7)
])


class DesignDocument:
    slip_regex = re.compile(r"""slip[^:]*:\s*(?P<slip>\d+)\s*""", re.I)

    def __init__(self, path, student, group, slip):
        self.path = path
        self.slip = slip
        self.student = student
        self.group = group

    def all_students(self):
        return [self.student, ] + self.group

    @classmethod
    def find_slip_days(cls, path, doc_string):
        """Find the reported number of slip days used, as well as whether it was really found
        """
        slip_match = cls.slip_regex.search(doc_string)

        # check slip validity
        if slip_match and slip_match.group('slip'):
            return int(slip_match.group('slip')), True
        else:
            logging.info("'%s': Couldn't find slip days, defaulting to 0" % path)
            return 0, False


    # TODO option skip rankings if we are just parsing readmes
    @classmethod
    def from_design_doc(cls, path, doc_string):
        """Create a design document from the contents of a file given by doc_string"""

        group = []

        # this is pretty hacky
        processed = doc_string.replace('\r\n', '\n')
        processed = processed.replace('\r', '')
        assert not '\r' in processed

        students = Student.all_from_text(processed, path)
        for s in students:
            duplicate = False
            for other_s in group:
                if s.is_valid() and s.matches(other_s):
                    duplicate = True
                    logging.info("'%s': Duplicate student found in group" % path)
                    break

            if not duplicate:
                group.append(s)

        slip, found = cls.find_slip_days(path, processed)

        #check group size
        if len(group) == 0:
            # document must be fixed and rerun
            logging.critical("'%s': No students/bad design document" % path)

        elif len(group) < 2:
            # this usually indicates an error in parsing
            logging.error("'%s': Singleton group" % path)
            return cls(os.path.abspath(path), group[0], [], slip)

        elif len(group) >= 2:
            #check rankings
            for s in group[1:]:
                if not s.hasRanking() or s.ranking not in rank_order:
                    logging.warning("'%s': Bad/Missing Ranking (eid:%s, ranking:'%s')" % (path, s.eid, s.ranking))

            return cls(os.path.abspath(path), group[0], group[1:], slip)

        return None


def load_dds():
    """Unpickle the design_docs list"""
    if not os.path.exists(Configger().dds_pickle_name):
        logging.critical("Missing DD database. Have you run the mine command?")
        raise MissingDDSException()

    with open(Configger().dds_pickle_name, 'rb') as f:
        return pickle.load(f)


class MissingDDSException(Exception):
    pass


class DesignDocParseError(Exception):
    def __init__(self, message):
        super(Exception, self).__init__(message)



def store_dds(design_docs):
    """Pickle the design_docs list"""
    with open(Configger().dds_pickle_name, 'wb') as f:
        pickle.dump(design_docs, f)
        f.flush()










