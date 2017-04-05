from __future__ import print_function, absolute_import, division

import unittest2 as unittest
import json

from rds_log_cat.parser.mysql57 import Mysql57
# from rds_log_cat.parser.parser import LineParserException
import rds_log_cat.linereader as linereader


class MySQLTests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.parser = Mysql57()

    def test_parse_timestamp_valid(self):
        (datetime) = '2017-04-30T03:01:53.766220Z'
        tz = 'UTC'
        self.assertEqual("2017-04-30T03:01:53.766220Z",
                         self.parser.compose_timestamp(datetime, tz))

    def test_parse_test_log(self):
        def debug_print():
            def p(desc, data):
                print('%-10s #%d: %s' % (desc, index, data))
            p('in', line)
            p('expect', json_data[index])
            p('out', out)

        with open('src/unittest/resources/mysql57_test.json') as j:
            json_data = json.load(j)
        with open('src/unittest/resources/mysql57_test.log') as f:
            log_reader = linereader.get_reader_with_lines_splitted(f)
            for index, line in enumerate(log_reader):
                if not line:
                    break
                out = self.parser.parse(line)
                debug_print()
                self.assertEqual(json_data[index], out)


if __name__ == '__main__':
    unittest.main()
