from setuptools import setup
import ddgrader

setup(
    name="DDGrader",
    version=ddgrader.__version__,
    packages=['ddgrader', 'ddgrader.commands'],
    scripts=['bin/project_prepare', 'bin/ddgrader'],
    author="Alex Knaust",
    author_email="awknaust@gmail.com",
)