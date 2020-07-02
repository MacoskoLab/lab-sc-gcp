#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configure defaults and user settings for package.
"""

import os
import shutil
import configparser
from pkg_resources import resource_filename
from pathlib import Path
from subprocess import call

# Config paths
default_config = resource_filename('lab_sc_gcp', 'config/config.ini')
user_config = os.path.join(Path.home(), '.lab_sc_gcp', 'config.ini')

def generate_config():
    # Check if user config file exists
    if not os.path.isfile(user_config):
        # If not, create it
        dir_name = os.path.join(Path.home(), '.lab_sc_gcp')
        if not os.path.isdir(dir_name):
            os.mkdir(dir_name)
        shutil.copy2(default_config, user_config)
        print('Created user config file {}.\n\n'.format(user_config))

def get_config():
    # First generate user config file if necessary
    generate_config()
    # Read config
    config = configparser.SafeConfigParser(allow_no_value=True)
    config.read(user_config)

    return config

def check_init():
    # Check initialization of important defaults
    config = configparser.SafeConfigParser(allow_no_value=True)
    config.read(user_config)

    if '' in [config['LOCAL']['user'],
              config['LOCAL']['lib_dir_sc'],
              config['GCP']['gcp_project_id'],
              config['GCP']['bucket']]:
        raise RuntimeError('You have not yet initialized important defaults. Please run "lab-gcp init".')

def init_defaults():
    config = get_config()
    # Get username
    user = input('Provide your Broad username: ').strip()
    config.set('LOCAL', 'USER', user)

    # Get default project -- using google cloud sdk
    call(['gcloud', 'projects', 'list'])
    project = input('Provide default GCP project ID (first column): ').strip()
    config.set('GCP', 'GCP_PROJECT_ID', project)

    # Get default bucket -- using google cloud sdk
    call(['gsutil', 'ls', '-p', project])
    bucket = input('Provide default GCP bucket: ').strip()
    bucket = bucket.replace('gs://', '').replace('/', '')
    config.set('GCP', 'bucket', bucket)

    # Get default library directory
    lib_dir = input('Provide path to single cell libraries: ').strip()
    config.set('LOCAL', 'lib_dir_sc', lib_dir)

    # Write config
    with open(user_config, 'w') as configfile:
        config.write(configfile)

    print('Change additional defaults by modifying {} directly.'.format(user_config))


