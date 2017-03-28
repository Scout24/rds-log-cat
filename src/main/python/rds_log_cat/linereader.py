from __future__ import print_function, absolute_import, division

import csv


def get_reader_with_lines_splitted(flo):
    return csv.reader(paginate(flo), delimiter=' ', quotechar='"')


def paginate(readable, buffersize=4069):
    buf = ''
    while True:
        while '\n' not in buf:
            next_buf = readable.read(buffersize)
            if not next_buf:
                yield buf
                return
            buf += next_buf
            if '\n' in next_buf:
                break
        line, buf = buf.split("\n", 1)
        yield line + '\n'
