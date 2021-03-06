from __future__ import print_function, absolute_import, division

import sys
import inspect


class Parser(object):
    """
    Parser to process logfiles
    """

    def __init__(self):
        """
        Create a new instance of the Parser class
        """
        pass

    @staticmethod
    def load(name):
        modulename = name.lower()
        fqmodulename = 'rds_log_cat.parser.%s' % modulename
        classname = modulename.capitalize()
        # Import the module
        __import__(fqmodulename, globals(), locals(), ['*'])
        # Get the class
        cls = getattr(sys.modules[fqmodulename], classname)
        # Check cls
        if not inspect.isclass(cls):
            raise TypeError("%s is not a class" % cls)
        # Return class
        return cls

    def parse(self, line, **args):
        """
        Parse line
        returns dict
        Should be overridden in subclass
        """
        raise NotImplementedError


class LineParserException(Exception):

    def __init__(self, msg=None):
        self.msg = msg

    def __str__(self):
        return self.msg
