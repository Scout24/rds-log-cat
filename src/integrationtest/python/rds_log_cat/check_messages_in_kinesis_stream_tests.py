
import boto3
import time
import unittest2 as unittest


class MessageTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.kinesis_client = boto3.client('kinesis')
        cls.shard_id = 'shardId-000000000000'
        # TODO: discover 
        cls.name = 'rds-log-cat-kinesis-it-kinesisStream-18ULEPUSFVZ9O'
        cls.shard_it = cls.get_latest_shard_it(
            cls.kinesis_client, cls.name, cls.shard_id)

    @staticmethod
    def get_latest_shard_it(client, name, sid):
        return client.get_shard_iterator(
            StreamName=name,
            ShardId=sid,
            ShardIteratorType="LATEST")["ShardIterator"]

    def invoke_lambda(self):
        import json
        from can_lambda_be_invoked_tests import (
            get_test_logfile, invoke_lambda, get_lambda_function_name, delete_prefix)
        bucket = None
        try:
            bucket, key = get_test_logfile()
            event = {
                'Records': [{
                    's3': {'bucket': {'name': bucket},
                           'object': {'key': key}}
                }]
            }
            print(json.dumps(event))
            response = invoke_lambda(
                get_lambda_function_name(), json.dumps(event))
        finally:
            if bucket:
                delete_prefix(bucket, key)

    @unittest.skip("WIP")
    def test_for_messages_in_kinesis(self):
        self.invoke_lambda()
        while True:
            out = self.kinesis_client.get_records(
                ShardIterator=self.shard_it)
            self.shard_it = out["NextShardIterator"]
            print out
            time.sleep(1)


if __name__ == '__main__':
    unittest.main()
