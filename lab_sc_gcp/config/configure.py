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
from lab_sc_gcp.utilities import *
from googleapiclient.discovery import build
from google.cloud import storage

# Config paths
default_config = resource_filename('lab_sc_gcp', 'config/config.ini')
user_config = os.path.join(Path.home(), '.lab_sc_gcp', 'config.ini')

# A few project and bucket related functions
def list_projects():
    service = build('cloudresourcemanager', 'v1')
    projects = service.projects()

    res = projects.list().execute()

    return res

def list_buckets(project):
    storage_client = storage.Client()
    buckets = storage_client.list_buckets(project=project)

    return [bucket.name for bucket in buckets]


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

    # Get default project
    projects = list_projects()
    available_proj_ids = [proj['projectId'] for proj in projects['projects']]
    print("Available projects:\n{}".format('\n'.join(available_proj_ids)))
    project = input_cv('Provide default GCP project ID: ',
                       controlled_values=available_proj_ids).strip()
    config.set('GCP', 'GCP_PROJECT_ID', project)

    # Get image source project
    image_project = input_cv('Provide project ID to use as source of compute images: ',
                             controlled_values=available_proj_ids).strip()
    config.set('GCP', 'IMAGE_PROJECT', image_project)

    # Get default bucket, selecting from those available on default and image source
    buckets_d = list_buckets(project=project)
    buckets_s = list_buckets(project=image_project)
    buckets = buckets_d + buckets_s
    print("Available buckets:\n{}".format('\n'.join(buckets)))
    bucket = input_cv('Provide default GCP bucket: ',
                      controlled_values=buckets).strip()
    bucket = bucket.replace('gs://', '').replace('/', '')
    config.set('GCP', 'bucket', bucket)

    # Get default library directory
    lib_dir = input('Provide path to single cell libraries (check Guidelines google doc for instructions): ').strip()
    config.set('LOCAL', 'lib_dir_sc', lib_dir)

    # Write config
    with open(user_config, 'w') as configfile:
        config.write(configfile)

    print('Change additional defaults by modifying {} directly.'.format(user_config))
    print('Check Computational Guidelines doc if default fields are unclear.')


