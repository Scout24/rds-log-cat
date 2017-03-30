from rds_log_cat.parser.parser import Parser, LineParserException


class Mysql56(Parser):

    def __init__(self):
        Parser.__init__(self)

    def compose_timestamp(self, date, time, timezone):
        if not len(date) == 10:
            raise LineParserException('wrong length of date')
        if not len(time) == 8:
            raise LineParserException('wrong length of time')
        if not timezone == 'UTC':
            raise LineParserException('Only able to parse times in UTC. You gave {}'.format(timezone))
        return "{}T{}.000000Z".format(date, time)

    def parse(self, line):
        """
        parses the fields in line to generate json structure
        """
        expected_min_no_fields = 5
        result = {}
        if len(line) < expected_min_no_fields:
            raise LineParserException('line too short')

        pid = line[2]
        log_level = line[3].lstrip("[").rstrip("]")
        timezone = 'UTC'

        result = {
            '@timestamp': self.compose_timestamp(line[0], line[1], timezone),
            'log_level': log_level,
            'process_id': int(pid),
            'message': ' '.join(map(str, line[4:]))
        }
        return result
