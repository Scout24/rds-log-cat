from __future__ import print_function, absolute_import, division

import hashlib
import logging
import urllib

import boto3
from aws_lambda_configurer import load_config

import rds_log_cat.linereader as linereader
import rds_log_cat.sender as sender
from rds_log_cat.parser.parser import Parser, LineParserException

logging.getLogger().setLevel(logging.INFO)


def get_config(context):
    config = load_config(Context=context)
    logging.info('Loaded config: %s', config)
    logfile_type = config.get('type')
    stream_to_send = config.get('kinesisStream')
    return (logfile_type, stream_to_send)


def get_bucket_and_key_from_event(event):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = urllib.unquote_plus(record['s3']['object']['key']).decode('utf8')
        yield (bucket, key)


def generate_partition_key(file_name, line_index):
    return hashlib.sha224("{0}.{1}".format(file_name, line_index)).hexdigest()


def handler(event, context):
    logging.info('Received event: %s', event)
    (logfile_type, kinesis_stream) = get_config(context)
    for bucket, key in get_bucket_and_key_from_event(event):
        logging.info("Processing key {} from bucket {}.".format(key, bucket))
        read_and_send(
            s3_get_object_raw_stream(bucket, key), logfile_type, kinesis_stream)


def process(reader, parser, file_name):
    records = []
    for index, line in enumerate(reader):
        record = {}
        try:
            record['Data'] = parser.parse(line)
            record['PartitionKey'] = generate_partition_key(file_name, index)
            # TODO: add more fields for the source of this record
            records.append(record)
        except LineParserException:
            logging.debug('skipped line {}'.format(index + 1))
            # TODO count overall skipped lines
    return records


def read_and_send(stream, logfile_type, send_to, file_name):
    parser_class = Parser.load(logfile_type)
    parser = parser_class()
    reader = linereader.get_reader_with_lines_splitted(stream)
    records = process(reader, parser, file_name)
    sender.send_in_batches(records, send_to)


def s3_get_object_raw_stream(bucket, key):
    client = boto3.client('s3')
    response = client.get_object(Bucket=bucket, Key=key)
    return response.get('Body')._raw_stream
