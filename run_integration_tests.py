import logging
import json
import os
import sys

import cfn_sphere
import pybuilder.cli


# sync with build.py (project)
BASE_PROJECT_NAME = 'rds_log_cat'
SUFFIX = 'it'


class Stack(object):

    def __init__(self, template_file, suffix='it', region=None, tags=None):
        self.logger = cfn_sphere.util.get_logger()
        self.logger.level = logging.INFO

        self.template = template_file
        self.suffix = suffix
        self.tags = tags if tags is not None else []
        self._change_to_workdir(os.path.dirname(
            os.path.realpath(self.template)))
        self.config = cfn_sphere.file_loader.FileLoader.get_yaml_or_json_file(
            os.path.basename(template_file), None)
        if region is not None:
            self.update_region(region)
        self.region = self.get_region()

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

    def _change_to_workdir(self, path=None):
        if path is not None:
            self.workdir = path
            self.savedPath = os.getcwd()
            self.logger.debug('saved path: %s', self.savedPath)
        os.chdir(self.workdir)

    def _restore_dir(self):
        os.chdir(self.savedPath)

    def create(self):
        self._change_to_workdir()
        self.logger.info('Region: %s, Creating/Updating cfn stacks from %s',
                         self.region, self.template)
        self.rename_stacks()
        self.logger.debug('new config: \n %s',
                          json.dumps(self.config, indent=2))
        cfn_sphere.StackActionHandler(
            config=self.create_stack_config()).create_or_update_stacks()
        self._restore_dir()

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


def get_stack_name(project_name):
    return '{}'.format(project_name.replace('_', '-'))


def run():
    # pybuilder.cli.main('-o', '-E', 'teamcity')
    bucket = os.environ.get('DISTRIBUTION_BUCKET_NAME')
    key = os.environ.get(
        'uploaded_zip', keyname_of_lambda(BASE_PROJECT_NAME))
    stack_basename = get_stack_name(BASE_PROJECT_NAME)
    stack = Stack('cfn/stacks.yaml')
    parameters = {
        'lambdaFunctionS3Bucket': bucket,
        'lambdaFunctionS3Key': key,
        'logFileType': 'postgresql'
    }
    stack_name = get_stack_name(BASE_PROJECT_NAME)
    stack.update_parameters(stack_name, parameters)
    stack.create()
    os.environ['STACK_NAME_LAMBDA'] = '{}-{}'.format(stack_basename, SUFFIX)
    result = pybuilder.cli.main(
        '-X', '-E', 'teamcity', 'run_integration_tests')
    stack.delete()
    return result

if __name__ == '__main__':
    sys.exit(run())
