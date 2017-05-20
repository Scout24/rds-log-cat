from __future__ import print_function, absolute_import, division

import logging
import time

import boto3


def send_in_batches(records, stream_name, batch_size=500):
    for chunk in chunks(records, batch_size):
        if stream_name != '':
            send(chunk, stream_name)
        else:
            logging.info('stream not defined. not sending batch.')
            logging.debug('chuck: %r', chunk)


def chunks(iterable, size):
    """Yield successive n-sized chunks from l."""
    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def send(chunk, stream_name, client=None):
    if not client:
        client = boto3.client('kinesis')
    retries = 0
    while chunk:
        response = client.put_records(StreamName=stream_name, Records=chunk)
        failed_record_count = response['FailedRecordCount']
        if failed_record_count == 0:
            logging.info("Successfully sent %i records.", len(chunk))
            return

        logging.warn("%i out of %i records failed to be sent.\
                     Retrying failed ...",
                     failed_record_count, len(chunk))

        next_chunk = []
        for item, result in zip(chunk, response['Records']):
            if 'ErrorCode' in result:
                if result['ErrorCode'] == 'ProvisionedThroughputExceededException':
                    next_chunk.append(item)
                else:
                    logging.warn("Unhandled ErrorCode: %r",
                                 result['ErrorCode'])
                    logging.warn('Dropping this record.')

        chunk = next_chunk
        retries += 1
        wait_time = 0.1 * retries * retries
        time.sleep(wait_time)
        logging.info("Gathered %i records for resending.\
         Retry: %i Wait: %r sec", len(chunk), retries, wait_time)
