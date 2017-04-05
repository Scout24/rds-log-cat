from __future__ import print_function, absolute_import, division

import unittest2 as unittest
import json

from rds_log_cat.parser.postgresql import Postgresql
from rds_log_cat.parser.parser import LineParserException
import rds_log_cat.linereader as linereader


class PostgresqlTests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.parser = Postgresql()

    def test_parse_timestamp_valid(self):
        (date, time, tz) = '2017-03-01 12:05:17 UTC'.split()
        self.assertEqual("2017-03-01T12:05:17.000000Z",
                         self.parser.compose_timestamp(date, time, tz))

    def test_parse_timestamp_invalid_field_will_raise_ae(self):
        with self.assertRaises(LineParserException):
            self.parser.compose_timestamp('', '00:00:00', 'UTC')
        with self.assertRaises(LineParserException):
            self.parser.compose_timestamp('0000-00-00', '00:00', 'UTC')
        with self.assertRaises(LineParserException):
            self.parser.compose_timestamp('0000-00-00', '00:00:00', 'CET')

    def test__decompose_multi_var_field(self):
        (tz, pid, log_level) = self.parser._decompose_multi_var_field(
            'UTC::@:[3256]:WARNING:')
        self.assertEqual('UTC', tz)
        self.assertEqual('3256', pid)
        self.assertEqual('WARNING', log_level)

    def test_parse_test_log(self):
        def debug_print():
            def p(desc, data):
                print('%-10s #%d: %s' % (desc, index, data))
            p('in', line)
            p('expect', json_data[index])
            p('out', out)

        with open('src/unittest/resources/postgresql_test.json') as j:
            json_data = json.load(j)
        with open('src/unittest/resources/postgresql_test.log') as f:
            log_reader = linereader.get_reader_with_lines_splitted(f)
            for index, line in enumerate(log_reader):
                if len(line) == 0:
                    break
                out = self.parser.parse(line)
                debug_print()
                self.assertEqual(json_data[index], out)

    def test_parse_wrong_test_log(self):
        with open('src/unittest/resources/postgresql_test_wrong.log') as f:
            log_reader = linereader.get_reader_with_lines_splitted(f)
            for index, line in enumerate(log_reader):
                with self.assertRaises(LineParserException):
                    self.parser.parse(line)


if __name__ == '__main__':
    unittest.main()
