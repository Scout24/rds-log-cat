from __future__ import print_function, unicode_literals, division

import base64
import json

import boto3
import unittest2 as unittest


def invoke_lambda(name, payload=None):
    client = boto3.client('lambda')
    response = client.invoke(
        FunctionName=name,
        LogType='Tail',
        Payload=payload)
    return response


class MissingConfigurationException(Exception):
    pass


def get_lambda_function_name():
    client = boto3.client('cloudformation')
    response = client.describe_stack_resource(
        StackName='rds-log-cat-it', LogicalResourceId='lambdaFunction')
    name = response['StackResourceDetail']['PhysicalResourceId']
    print('lambda function name: {}'.format(name))
    return name


def get_test_logfile():
    bucket = get_s3_bucket_name()
    key = 'postgresql_test.log'
    client = boto3.client('s3')
    with open('src/unittest/resources/postgresql_test.log') as fileobj:
        client.put_object(Body=fileobj, Bucket=bucket, Key=key)
    return bucket, key


def get_s3_bucket_name():
    client = boto3.client('cloudformation')
    response = client.describe_stack_resource(
        StackName='rds-log-cat-s3-it', LogicalResourceId='logBucket')
    return response['StackResourceDetail']['PhysicalResourceId']


def delete_prefix(bucket, prefix):
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    keys_to_delete = {'Objects': []}
    keys_to_delete['Objects'] = [{'Key': o['Key']}
                                 for o in response['Contents']]
    response = s3.delete_objects(Bucket=bucket, Delete=keys_to_delete)


class InvocationTest(unittest.TestCase):

    def assert_no_invocation_error(self, response):
        if 'LogResult' in response:
            self.assertNotIn('FunctionError', response, 'invocation error.\n response: {}'.format(
                base64.b64decode(response['LogResult'])))
        else:
            print(response)

    def test_is_lambda_invokeable(self):
        response = invoke_lambda(
            get_lambda_function_name(), '{"Records": []}')
        self.assert_no_invocation_error(response)
        self.assertEqual(200, response['StatusCode'])

    def test_is_lambda_be_able_to_read_s3(self):
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
            self.assert_no_invocation_error(response)
        finally:
            if bucket:
                delete_prefix(bucket, key)


if __name__ == '__main__':
    unittest.main()
