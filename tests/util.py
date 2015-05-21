import os

from nose.tools import ok_
from configger import Singleton, Configger

from ddgrader.commands.mine import MineCommand
from ddgrader.designdocument import DesignDocument


__author__ = 'awknaust'

DDS_DIR = os.path.join('tests', 'files', 'dds')

assert os.path.exists(DDS_DIR), "Not running nose from source root directory"

def dd_path(name):
    """Map a design doc name to a path"""
    return os.path.join(DDS_DIR, name)

def read_dd(name):
    """read a design document by name"""
    return MineCommand.read_design_doc(dd_path(name))

def get_dd(name):
    """Read and parse a design document by name"""
    dd = DesignDocument.from_design_doc(dd_path(name), read_dd(name))
    ok_(dd is not None)
    return dd


def cfg_path(name):
    """Get the path to the one test config"""
    return os.path.join('tests', 'files', 'config', name)


def mock_config(value_dict):
    """Create a config object and set values as specified by value_dict"""
    config = Configger()

    for key, val in value_dict:
        config.key = val


# TODO this singleton stuff is hardly testable
def reset_config():
    """Reset config by deleting all singleton instances"""
    Singleton._instances = {}