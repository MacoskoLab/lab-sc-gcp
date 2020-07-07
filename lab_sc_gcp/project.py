#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Functions for managing Google Cloud projects.

"""

from googleapiclient.discovery import build
from google.cloud import storage
from lab_sc_gcp.config.configure import *
from lab_sc_gcp.utilities import *
from pkg_resources import resource_filename
import time

config = get_config()

# TODO: Move to config and hide later
allowed_ips = ["69.173.112.0/21", "69.173.127.232/29", "69.173.127.128/26", "69.173.127.0/25", "69.173.127.240/28",
               "69.173.127.224/30", "69.173.127.230/31", "69.173.120.0/22", "69.173.127.228/32", "69.173.126.0/24",
               "69.173.96.0/20", "69.173.64.0/19", "69.173.127.192/27", "69.173.124.0/23"]

def create_project(
    project_id,
    billing_account,
    set_default=False,
):
    service = build('cloudresourcemanager', 'v1')
    projects = service.projects()

    # Note that user can only specify billing after creation
    # https://googleapis.github.io/google-api-python-client/docs/dyn/cloudresourcemanager_v1.projects.html#create
    req = projects.create(
        body={
            "projectId": project_id,
            'name': project_id,
            # Automatically places under user organization
        }
    )
    res = req.execute()
    # Prevent permissions errors
    time.sleep(10)

    # Add billing info
    service = build('cloudbilling', 'v1')
    projects = service.projects()

    # https://developers.google.com/resources/api-libraries/documentation/cloudbilling/v1/python/latest/cloudbilling_v1.projects.html
    req = projects.updateBillingInfo(
        name="projects/{}".format(project_id),
        body={
            "billingAccountName": "billingAccounts/{}".format(billing_account),
        }
    )
    res2 = req.execute()
    # TODO: check creation complete

    # Set as default if requested
    if set_default:
        config.set('GCP', 'GCP_PROJECT_ID', project_id)

        # Write new config
        with open(user_config, 'w') as configfile:
            config.write(configfile)
        print('Project {} set as default project.'.format(project_id))

    return [res, res2]

def create_bucket(
    name,
    project=config['GCP']['gcp_project_id'],
    location=config['GCP']['gcp_zone'],
    set_default=False,
):
    # Convert compute region zone to region (works for most zones)
    location = '-'.join(location.split('-')[:-1])

    storage_client = storage.Client()

    bucket = storage_client.create_bucket(
        bucket_or_name=name,
        project=project,
        location=location,
        predefined_acl='projectPrivate',  # This is default for all buckets anyway
    )

    # Set as default if requested
    if set_default:
        config.set('GCP', 'BUCKET', name)

        # Write new config
        with open(user_config, 'w') as configfile:
            config.write(configfile)
        print('Bucket {} set as default bucket.'.format(name))

    return bucket

def enable_apis(
    project=config['GCP']['gcp_project_id'],
    exclude_compute=False,
    exclude_functions=False,
):
    if not exclude_compute:
        call(['gcloud', 'services', 'enable', 'compute.googleapis.com',
              '--project', project])
        print('Enabled Compute Engine API.')
    if not exclude_functions:
        call(['gcloud', 'services', 'enable', 'cloudfunctions.googleapis.com',
              'pubsub.googleapis.com', 'cloudscheduler.googleapis.com',
              'appengine.googleapis.com', '--project', project])
        # Create app engine app in central region for now
        call(['gcloud', 'app', 'create', '--region', 'us-central', '--project', project])
        print('Enabled Cloud Functions,Pub/Sub and Scheduler APIs.')

def configure_network(
    project=config['GCP']['gcp_project_id'],
    region=config['GCP']['gcp_zone'],
):
    # Best practices outlined in https://dsp-security.broadinstitute.org/cloud-security/google-cloud-platform/securing-the-network
    service = build('compute', 'v1')
    firewalls = service.firewalls()

    # TODO: clean up error messages if configuration steps already done
    # First close default SSH and RDP access
    try:
        res = firewalls.delete(
            firewall='default-allow-rdp',
            project=project,
        ).execute()
    except Exception as e:
        print(e)

    try:
        res = firewalls.delete(
            firewall='default-allow-ssh',
            project=project,
        ).execute()
    except Exception as e:
        print(e)

    # Create a managed network and subnet
    networks = service.networks()
    req = networks.insert(
        project=project,
        body={
            "name": "managed",
            "autoCreateSubnetworks": True,
        }
    )
    try:
        res = req.execute()
        print("Managed network created.")
    except Exception as e:
        print(e)
    # Network needs some time to be ready
    time.sleep(30)

    # Convert compute region zone to region (works for most zones)
    region = '-'.join(region.split('-')[:-1])

    subnetworks = service.subnetworks()
    req = subnetworks.insert(
        project=project,
        region=region,
        body={
            "name": "managed-subnet",
            "network": "global/networks/managed",
            "ipCidrRange": "10.100.1.0/24",
            "enableFlowlogs": True,
        }
    )
    try:
        res = req.execute()
        print("Managed subnetwork created.")
    except Exception as e:
        print(e)

    # Create firewall rules for managed network (access to default RStudio, jupyter, and SSH ports)
    req = firewalls.insert(
        project=project,
        body={
            "name": "managed-allow-ssh",
            "network": "global/networks/managed",
            "allowed": {
                "IPProtocol": "tcp",
                "ports": ["22"],
            },
            "logConfig": {
                "enable": True,
            },
            "sourceRanges": allowed_ips,
        }
    )
    res = req.execute()
    print('SSH firewall rule created.')

    # Rstudio and jupyter
    req = firewalls.insert(
        project=project,
        body={
            "name": "managed-allow-rstudio",
            "network": "global/networks/managed",
            "allowed": {
                "IPProtocol": "tcp",
                "ports": ["8787", "8888"],
            },
            "logConfig": {
                "enable": True,
            },
            "sourceRanges": allowed_ips,
        }
    )
    res = req.execute()
    print("RStudio/jupyter firewall rule created.")

def create_schedule(
    shutdown_time="23,59",
    startup_time=None,
    zone=config['GCP']['gcp_zone'],
    project=config['GCP']['gcp_project_id']
):
    # For now use gcloud utilities here
    # Got source from https://github.com/GoogleCloudPlatform/nodejs-docs-samples
    # However, most recent version breaks functionality, so have rolled back json source
    source_dir = resource_filename('lab_sc_gcp', 'schedule')

    # Create instance shutdown and startup functions
    function_command = ['gcloud', 'pubsub', 'topics', 'create', 'stop-instance-event',
                        '--project', project]
    call(function_command)
    function_command = ['gcloud', 'functions', 'deploy', 'stopInstancePubSub', '--trigger-topic',
                        'stop-instance-event', '--project', project,
                        '--runtime', 'nodejs8', '--source', source_dir]
    call(function_command)
    # Start up
    function_command = ['gcloud', 'pubsub', 'topics', 'create', 'start-instance-event',
                        '--project', project]
    call(function_command)
    function_command = ['gcloud', 'functions', 'deploy', 'startInstancePubSub', '--trigger-topic',
                        'start-instance-event', '--project', project,
                        '--runtime', 'nodejs8', '--source', source_dir]
    call(function_command)

    # Schedule the jobs, every day by default
    # TODO: Add time-zone option instead of assuming east coast time
    stop_hr = shutdown_time.split(':')[0]
    stop_min = shutdown_time.split(':')[1]
    stop_args = ['gcloud', 'beta', 'scheduler', 'jobs', 'create', 'pubsub', 'shutdown-tm-instances',
                 '--project', project, '--schedule', '{} {} * * *'.format(stop_min, stop_hr),
                 '--topic', 'stop-instance-event',
                 '--message-body', '{{"zone":"{}", "label":"env=time-managed"}}'.format(zone),
                 '--time-zone', 'America/New_York']
    call(stop_args)

    if startup_time:
        start_hr = startup_time.split(':')[0]
        start_min = startup_time.split(':')[1]
        start_args = ['gcloud', 'beta', 'scheduler', 'jobs', 'create', 'pubsub', 'startup-tm-instances',
                      '--project', project, '--schedule', '{} {} * * *'.format(start_min, start_hr),
                      '--topic', 'start-instance-event',
                      '--message-body', '{{"zone":"{}", "label":"env=time-managed"}}'.format(zone),
                      '--time-zone', 'America/New_York']
        call(start_args)


# TODO: Create snapshot schedule that can be easily applied to all instance disks
