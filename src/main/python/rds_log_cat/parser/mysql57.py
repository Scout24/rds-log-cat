from rds_log_cat.parser.parser import Parser, LineParserException


class Mysql57(Parser):

    def __init__(self):
        Parser.__init__(self)

    def compose_timestamp(self, datetime, timezone):
        if len(datetime) != 27:
            raise LineParserException('wrong length of datetime - wrong date is: ' + datetime)
        if not timezone == 'UTC':
            raise LineParserException('Only able to parse times in UTC. You gave {}'.format(timezone))
        return datetime

    def parse(self, line):
        """
        parses the fields in line to generate json structure
        """
        expected_min_no_fields = 5
        if len(line) < expected_min_no_fields:
            raise LineParserException('line too short')

        pid = line[1]
        log_level = line[2].lstrip("[").rstrip("]")
        timezone = 'UTC'

        return {
            '@timestamp': self.compose_timestamp(line[0], timezone),
            'log_level': log_level,
            'process_id': int(pid),
            'message': ' '.join(map(str, line[3:]))
        }
