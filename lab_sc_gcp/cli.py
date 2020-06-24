#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Command line interface for interacting with GCP projects, creating and managing instances.
"""
import argparse
import os
import time

from lab_sc_gcp.config.configure import *
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
c_UPLOAD_DIR_INST = 'upload-dir-instance'
# TODO: THIS LAST ONE NEEDS TO BE ADDED
c_DOWNLOAD_INST = 'download-from-inst'

c_INIT = 'init'

# Globals
max_inst = 2  # max number of instances allowed at one time

# Configure user defaults
config = get_config()

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
        default=config['GCP']['gcp_project_id'],
        help='Project ID (defaults to id specified in config file).',
    )

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
        default=config['LOCAL']['user'],
        help='User name to associate with instance.',
    )
    parser_create_instance.add_argument(
        '--instance',
        default=config['GCP']['instance_name'],
        help='Name to use for instance. Will append user name if necessary.',
    )
    parser_create_instance.add_argument(
        '--zone',
        default=config['GCP']['gcp_zone'],
        help='Zone in which to create instance.',
    )
    parser_create_instance.add_argument(
        '--machine-type',
        default=config['GCP']['machine_type'],
        help='Machine type. List possible machine types with "lab-gcp list-machine-types".',
    )
    parser_create_instance.add_argument(
        '--boot-disk-size',
        default=config['GCP']['boot_disk_size'],
        help='Size of boot disk in GB (at least 20).',
    )
    parser_create_instance.add_argument(
        '--image',
        default=config['GCP']['image'],
        help='Image to use in creating instance.',
    )

    # List instances subparser
    parser_list_instances = subargs.add_parser(
        c_LIST,
        help="List instances.",
    )
    parser_list_instances.add_argument(
        '--zone',
        default=config['GCP']['gcp_zone'],
        help='GCP zone to show instances for.',
    )

    # Stop instance subparser
    parser_stop_instance = subargs.add_parser(
        c_STOP,
        help="Stop running instance.",
    )
    parser_stop_instance.add_argument(
        '--user',
        default=config['LOCAL']['user'],
        help='User name to associate with instance.',
    )
    parser_stop_instance.add_argument(
        '--zone',
        default=config['GCP']['gcp_zone'],
        help='GCP zone.',
    )
    parser_stop_instance.add_argument(
        '--instance',
        default=config['GCP']['instance_name'],
        help='Name of instance to stop.',
    )
    # Delete instance subparser
    parser_delete_instance = subargs.add_parser(
        c_DELETE,
        help="Stop running instance.",
    )
    parser_delete_instance.add_argument(
        '--user',
        default=config['LOCAL']['USER'],
        help='User name to associate with instance.',
    )
    parser_delete_instance.add_argument(
        '--zone',
        default=config['GCP']['gcp_zone'],
        help='GCP zone.',
    )
    parser_delete_instance.add_argument(
        '--instance',
        default=config['GCP']['instance_name'],
        help='Name of instance to delete.',
    )

    # Start instance subparser
    parser_start_instance = subargs.add_parser(
        c_START,
        help="Start stopped instance.",
    )
    parser_start_instance.add_argument(
        '--user',
        default=config['LOCAL']['USER'],
        help='User name to associate with instance.',
    )
    parser_start_instance.add_argument(
        '--zone',
        default=config['GCP']['gcp_zone'],
        help='GCP zone.',
    )
    parser_start_instance.add_argument(
        '--instance',
        default=config['GCP']['instance_name'],
        help='Name of instance to start.',
    )

    # Set machine type subparser
    parser_set_machine = subargs.add_parser(
        c_SET_MACHINE,
        help="Set machine type of stopped instance.",
    )
    parser_set_machine.add_argument(
        '--user',
        default=config['LOCAL']['USER'],
        help='User name to associate with instance.',
    )
    parser_set_machine.add_argument(
        '--machine-type',
        default=config['GCP']['machine_type'],
        help='Machine type to set for instance. List possible machine types with "lab-gcp list-machine-types".',
    )
    parser_set_machine.add_argument(
        '--zone',
        default=config['GCP']['gcp_zone'],
        help='GCP zone.',
    )
    parser_set_machine.add_argument(
        '--instance',
        default=config['GCP']['instance_name'],
        help='Name of instance to start.',
    )

    # List machine types subparser
    parser_list_machines = subargs.add_parser(
        c_LIST_MACHINES,
        help="List available machine types for zone.",
    )
    parser_list_machines.add_argument(
        '--zone',
        default=config['GCP']['gcp_zone'],
        help='GCP zone.',
    )

    # Set time-managed label
    parser_set_time_label = subargs.add_parser(
        c_SET_TLABEL,
        help="Toggle time-managed label on instance. Turns time-management on by default.",
    )
    parser_set_time_label.add_argument(
        '--user',
        default=config['LOCAL']['USER'],
        help='User name to associate with instance.',
    )
    parser_set_time_label.add_argument(
        '--zone',
        default=config['GCP']['gcp_zone'],
        help='GCP zone.',
    )
    parser_set_time_label.add_argument(
        '--instance',
        default=config['GCP']['instance_name'],
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
        default=config['LOCAL']['USER'],
        help='User name to associate with instance.',
    )
    parser_upload_libs.add_argument(
        '--bucket',
        default=config['GCP']['bucket'],
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
        default=config['LOCAL']['lib_dir_sc'],
        help='Path to directory where libraries stored (defaults to /broad/macosko/data/libraries).',
    )

    # Upload directory to instance parser
    parser_upload_dir_inst = subargs.add_parser(
        c_UPLOAD_DIR_INST,
        help="Upload file or directory to GCP instance.",
    )
    parser_upload_dir_inst.add_argument(
        '--source-path',
        required=True,
        help='File path to data to upload.',
    )
    parser_upload_dir_inst.add_argument(
        '--dest-path',
        default=None,
        help='Destination path for data.',
    )
    parser_upload_dir_inst.add_argument(
        '--user',
        default=config['LOCAL']['USER'],
        help='User name to associate with instance.',
    )
    parser_upload_dir_inst.add_argument(
        '--zone',
        default=config['GCP']['gcp_zone'],
        help='GCP zone.',
    )
    parser_upload_dir_inst.add_argument(
        '--instance',
        default=config['GCP']['instance_name'],
        help='Name of instance to which to upload data.',
    )

    # Init parser
    parser_init = subargs.add_parser(
        c_INIT,
        help="Initialize default settings.",
    )

    return args

def main():

    parsed_args = create_parser().parse_args()

    if parsed_args.command == c_INIT:
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

    # Check for initialization
    check_init()

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
        # Generate full instance name
        final_name = parsed_args.instance
        if parsed_args.user not in parsed_args.instance:
            final_name = '-'.join([parsed_args.instance, parsed_args.user])
        curr_names = [inst['name'] for inst in instances['items']]
        if final_name in curr_names:
            raise RuntimeError('An instance with the name {} already exists. '.format(final_name) +
                               'Please select a different name.')

        # TODO: make sure instance name contains no slashes, other breaking chars
        res = create_instance(rstudio_passwd=parsed_args.rpass,
                              user=parsed_args.user,
                              name=parsed_args.instance,
                              project=parsed_args.project,
                              zone=parsed_args.zone,
                              machine_type=parsed_args.machine_type,
                              boot_disk_size=parsed_args.boot_disk_size,
                              image=parsed_args.image)
        final_name = res['targetLink'].split('/')[-1]
        # In case creation is slow
        time.sleep(5)
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
        print('Your instance {} is being started. This may take a minute.'.format(final_name))
        time.sleep(5)
        instances = list_instances(project=parsed_args.project)
        nat_ip = [item for item in instances['items']
                  if item['name'] == final_name][0]['networkInterfaces'][0]['accessConfigs'][0]['natIP']

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

        res = set_label(label_key='env',
                        label_value=label_value,
                        user=parsed_args.user,
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

    if parsed_args.command == c_UPLOAD_DIR_INST:
        # Set default destination
        if parsed_args.dest_path is None:
            dest_path = '/home/{}/'.format(parsed_args.user)

        # Generate full instance name
        final_name = parsed_args.instance
        if parsed_args.user not in parsed_args.instance:
            final_name = '-'.join([parsed_args.instance, parsed_args.user])

        # Could also do this with paramiko instead
        scp_args = ['gcloud', 'compute', 'scp', '--recurse', parsed_args.source_path,
                    '{}:{}'.format(final_name, dest_path), '--project', parsed_args.project,
                    '--zone', parsed_args.zone]
        call(scp_args)

        # gcloud logs directly to console

# CLI entry points
if __name__ == '__main__':
    main()

