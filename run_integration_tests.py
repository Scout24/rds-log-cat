import logging
import json
import os
import sys

import cfn_sphere
import pybuilder.cli


# sync with build.py (project)
BASE_PROJECT_NAME = 'rds_log_cat'
SUFFIX = 'it'


class RunInDirectory(object):

    def __init__(self, new_pwd):
        self.new_pwd = new_pwd
        self.old_pwd = None

    def __enter__(self):
        self.old_pwd = os.getcwd()
        os.chdir(self.new_pwd)

    def __exit__(self, *_):
        os.chdir(self.old_pwd)


class Stack(object):

    def __init__(self, template_file, suffix='it', region=None, tags=None):
        self.template = template_file
        self.suffix = suffix
        self.tags = tags or []
        self.config = self.load_config()
        if region is not None:
            self.update_region(region)
        self.region = self.get_region()
        self.logger = cfn_sphere.util.get_logger()
        self.logger.setLevel(logging.INFO)

    def _get_template_dir(self):
        return os.path.dirname(os.path.realpath(self.template))

    def load_config(self):
        with RunInDirectory(self._get_template_dir()):
            config = cfn_sphere.file_loader.FileLoader.get_yaml_or_json_file(
                os.path.basename(self.template), None)
        return config

    def create_stack_config(self):
        return cfn_sphere.stack_configuration.Config(config_dict=self.config)

    def get_region(self):
        return self.config['region']

    def update_region(self, region):
        self.config['region'] = region

    def update_parameters(self, stack_name, parameters):
        stack_parameters = self.config['stacks'][stack_name]['parameters']
        for key, value in parameters.iteritems():
            stack_parameters[key] = value
        self.config['stacks'][stack_name]['parameters'] = stack_parameters

    def rename_stacks(self):
        '''
        rename stacks with adding suffix
        renames refs to stack too
        '''
        new_stacks = {}
        mapping = {}
        for key, value in self.config['stacks'].iteritems():
            new_key = '{}-{}'.format(key, self.suffix)
            new_stacks[new_key] = value
            mapping[key] = new_key
        for key, value in new_stacks.iteritems():
            new_stacks[key] = self._rename_refs(value, mapping)
        self.config['stacks'] = new_stacks

    def _rename_refs(self, stack, mapping):
        if 'parameters' not in stack:
            return stack
        result = stack
        for key, value in stack['parameters'].iteritems():
            if value.lower().startswith('|ref|'):
                ref = value.split('|', 2)[2]
                for old, new in mapping.iteritems():
                    if ref.startswith('{}.'.format(old)):
                        result['parameters'][key] = '|ref|{}{}'.format(
                            new, ref[len(old):])
                        break
        return result

    def create(self):
        with RunInDirectory(self._get_template_dir()):
            self.logger.info('Region: %s, Creating/Updating cfn stacks from %s',
                             self.region, self.template)
            self.rename_stacks()
            self.logger.debug('new config: \n %s',
                              json.dumps(self.config, indent=2))
            cfn_sphere.StackActionHandler(
                config=self.create_stack_config()).create_or_update_stacks()

    def delete(self):
        cfn_sphere.StackActionHandler(
            config=self.create_stack_config()).delete_stacks()


def keyname_of_lambda(project_name):
    '''
    Discovers version string of previous build
    and construct s3 upload filename (key)
    '''
    with open('target/VERSION') as version_file:
        version = version_file.read()
    keyname = '{0}_v{1}/{2}.zip'.format(
        project_name, version, project_name)
    return keyname


def get_stack_basename():
    return '{}'.format(BASE_PROJECT_NAME.replace('_', '-'))


def get_stack_paramters():
    bucket = '{}-eu-west-1'.format(os.environ['DISTRIBUTION_BUCKET_NAME'])
    key = os.environ.get(
        'uploaded_zip', keyname_of_lambda(BASE_PROJECT_NAME))
    return {
        'lambdaFunctionS3Bucket': bucket,
        'lambdaFunctionS3Key': key,
        'logFileType': 'postgresql'
    }


def create_test_stack():
    parameters = get_stack_paramters()
    stack_basename = get_stack_basename()
    stack = Stack('cfn/stacks.yaml')
    stack.update_parameters(stack_basename, parameters)
    stack.create()
    return stack


def run_integration_tests():
    os.environ[
        'STACK_NAME_LAMBDA'] = '{}-{}'.format(get_stack_basename(), SUFFIX)
    result = pybuilder.cli.main(
        '-X', '-E', 'teamcity', 'run_integration_tests')
    return result


def run():
    # pybuilder.cli.main('-o', '-E', 'teamcity')
    stack = create_test_stack()
    try:
        return run_integration_tests()
    finally:
        stack.delete()

if __name__ == '__main__':
    region = os.environ.get('AWS_DEFAULT_REGION')
    if region != "eu-west-1":
        print('Wrong AWS_DEFAULT_REGION {}. Please set to eu-west-1.'.format(region))
        print('eg: export AWS_DEFAULT_REGION="eu-west-1"')
        sys.exit(1)
    sys.exit(run())
