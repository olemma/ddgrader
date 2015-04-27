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


class Configger(metaclass=Singleton):
    # singleton class for configuration information. Weird sort of global configuration object

    setup_items = {
        'report_thresh': 'marginal',
        'design_doc_name': 'design_doc.txt',
        'student_dir': 'students',
        'feedback_name': 'feedback.txt',
        'feedback_template': 'template.txt',
        'code_name': 'code',
        'dds_pickle_name': '.dds.pkl',
        'partner_pattern': 'group%d_doc.txt',
        'loglevel': 'warning',
        'logfile': ''
    }

    grade_items = {
        'editor': 'vim',
        'editor_args': '-p',
        'editor_rel_files': '',
        'grader_pickle_name': '.grader.pkl',
        'grade_regex': '',
        'grade_column': -1
    }

    sections = {'grade': grade_items, 'setup': setup_items}

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
        return defdict[name]


    def __getattr__(self, attr_name):
        section_name, defdict = self._lookup_sect_dict(attr_name)
        return self.config.get(section_name, attr_name, fallback=defdict[attr_name])


    def __setattr__(self, name, value):
        try:
            section_name, defdict = self._lookup_sect_dict(name)
            self.config.set(section_name, name, value)
        except KeyError:
            super().__setattr__(name, value)