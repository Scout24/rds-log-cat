from __future__ import print_function, absolute_import, division

import logging
import time

import boto3

logging.getLogger().setLevel(logging.DEBUG)


def send_in_batches(records, stream_name, batch_size=500):
    for chunk in chunks(records, batch_size):
        send(chunk, stream_name)


def chunks(array, size):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(array), size):
        yield array[i:i + size]


def send(chunk, stream_name, client=None):
    if not client:
        client = boto3.client('kinesis')
    while chunk:
        response = client.put_records(StreamName=stream_name, Records=chunk)
        failed_record_count = response['FailedRecordCount']
        if failed_record_count == 0:
            logging.info("Successfully sent %i records", len(chunk))
            return

        logging.warn("%i out of %i records failed to be sent.",
                     failed_record_count, len(chunk))
        time.sleep(0.1)

        next_chunk = []
        for item, result in zip(chunk, response['Records']):
            if 'ErrorCode' in result:
                if result['ErrorCode'] == 'ProvisionedThroughputExceededException':
                    next_chunk.append(item)
                else:
                    logging.warn("Unhandled ErrorCode: %r",
                                 result['ErrorCode'])

        chunk = next_chunk
        logging.info("Gathered %i records for resending.", len(chunk))
