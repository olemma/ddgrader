from setuptools import setup, find_packages

setup(
    name="DDGrader",
    version=2.0,
    packages=['ddgrader',],
    scripts=['bin/project_prepare'],
    author="Alex Knaust",
    author_email="awknaust@gmail.com",

    entry_points={
        'console_scripts' : [
            'ddgrader = ddgrader.main:begin'
        ]
    }
)