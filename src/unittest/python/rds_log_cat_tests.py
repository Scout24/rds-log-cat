from __future__ import print_function, absolute_import, division

import boto3
import unittest2 as unittest
from mock import MagicMock, patch
from moto import mock_s3

import rds_log_cat.rds_log_cat as rds_log_cat
from rds_log_cat.parser.parser import LineParserException


class Tests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        pass

    def example_minimal_s3_event(self):
        return {
            'Records': [{
                's3': {
                    'bucket': {
                        'name': 'mybucket'
                    },
                    'object': {
                        'key': 'myfile'
                    }
                }
            }]
        }

    @unittest.skip("skipping because of buildserver fails. TODO - reenable")
    @mock_s3
    def test_call_s3_get_object_raw_stream_wo_exceptions(self):
        s3 = boto3.client('s3')
        s3.create_bucket(Bucket='foo')
        s3.put_object(Body='foo', Bucket='foo', Key='bar')
        file_like_obj = rds_log_cat.s3_get_object_raw_stream('foo', 'bar')
        self.assertEqual('foo', file_like_obj.next())

    def test_get_bucket_and_key_from_event(self):
        res = rds_log_cat.get_bucket_and_key_from_event(
            self.example_minimal_s3_event())
        self.assertEqual(('mybucket', 'myfile'), res.next())

    @patch('rds_log_cat.rds_log_cat.s3_get_object_raw_stream')
    @patch('rds_log_cat.rds_log_cat.read_and_send')
    @patch('rds_log_cat.rds_log_cat.get_bucket_and_key_from_event')
    @patch('rds_log_cat.rds_log_cat.get_config')
    def test_handler(self, get_config, get_bucket_and_key_from_event, read_and_send, s3_get_object_raw_stream):
        get_config.return_value = ('type', 'kinesisStream', 'origin')
        get_bucket_and_key_from_event.return_value = [('foo', 'key')]
        rds_log_cat.handler(
            self.example_minimal_s3_event(),
            Tests.MockContext('arn', 'funcname', 'anyVersion'))
        read_and_send.assert_called_once_with(
            s3_get_object_raw_stream('foo', 'key'), 'type', 'kinesisStream', 'key', 'origin')

    @patch('rds_log_cat.rds_log_cat.s3_get_object_raw_stream')
    @patch('rds_log_cat.rds_log_cat.read_and_send')
    @patch('rds_log_cat.rds_log_cat.get_bucket_and_key_from_event')
    @patch('rds_log_cat.rds_log_cat.get_config')
    def test_handler_with_read_and_send_exception_reraised(
            self, get_config, get_bucket_and_key_from_event,
            read_and_send, s3_get_object_raw_stream):
        get_config.return_value = ('type', 'kinesisStream', 'origin')
        get_bucket_and_key_from_event.return_value = Exception()
        rds_log_cat.handler(
            self.example_minimal_s3_event(),
            Tests.MockContext('arn', 'funcname', 'anyVersion'))
        with self.assertRaises(Exception):
            read_and_send.assert_called_once_with(
                s3_get_object_raw_stream('foo', 'bar'),
                'type', 'kinesisStream')

    def test_process(self):
        reader = [0, 1]
        parser = MagicMock()
        parser.parse.side_effect = [{'id': 1}, {'id': 2}]
        result = rds_log_cat.process(reader, parser, '', 'foo')
        result = list(result)
        expected = [{'PartitionKey': '641ce8fd24c9a626691d97952ff1a2abcbc553e0a9f5ff987b302cc8',
                     'Data': '{"origin": "foo", "id": 1}'},
                    {'PartitionKey': 'e2b13fb360b1ec2d2474b3482c7c55e7662d589f1fcf057a9c5cd555',
                     'Data': '{"origin": "foo", "id": 2}'}]
        parser.parse.assert_called()
        print(result)
        self.assertEqual(expected, result)

    def test_process_with_one_unparseable_line_which_should_be_skipped(self):
        reader = [0, 1, 2]
        parser = MagicMock()
        parser.parse.side_effect = [{'foo': 0}, LineParserException(), {}]
        result = rds_log_cat.process(reader, parser, '', '')
        self.assertEqual(len(list(result)), 2)

    @patch('rds_log_cat.rds_log_cat.process')
    @patch('rds_log_cat.linereader.get_reader_with_lines_splitted')
    @patch('rds_log_cat.sender.send_in_batches')
    @patch('rds_log_cat.parser.parser.Parser.load')
    def test_read_and_send(self, _, sender, get_reader, process):
        stream_mock = MagicMock()
        rds_log_cat.read_and_send(stream_mock, 'foo', 'bar', '', '')
        get_reader.assert_called_once_with(stream_mock)
        process.assert_called_once()
        sender.assert_called_once()

    class MockContext:

        def __init__(self, invoked_function_arn, function_name, function_version):
            self.function_name = function_name
            self.invoked_function_arn = invoked_function_arn
            self.function_version = function_version


if __name__ == '__main__':
    unittest.main()
