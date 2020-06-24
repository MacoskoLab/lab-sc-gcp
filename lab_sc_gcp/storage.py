#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Functions for managing Google Compute Storage (GCE) resources.

Also includes some wrappers for gsutil calls.
"""
from googleapiclient.discovery import build
from .user_defaults import *
from pkg_resources import resource_filename

from google.cloud import storage
from subprocess import PIPE, run, call

def upload_file(
    source_file_name,
    destination_name,
    bucket_name=BUCKET,
):
    """
    Uploads a file to the bucket.
    """
    # bucket_name = "your-bucket-name"
    # source_file_name = "local/path/to/file"
    # destination_blob_name = "storage-object-name"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_name)

    blob.upload_from_filename(source_file_name)

def upload_libraries_10x(
    libraries,
    bucket_name=BUCKET,
    library_dir=LIB_DIR_SC,
):
    """
    Currently only supports 10x libraries generated with v>=3.
    :param libraries:
    :param bucket_name:
    :param library_dir:
    :return:
    """
    # Add prefix if necessary
    if 'gs://' not in bucket_name:
        bucket_name = 'gs://' + bucket_name

    # Series of gsutil calls because rsync exclude functionality doesn't work...
    gsutil_args = ['gsutil', 'cp', '{}/{}/outs/raw_feature_bc_matrix.h5'.format(library_dir, libraries),
                    '{}/libraries/{}/outs/'.format(bucket_name, libraries)]
    call(gsutil_args)
    gsutil_args = ['gsutil', 'cp', '{}/{}/outs/filtered_feature_bc_matrix.h5'.format(library_dir, libraries),
                   '{}/libraries/{}/outs/'.format(bucket_name, libraries)]
    call(gsutil_args)
    gsutil_args = ['gsutil', 'cp', '-r', '{}/{}/outs/raw_feature_bc_matrix/'.format(library_dir, libraries),
                   '{}/libraries/{}/outs/'.format(bucket_name, libraries)]
    call(gsutil_args)
    gsutil_args = ['gsutil', 'cp', '-r', '{}/{}/outs/filtered_feature_bc_matrix/'.format(library_dir, libraries),
                   '{}/libraries/{}/outs/'.format(bucket_name, libraries)]
    call(gsutil_args)

def upload_libraries_jp(
    libraries,
    bucket_name=BUCKET,
    library_dir=LIB_DIR_SC,
):
    """

    :param libraries:
    :param bucket_name:
    :param library_dir:
    :return:
    """
    # Add prefix if necessary
    if 'gs://' not in bucket_name:
        bucket_name = 'gs://' + bucket_name

    # Series of gsutil calls because rsync exclude functionality doesn't always work...
    gsutil_args = ['gsutil', 'cp', '{}/{}/*/alignment/*digital_expression_matrix*'.format(library_dir, libraries),
                    '{}/libraries/{}/'.format(bucket_name, libraries)]
    call(gsutil_args)
    gsutil_args = ['gsutil', 'cp', '{}/{}/*/alignment/*digital_expression_barcodes*'.format(library_dir, libraries),
                   '{}/libraries/{}/'.format(bucket_name, libraries)]
    call(gsutil_args)
    gsutil_args = ['gsutil', 'cp', '{}/{}/*/alignment/*digital_expression_features*'.format(library_dir, libraries),
                   '{}/libraries/{}/'.format(bucket_name, libraries)]
    call(gsutil_args)
    gsutil_args = ['gsutil', 'cp', '{}/{}/*/alignment/*digital_expression_summary*'.format(library_dir, libraries),
                   '{}/libraries/{}/'.format(bucket_name, libraries)]
    call(gsutil_args)