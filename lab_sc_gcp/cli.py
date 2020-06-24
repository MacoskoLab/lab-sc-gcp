#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Command line interface for interacting with GCP projects, creating and managing instances.
"""
import argparse
import os

from lab_sc_gcp.user_defaults import *
from lab_sc_gcp.gce import *
from lab_sc_gcp.storage import *
from subprocess import PIPE, run, call

import warnings
# Hide warnings from Google Cloud SDK about authentication
# TODO: make more granular filter so not all user warnings are ignored
warnings.simplefilter(action='ignore', category=UserWarning)

# Available commands
c_CREATE = 'create-instance'
c_LIST = 'list-instances'
c_STOP = 'stop-instance'
c_DELETE = 'delete-instance'
c_START = 'start-instance'
c_SET_MACHINE = 'set-machine-type'
c_LIST_MACHINES = 'list-machine-types'
c_SET_TLABEL = 'set-time-label'
c_UPLOAD_LIBS = 'upload-libs'
# TODO: THESE LAST TWO NEED TO BE ADDED
c_UPLOAD_DIR_INST = 'upload-dir-instance'
c_DOWNLOAD_INST = 'download-from-inst'

# Globals
max_inst = 2  # max number of instances allowed at one time

def confirm(question):
    while True:
        answer = input(question + ' (y/n): ').lower().strip()
        if answer in ('y', 'yes', 'n', 'no'):
            return answer in ('y', 'yes')

def create_parser():
    """

    :return:
    """
    args = argparse.ArgumentParser(
        prog='cli.py',
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    args.add_argument(
        '--project',
        default=GCP_PROJECT_ID,
        help='Project ID (defaults to id specified in user_defaults.py).',
    )
    # args.add_argument(
    #     '--dry-run',
    #     action='store_true',
    #     help='Walk through and log what would occur, without performing the actions.',
    # )
    # args.add_argument(
    #     '--no-validate',
    #     dest='validate',
    #     action='store_false',
    #     help='Do not check file locally before uploading.',
    # )
    # args.add_argument(
    #     '--verbose', action='store_true', help='Whether to print debugging information'
    # )

    # Create subcommands
    subargs = args.add_subparsers(dest='command')

    # Create instance subparser
    parser_create_instance = subargs.add_parser(
        c_CREATE,
        help="Create instance with specified parameters.",
    )
    parser_create_instance.add_argument(
        '--rpass',
        required=True,
        help='Password to use for Rstudio Server.',
    )
    parser_create_instance.add_argument(
        '--user',
        default=USER,
        help='User name to associate with instance.',
    )
    parser_create_instance.add_argument(
        '--instance',
        default=INSTANCE_NAME,
        help='Name to use for instance.',
    )

    # List instances subparser
    parser_list_instances = subargs.add_parser(
        c_LIST,
        help="List instances.",
    )
    parser_list_instances.add_argument(
        '--zone',
        default=GCP_ZONE,
        help='GCP zone.',
    )

    # Stop instance subparser
    parser_stop_instance = subargs.add_parser(
        c_STOP,
        help="Stop running instance.",
    )
    parser_stop_instance.add_argument(
        '--user',
        default=USER,
        help='User name to associate with instance.',
    )
    parser_stop_instance.add_argument(
        '--zone',
        default=GCP_ZONE,
        help='GCP zone.',
    )
    parser_stop_instance.add_argument(
        '--instance',
        default=INSTANCE_NAME,
        help='Name of instance to stop.',
    )
    # Delete instance subparser
    parser_delete_instance = subargs.add_parser(
        c_DELETE,
        help="Stop running instance.",
    )
    parser_delete_instance.add_argument(
        '--user',
        default=USER,
        help='User name to associate with instance.',
    )
    parser_delete_instance.add_argument(
        '--zone',
        default=GCP_ZONE,
        help='GCP zone.',
    )
    parser_delete_instance.add_argument(
        '--instance',
        default=INSTANCE_NAME,
        help='Name of instance to delete.',
    )

    # Start instance subparser
    parser_start_instance = subargs.add_parser(
        c_START,
        help="Start stopped instance.",
    )
    parser_start_instance.add_argument(
        '--user',
        default=USER,
        help='User name to associate with instance.',
    )
    parser_start_instance.add_argument(
        '--zone',
        default=GCP_ZONE,
        help='GCP zone.',
    )
    parser_start_instance.add_argument(
        '--instance',
        default=INSTANCE_NAME,
        help='Name of instance to start.',
    )

    # Set machine type subparser
    parser_set_machine = subargs.add_parser(
        c_SET_MACHINE,
        help="Set machine type of stopped instance.",
    )
    parser_set_machine.add_argument(
        '--user',
        default=USER,
        help='User name to associate with instance.',
    )
    parser_set_machine.add_argument(
        '--machine-type',
        default=MACHINE_TYPE,
        help='Machine type to set for instance. List possible machine types with "lab-gcp list-machine-types".',
    )
    parser_set_machine.add_argument(
        '--zone',
        default=GCP_ZONE,
        help='GCP zone.',
    )
    parser_set_machine.add_argument(
        '--instance',
        default=INSTANCE_NAME,
        help='Name of instance to start.',
    )

    # List machine types subparser
    parser_list_machines = subargs.add_parser(
        c_LIST_MACHINES,
        help="List available machine types for zone.",
    )
    parser_list_machines.add_argument(
        '--zone',
        default=GCP_ZONE,
        help='GCP zone.',
    )

    # Set time-managed label
    parser_set_time_label = subargs.add_parser(
        c_SET_TLABEL,
        help="Toggle time-managed label on instance. Turns time-management on by default.",
    )
    parser_set_time_label.add_argument(
        '--user',
        default=USER,
        help='User name to associate with instance.',
    )
    parser_set_time_label.add_argument(
        '--zone',
        default=GCP_ZONE,
        help='GCP zone.',
    )
    parser_set_time_label.add_argument(
        '--instance',
        default=INSTANCE_NAME,
        help='Name of instance to set label on.',
    )
    parser_set_time_label.add_argument(
        '--turn-off',
        action='store_true',
        help='Whether to turn time-management off. (OFF=instance stays on past midnight)',
    )

    # Upload libraries to bucket parser
    parser_upload_libs = subargs.add_parser(
        c_UPLOAD_LIBS,
        help="Upload one or more single cell count libraries to default bucket.",
    )
    parser_upload_libs.add_argument(
        '--user',
        default=USER,
        help='User name to associate with instance.',
    )
    parser_upload_libs.add_argument(
        '--bucket',
        default=BUCKET,
        help='Bucket to which to upload libraries.',
    )
    parser_upload_libs.add_argument(
        '--libraries',
        required=True,
        help='Name of library (not full path) to upload or path to file containing library names.\n'+
             'If file, libraries must be listed one per line with no other separators.',
    )
    parser_upload_libs.add_argument(
        '--library-dir',
        default=LIB_DIR_SC,
        help='Path to directory where libraries stored (defaults to /broad/macosko/data/libraries).',
    )

    return args

def main():
    parsed_args = create_parser().parse_args()

    if parsed_args.command == c_CREATE:
        # Check that user has fewer than max instances
        user = parsed_args.user
        instances = list_instances(parsed_args.project)
        curr_user = [inst.get('labels', {}).get('owner') for inst in instances['items']]
        # TODO: fix error codes
        if curr_user.count(user) >= max_inst:
            raise RuntimeError('You already have {} instances in use. '.format(max_inst) +
                            'Please delete one before creating another.\n' +
                            'You can see your existing instances with "lab-gcp list instances".')
        # TODO: make sure instance name contains no slashes, other breaking chars
        res = create_instance(user=parsed_args.user,
                              name=parsed_args.instance,
                              rstudio_passwd=parsed_args.rpass)
        final_name = res['targetLink'].split('/')[-1]
        instances = list_instances(project=parsed_args.project)
        nat_ip = [item for item in instances['items']
                  if item['name'] == final_name][0]['networkInterfaces'][0]['accessConfigs'][0]['natIP']
        print('Your instance {} has been created.'.format(final_name))
        print('You can access RStudio Server at http://{}:8787.'.format(nat_ip))


    if parsed_args.command == c_LIST:
        # In this case, probably easier for the user to just see list output from google cloud sdk
        # Could change to call API later
        sdk_command = ['gcloud', 'compute', 'instances', 'list', '--project', parsed_args.project]
        call(sdk_command)

    if parsed_args.command == c_STOP:
        #TODO: Add check to see if instance has already been stopped
        res = stop_instance(user=parsed_args.user,
                            name=parsed_args.instance,
                            project=parsed_args.project,
                            zone=parsed_args.zone)
        final_name = res['targetLink'].split('/')[-1]
        print('Your instance {} is being stopped. This may take a minute.'.format(final_name))

    if parsed_args.command == c_DELETE:
        # Generate full instance name
        final_name = parsed_args.instance
        if parsed_args.user not in parsed_args.instance:
            final_name = '-'.join([parsed_args.instance, parsed_args.user])

        confirmed = confirm("Are you sure you want to delete instance {}? ".format(final_name) +
                            "The corresponding boot disk will also be deleted.")
        if confirmed:
            res = delete_instance(user=parsed_args.user,
                                name=parsed_args.instance,
                                project=parsed_args.project,
                                zone=parsed_args.zone)
            print('Your instance {} is being deleted. This may take a minute.'.format(final_name))

    if parsed_args.command == c_START:
        # TODO: Add check to see if instance has already been started
        res = start_instance(user=parsed_args.user,
                            name=parsed_args.instance,
                            project=parsed_args.project,
                            zone=parsed_args.zone)

        final_name = res['targetLink'].split('/')[-1]
        instances = list_instances(project=parsed_args.project)
        nat_ip = [item for item in instances['items']
                  if item['name'] == final_name][0]['networkInterfaces'][0]['accessConfigs'][0]['natIP']

        print('Your instance {} is being started. This may take a minute'.format(final_name))
        print('You can access RStudio Server at http://{}:8787.'.format(nat_ip))

    if parsed_args.command == c_SET_MACHINE:
        # Generate full instance name
        final_name = parsed_args.instance
        if parsed_args.user not in parsed_args.instance:
            final_name = '-'.join([parsed_args.instance, parsed_args.user])

        # Check that instance is stopped
        instances = list_instances(project=parsed_args.project)
        status = nat_ip = [item for item in instances['items']
                  if item['name'] == final_name][0]['status']
        if status != 'TERMINATED':
            raise RuntimeError('You must stop your instance before changing its machine type. ' +
                            'If you have recently sent a stop command, wait one or two minutes\n' +
                            'for the instance to stop fully before trying to set the machine type again.')

        res = set_machine_type(user=parsed_args.user,
                               machine_type=parsed_args.machine_type,
                            name=parsed_args.instance,
                            project=parsed_args.project,
                            zone=parsed_args.zone)
        final_name = res['targetLink'].split('/')[-1]

        print('The machine type of your instance {} has been updated to {}.'.format(final_name,
                                                                                   parsed_args.machine_type))

    if parsed_args.command == c_LIST_MACHINES:
        # Again use google cloud SDK output
        sdk_command = ['gcloud', 'compute', 'machine-types',
                       'list', "--filter=zone:{}".format(parsed_args.zone)]
        call(sdk_command)
        print("To specify a custom machine type, use the following format;\n" +
              "where CPUS is 1 or an even number up to 32 (2, 4, 6, etc), and \n" +
              "MEMORY is the total memory for this instance. Memory must be a \n" +
              "multiple of 256 MB and must be supplied in MB (e.g. 5 GB of memory is 5120 MB):\n" +
              "custom-CPUS-MEMORY\nFor example: custom-4-5120")

    if parsed_args.command == c_SET_TLABEL:
        label_value = 'time-unmanaged' if parsed_args.turn_off else 'time-managed'

        res = set_label(user=parsed_args.user,
                        label_key='env',
                        label_value=label_value,
                        name=parsed_args.instance,
                        project=parsed_args.project,
                        zone=parsed_args.zone)

        final_name = res['targetLink'].split('/')[-1]
        print('Your instance {} has been set to {}.'.format(final_name,
                                                            label_value))

    if parsed_args.command == c_UPLOAD_LIBS:
        # As of 2019, storage API does not have native support for recursive upload
        # Rely on existing gsutil utilities for now
        # Check if uploading from file
        if os.path.isdir('{}/{}'.format(parsed_args.library_dir, parsed_args.libraries)):
            libraries = [parsed_args.libraries]
        elif os.path.isfile(parsed_args.libraries):
            print('Reading libraries from file.')
            with open(parsed_args.libraries, 'r') as f:
                libraries = f.read().splitlines()
        else:
            raise RuntimeError('Provided "libraries" must be valid directory or file path.')

        for lib in libraries:
            # Check if generated by 10x or new pipeline (jp)
            short_lib = '_'.join(lib.split('_')[1:])
            if os.path.isdir('{}/{}/outs'.format(parsed_args.library_dir, lib)):
                upload_libraries_10x(libraries=lib,
                                     bucket_name=parsed_args.bucket,
                                     library_dir=parsed_args.library_dir)
            elif os.path.isfile('{}/{}/{}.bam'.format(parsed_args.library_dir, lib, short_lib)):
                upload_libraries_jp(libraries=lib,
                                    bucket_name=parsed_args.bucket,
                                    library_dir=parsed_args.library_dir)
            else:
                warnings.warn('Library {} does not have a recognized output format (10x, jp)'.format(lib) +
                              ' and is being skipped.', RuntimeWarning)

        # TODO: Check if some libraries have already been uploaded?
        # gsutil will log directly to console




# CLI entry points
if __name__ == '__main__':
    main()

