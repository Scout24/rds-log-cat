from __future__ import print_function, unicode_literals, division

import base64
import json
import os

import boto3
import unittest2 as unittest


def invoke_lambda(name, payload=None):
    client = boto3.client('lambda')
    response = client.invoke(
        FunctionName=name,
        LogType='Tail',
        Payload=payload)
    return response


def get_stackname():
    name = os.getenv("STACK_NAME_LAMBDA")
    if name is None:
        name = 'rds-log-cat'   # try default
        # TODO check if stack exists, otherwise throw an error
        # raise MissingConfigurationException(
        #    """
        #    missing ENV variable. TRY:
        #    export STACK_NAME_LAMBDA="rds-log-cat"
        #    """)
    print('lambda from stack: {}'.format(name))
    return name


def get_s3_bucket_stack_name():
    return '{}-s3'.format(get_stackname())


def get_lambda_function_name():
    client = boto3.client('cloudformation')
    response = client.describe_stack_resource(
        StackName=get_stackname(), LogicalResourceId='lambdaFunction')
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
        StackName=get_s3_bucket_stack_name(), LogicalResourceId='logBucket')
    return response['StackResourceDetail']['PhysicalResourceId']


class InvocationTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def assert_no_invocation_error(self, response):
        if 'LogResult' in response:
            self.assertNotIn('FunctionError', response,
                             'invocation error.\n response: {}'.format(base64.b64decode(response['LogResult'])))
        else:
            print(response)

    def test_is_lambda_invokeable(self):
        response = invoke_lambda(
            get_lambda_function_name(), '{"Records": []}')
        self.assert_no_invocation_error(response)
        self.assertEqual(200, response['StatusCode'])

    def test_is_lambda_be_able_to_read_s3(self):
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


if __name__ == '__main__':
    unittest.main()
