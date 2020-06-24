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

def upload_libraries(
    libraries,
    bucket_name=BUCKET,
    library_dir=LIB_DIR_10x,
):
    # Add prefix if necessary
    if 'gs://' not in bucket_name:
        bucket_name = 'gs://' + bucket_name

    for lib in libraries:
        # Series of gsutil calls because rsync exclude functionality doesn't work...
        gsutil_args = ['gsutil', 'cp', '{}/outs/raw_feature_bc_matrix.h5'.format(lib),
                        '{}/libraries/{}/outs/'.format(bucket_name, lib)]
        call(gsutil_args)
        gsutil_args = ['gsutil', 'cp', '{}/outs/filtered_feature_bc_matrix.h5'.format(lib),
                       '{}/libraries/{}/outs/'.format(bucket_name, lib)]
        call(gsutil_args)
        gsutil_args = ['gsutil', 'cp', '-r', '{}/outs/raw_feature_bc_matrix/'.format(lib),
                       '{}/libraries/{}/outs/'.format(bucket_name, lib)]
        call(gsutil_args)
        gsutil_args = ['gsutil', 'cp', '-r', '{}/outs/filtered_feature_bc_matrix/'.format(lib),
                       '{}/libraries/{}/outs/'.format(bucket_name, lib)]
        call(gsutil_args)