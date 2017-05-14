#!/usr/bin/env python

from __future__ import print_function, absolute_import, division

import sys
import os
import logging

import rds_log_cat.rds_log_cat as rlc


if __name__ == "__main__":
    print("local mode executing ...")
    logging.getLogger().setLevel(os.getenv('LOG_LEVEL', 'INFO'))
    bucket = sys.argv[1]
    key = sys.argv[2]
    logfile_type = sys.argv[3]
    kinesis_stream = sys.argv[4]
    origin = sys.argv[5]
    rlc.read_and_send(rlc.s3_get_object_raw_stream(bucket, key),
                      logfile_type, kinesis_stream, key, origin)