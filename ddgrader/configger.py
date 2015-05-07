import configparser
import logging
import os

__author__ = 'awknaust'


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


"""Config key class"""


class CKey:
    def __init__(self, default, typ):
        self.default = default
        self.typ = typ

    def _extract_list(self, val):
        """Convert a comma separated list into a list of strings"""
        print("list extraction", val)
        if val.strip():
            return list(p.strip() for p in val.split(','))
        return []

    def _extract_int(self, val):
        return int(val)

    def extract(self, val):
        """Extract a value into the appropriate type"""

        if self.typ == 'str':
            return val
        elif self.typ == 'int':
            return self._extract_int(val)
        elif self.typ == 'list':
            return self._extract_list(val)

class Configger(metaclass=Singleton):
    # singleton class for configuration information. Weird sort of global configuration object

    setup_items = {
        'report_thresh': CKey('marginal', 'str'),
        'design_doc_name': CKey('design_doc.txt', 'str'),
        'student_dir': CKey('students', 'str'),
        'feedback_template': CKey('feedback.txt', 'list'),
        'code_name': CKey('code', 'str'),
        'dds_pickle_name': CKey('.dds.pkl', 'str'),
        'partner_pattern': CKey('group%d_doc.txt', 'str'),
        'loglevel': CKey('warning', 'str'),
        'logfile': CKey('', 'str')
    }

    grade_items = {
        'editor': CKey('vim', 'str'),
        'editor_args': CKey('-p', 'str'),
        'editor_rel_files': CKey('', 'list'),
        'editor_abs_files': CKey('', 'list'),
        'grader_pickle_name': CKey('.grader.pkl', 'str'),
        'grade_regex': CKey('', 'str'),
        'grade_column': CKey(-1, 'int')
    }

    sections = {'grader': grade_items, 'setup': setup_items}

    def __init__(self, fname=None):
        self.fname = fname

        self.config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())

        # necessary if we want to set any values
        for section_name in self.sections:
            self.config.add_section(section_name)

        if fname:
            self.reload(self.fname)


    def reload(self, fname=None):
        """Reload the config from file (overwrites any in-memory changes to config)"""
        self.fname = fname
        if os.path.exists(fname):
            self.config.read(fname)
        else:
            logging.error("Failed to read config file : using defaults")

    @classmethod
    def _lookup_sect_dict(cls, name):
        """Return the section name, default dict that name is in"""
        for section_name, keydefdict in cls.sections.items():
            if name in keydefdict:
                return section_name, keydefdict
        raise KeyError


    @classmethod
    def get_default(cls, name):
        """Get the default value for a name, mainly for argparsers"""
        section_name, defdict = cls._lookup_sect_dict(name)
        return defdict[name].default


    def __getattr__(self, attr_name):
        section_name, defdict = self._lookup_sect_dict(attr_name)
        ckey = defdict[attr_name]
        return ckey.extract(self.config.get(section_name, attr_name, fallback=ckey.default))


    def __setattr__(self, name, value):
        try:
            section_name, defdict = self._lookup_sect_dict(name)
            self.config.set(section_name, name, value)
        except KeyError:
            super().__setattr__(name, value)