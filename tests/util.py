import os
from nose.tools import ok_
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