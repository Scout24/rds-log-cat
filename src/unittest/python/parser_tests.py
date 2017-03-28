from __future__ import print_function, absolute_import, division

import unittest2 as unittest

from rds_log_cat.parser.parser import Parser


class ParserTests(unittest.TestCase):

    def test_load(self):
        # should pass w/o errors
        Parser.load('mysql')
        Parser.load('Mysql')

    def test_load_with_errors(self):
        with self.assertRaises(ImportError):
            Parser.load('foo')


if __name__ == '__main__':
    unittest.main()
