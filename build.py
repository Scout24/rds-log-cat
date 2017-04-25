import os
from pybuilder.core import use_plugin, init
from pybuilder.vcs import VCSRevision

use_plugin('copy_resources')
use_plugin('pypi:pybuilder_aws_plugin')
use_plugin("python.core")
use_plugin("python.coverage")
use_plugin("python.distutils")
use_plugin("python.flake8")
use_plugin("python.install_dependencies")
use_plugin('python.integrationtest')
use_plugin("python.unittest")

name = "rds_log_cat"
version = '0.1.%s' % VCSRevision().get_git_revision_count()
summary = 'lambda function to send (rds) logs to kinesis'
description = open("README.md").read()
license = 'MIT License'
url = 'https://github.com/ImmobilienScout24/rds-log-cat'

default_task = ['clean', 'analyze', 'package']


@init
def set_properties(project):
    project.build_depends_on("unittest2")
    project.build_depends_on("moto")
    project.build_depends_on("mock")
    project.build_depends_on("requests_mock")
    project.build_depends_on("cfn-sphere")

    project.depends_on("boto3")
    project.depends_on("requests")
    project.depends_on("aws-lambda-configurer")

    '''
    Distribution bucket setting for lambda
    '''
    project.set_property(
        'bucket_name', os.environ.get('DISTRIBUTION_BUCKET_NAME'))
    # if you want to distribute outside your account, change the following to 'public-read'
    project.set_property(
        'lambda_file_access_control',
        os.environ.get('LAMBDA_FILE_ACCESS_CONTROL', 'bucket-owner-full-control'))

    project.set_property('copy_resources_target', '$dir_dist')
    project.get_property('copy_resources_glob').extend(['setup.cfg'])
    project.set_property('bucket_prefix', '%s_' % name)
    project.set_property('template_key_prefix', '%s_' % name)

    project.set_property("integrationtest_inherit_environment", True)

    project.set_property('flake8_include_test_sources', True)
    project.set_property('flake8_break_build', True)
    project.set_property('install_dependencies_upgrade', True)


@init(environments='teamcity')
def set_properties_for_teamcity_builds(project):
    project.version = '%s-%s' % (project.version,
                                 os.environ.get('BUILD_NUMBER', 0))
    print("##teamcity[buildNumber '{0}']".format(version))
    project.set_property('teamcity_output', True)
    project.set_property('teamcity_parameter', 'uploaded_zip')

    project.default_task = [
        'clean',
        'install_build_dependencies',
        'upload_zip_to_s3',
        'upload_cfn_to_s3',
    ]
    project.set_property('install_dependencies_index_url',
                         os.environ.get('PYPIPROXY_URL'))

    project.set_property('template_files',
    [
        ('cfn','function.yaml')
    ])

