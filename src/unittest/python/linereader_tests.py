from __future__ import print_function, absolute_import, division

import unittest2 as unittest
from rds_log_cat.linereader import paginate


class LineReaderTests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        with open('src/unittest/resources/elb_logline.log') as f:
            self.oneline = f.readline()

    def test_paginate_with_one_line(self):
        with open('src/unittest/resources/elb_logline.log') as f:
            self.assertEqual(self.oneline, paginate(f).next())

    def test_paginate_with_small_buffer(self):
        with open('src/unittest/resources/elb_logline.log') as f:
            self.assertEqual(self.oneline, paginate(f, 1).next())
            self.assertEqual('', paginate(f, 1).next())

    def test_paginate_with_large_buffer(self):
        with open('src/unittest/resources/elb_logline.log') as f:
            self.assertEqual(self.oneline, paginate(f, 16000).next())
            self.assertEqual('', paginate(f, 16000).next())

    def test_paginate_with_file_ending_with_newline(self):
        with open('src/unittest/resources/elb_logline.log') as f:
            paginate(f).next()  # skip first line
            self.assertEqual('', paginate(f).next())


if __name__ == '__main__':
    unittest.main()
