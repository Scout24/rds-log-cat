from __future__ import unicode_literals, print_function, absolute_import, division


from rds_log_cat.parser.parser import Parser, LineParserException


class Postgresql(Parser):

    def __init__(self):
        Parser.__init__(self)

    def compose_timestamp(self, date, time, timezone):
        if len(date) != 10:
            raise LineParserException('wrong length of date - wrong date is: ' + date)
        if len(time) != 8:
            raise LineParserException('wrong length of time - wrong time is: ' + time)
        if timezone != 'UTC':
            raise LineParserException('Only able to parse times in UTC. You gave {}'.format(timezone))
        return "{}T{}.000000Z".format(date, time)

    def _decompose_multi_var_field(self, field):
        (timezone, _, _, pid, log_level, _) = field.split(':')
        pid = pid[1:-1]
        return (timezone, pid, log_level)

    def parse(self, line):
        """
        parses the fields in line to generate json structure
        """
        expected_min_no_fields = 5
        result = {}
        if len(line) < expected_min_no_fields:
            raise LineParserException('line too short')

        (timezone, pid, log_level) = self._decompose_multi_var_field(line[2])

        result = {
            '@timestamp': self.compose_timestamp(line[0], line[1], timezone),
            'log_level': log_level,
            'process_id': int(pid),
            'message': ' '.join(map(str, line[4:]))
        }
        return result
