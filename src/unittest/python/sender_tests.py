from __future__ import print_function, absolute_import, division

import unittest2 as unittest
from mock import MagicMock, patch, call

from rds_log_cat.sender import (chunks, send_in_batches, send)


class SenderTests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        pass

    def test_chunks_with_array(self):
        in_array = [1, 2, 3, 4, 5]
        result = chunks(in_array, 2)
        self.assertEqual(list(result), [[1, 2], [3, 4], [5]])

    def itest_chunks_with_generator(self):
        generator = (i for i in (1, 2, 3, 4, 5))
        result = chunks(generator, 2)
        self.assertEqual(list(result), [[1, 2], [3, 4], [5]])

    @patch('rds_log_cat.sender.send')
    def test_send_in_batches(self, send):
        send_in_batches([1, 2, 3], 'foo', 2)
        expected = [call([1, 2], 'foo'), call([3], 'foo')]
        send.assert_has_calls(expected)

    def test_send_resends_when_throughput_exceeded(self):
        mock_kinesis = MagicMock()
        mock_kinesis.put_records.side_effect = [
            {
                'FailedRecordCount': 1,
                'Records': [
                    {
                        'SequenceNumber': 'string',
                        'ShardId': 'string',
                    },
                    {
                        'ErrorCode': 'ProvisionedThroughputExceededException',
                        'ErrorMessage': 'Rate exceeded for shard shardId-000000000001 in stream...'
                    },
                ]
            },

            {
                'FailedRecordCount': 0,
                'Records': [
                    {
                        'SequenceNumber': 'string',
                        'ShardId': 'string',
                    },
                ]
            }]

        send([{'Data': 'foo'}, {'Data': 'bar'}], "stream_name", mock_kinesis)

        self.assertEqual(mock_kinesis.put_records.call_count, 2)
        mock_kinesis.put_records.assert_any_call(
            StreamName="stream_name", Records=[{'Data': 'foo'}, {'Data': 'bar'}])
        mock_kinesis.put_records.assert_any_call(
            StreamName="stream_name", Records=[{'Data': 'bar'}])

    def test_send_no_empty_resend(self):
        mock_kinesis = MagicMock()
        mock_kinesis.put_records.side_effect = [
            {
                'FailedRecordCount': 1,
                'Records': [
                    {
                        'SequenceNumber': 'string',
                        'ShardId': 'string',
                    },
                    {
                        'ErrorCode': 'InternalFailure',
                        'ErrorMessage': 'Something went wrong'
                    },
                ]
            }]

        send([{'Data': 'foo'}, {'Data': 'bar'}], "stream_name", mock_kinesis)

        # Records with "InternalFailure" should not be resent. In this case it
        # can happen that errors occurred but not records should be resent.
        # But put_records() must not be called with an empty list, it raises
        # an exception if that happens.
        self.assertEqual(mock_kinesis.put_records.call_count, 1)
        mock_kinesis.put_records.assert_any_call(
            StreamName="stream_name",
            Records=[{'Data': 'foo'}, {'Data': 'bar'}])


if __name__ == '__main__':
    unittest.main()
