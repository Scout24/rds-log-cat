from __future__ import print_function, absolute_import, division

import unittest2 as unittest
from rds_log_cat.linereader import paginate


class LineReaderMySQL56Tests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.resource_file = 'src/unittest/resources/mysql56_logline.log'
        with open(self.resource_file) as f:
            self.oneline = f.read()
        self.oneline = self.oneline.splitlines()[0] + '\n'

    def test_paginate_with_one_line(self):
        with open(self.resource_file) as f:
            self.assertEqual(self.oneline, paginate(f).next())


if __name__ == '__main__':
    unittest.main()
