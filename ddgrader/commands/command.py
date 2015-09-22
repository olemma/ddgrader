__author__ = 'awknaust'


class Command:
    def do_cmd(self, args):
        """args should be the name of the command, followed by any parameters"""
        raise NotImplementedError()

    def add_parser(self, subparser):
        """Command builds an argparse subparser and adds it to subparser"""
        raise NotImplementedError()


class InvalidCommandException(Exception):
    pass