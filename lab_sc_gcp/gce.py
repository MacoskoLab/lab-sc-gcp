#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Functions for managing Google Compute Engine (GCE) resources.

Code referenced from Deverman lab pipeline repo (author Albert Chen).
"""
from googleapiclient.discovery import build
from pkg_resources import resource_filename
from lab_sc_gcp.config.configure import *
from lab_sc_gcp.utilities import *

config = get_config()

def create_instance(
    rstudio_passwd,
    user=config['LOCAL']['user'],
    name=config['GCP']['instance_name'],
    project=config['GCP']['gcp_project_id'],
    zone=config['GCP']['gcp_zone'],
    machine_type=config['GCP']['machine_type'],
    boot_disk_size=config['GCP']['boot_disk_size'],
    image=config['GCP']['image'],
    disk_type='pd-standard',
):
    """

    :param rstudio_passwd:
    :param user:
    :param name:
    :param project:
    :param zone:
    :param machine_type:
    :param boot_disk_size:
    :param image:
    :param disk_type:
    :return:
    """
    # Read basic start-up script
    with open(resource_filename('lab_sc_gcp', 'startup/script_template.sh'), 'r') as f:
        startup_script = f.read()
        startup_script = startup_script.replace("${USER}", user)
        startup_script = startup_script.replace("${R_PASS}", rstudio_passwd)

    # Append user to instance name if necessary
    name = get_full_inst_name(name, user)

    # http://googleapis.github.io/google-api-python-client/docs/dyn/compute_v1.html
    service = build('compute', 'v1')
    instances = service.instances()

    # http://googleapis.github.io/google-api-python-client/docs/dyn/compute_v1.instances.html#insert
    req = instances.insert(
        project=project,
        zone=zone,
        body={
            "labels": {
                "env": "time-managed",  # shuts off every night at midnight
                "owner": user,          # keep track of who's using compute resources
            },
            'scheduling': {
                'preemptible': False,
                'automaticRestart': False,
                'onHostMaintenance': 'MIGRATE'
            },
            # 'minCpuPlatform': 'Intel Skylake',
            'serviceAccounts': [{
                'scopes': [
                    # Allows instance to manage itself and other instances
                    'https://www.googleapis.com/auth/compute',
                    # Allows instance to manage storage engine (bucket) resources
                    'https://www.googleapis.com/auth/devstorage.full_control',
                    # For logging to stackdriver
                    'https://www.googleapis.com/auth/logging.write',
                    'https://www.googleapis.com/auth/monitoring',
                    'https://www.googleapis.com/auth/monitoring.write'
                ],
                # Defaults to basic compute engine service account
            }],
            # IP access
            'networkInterfaces': [{
                'network': 'global/networks/managed',
                'accessConfigs': [{
                    'name': 'External NAT',
                    'networkTier': 'PREMIUM',  # STANDARD or PREMIUM
                    "kind": "compute#accessConfig",
                    "type": "ONE_TO_ONE_NAT",
                }],
                # 'networkIP': '', # IPv4 internal IP address. If not specified by the user,
                # an unused internal IP is assigned by the system.
                # 'fingerprint': '',
                'subnetwork': '/regions/us-central1/subnetworks/managed',
            }],
            # 'hostname': hostname,
            'metadata': {
                'items': [
                    {
                        'key': 'startup-script',
                        'value': startup_script,
                    }
                ]
                # 'fingerprint': '' # get fingerprint??
            },
            'deletionProtection': False,
            'canIpForward': False,
            'description': "",
            'tags': {
                # 'allow-http' is the name of a custom firewall rule
                'items': ['allow-http', ],
            },
            # 'labelFingerprint': ''
            # in the format: zones/<zone>/machineTypes/<machine-type>
            # To create a custom machine type, provide a URL to a machine type in the following format,
            # where CPUS is 1 or an even number up to 32 (2, 4, 6, ... 24, etc), and MEMORY is the total memory
            # for this instance. Memory must be a multiple of 256 MB and must be supplied in MB
            # (e.g. 5 GB of memory is 5120 MB):
            # zones/zone/machineTypes/custom-CPUS-MEMORY
            # For example: zones/us-central1-f/machineTypes/custom-4-5120
            'machineType': 'zones/{zone}/machineTypes/{machine_type}'.format(zone=zone, machine_type=machine_type),
            'name': name,
            'disks': [
                {
                    # 'diskEncryptionKey': '', # If we ever encrypt our disk
                    # 'deviceName': '', # For persistent disks
                    # Parameters for a new disk that will be created alongside the instance
                    # Mutually exclusive with the "source" parameter
                    'initializeParams': {
                        # 'sourceSnapshot': '', # Use a snapshot to create this disk
                        # 'diskName': '', # Unique disk name - will be generated if not provided
                        # 'description: '', # Optional disk description
                        # 'labels': { 'key': 'value' }, # Optional labels for this disk
                        # Disk type choices:
                        # pd-standard: disk drive, standard i/o
                        # pd-ssd: solid-state drive
                        # local-ssd: solid-state drive, directly wired to the hardware. very fast
                        # Specify with the partial URL: zones/<zone>/diskTypes/<diskType>
                        'diskType': 'zones/{zone}/diskTypes/{disk_type}'.format(zone=zone, disk_type=disk_type),
                        'diskSizeGb': boot_disk_size,
                        # You can also specify a custom image by its image family,
                        # which returns the latest version of the image in that family.
                        # Replace the image name with family/family-name:
                        # global/images/family/my-image-family
                        #
                        # Use the specified custom image.
                        'sourceImage': 'global/images/{}'.format(image)
                    },
                    'autoDelete': True,  # Delete the disk when the instance is deleted
                    'boot': True,  # This is a boot disk
                    'mode': 'READ_WRITE',  # READ_ONLY or READ_WRITE
                    'interface': 'SCSI',  # SCSI or NVME. Only local SSDs can use NVME
                    'type': 'PERSISTENT',  # SCRATCH or PERSISTENT
                    # 'source': '' # Full or partial URL to an existing disk instance
                },
            ]  # END DISKS
        }  # END BODY
    )  # END INSERT

    res = req.execute()

    return res

def list_instances(
    project=config['GCP']['gcp_project_id'],
    zone=config['GCP']['gcp_zone'],
):
    # http://googleapis.github.io/google-api-python-client/docs/dyn/compute_v1.html
    service = build('compute', 'v1')
    instances = service.instances()

    # http://googleapis.github.io/google-api-python-client/docs/dyn/compute_v1.instances.html#list
    req = instances.list(project=project, zone=zone)
    res = req.execute()
    # print(json.dumps(res, sort_keys=True, indent=4))
    return res

def stop_instance(
    user=config['LOCAL']['user'],
    name=config['GCP']['instance_name'],
    project=config['GCP']['gcp_project_id'],
    zone=config['GCP']['gcp_zone'],
):
    # Add user to instance name if necessary
    if user not in name:
        name = '-'.join([name, user])

    service = build('compute', 'v1')
    instances = service.instances()

    req = instances.stop(project=project,
                         zone=zone,
                         instance=name)
    res = req.execute()

    return res

def delete_instance(
    user=config['LOCAL']['user'],
    name=config['GCP']['instance_name'],
    project=config['GCP']['gcp_project_id'],
    zone=config['GCP']['gcp_zone'],
):
    # Add user to instance name if necessary
    if user not in name:
        name = '-'.join([name, user])

    service = build('compute', 'v1')
    instances = service.instances()

    req = instances.delete(project=project,
                           zone=zone,
                           instance=name)
    res = req.execute()

    return res

def start_instance(
    user=config['LOCAL']['user'],
    name=config['GCP']['instance_name'],
    project=config['GCP']['gcp_project_id'],
    zone=config['GCP']['gcp_zone'],
):
    # Add user to instance name if necessary
    if user not in name:
        name = '-'.join([name, user])

    service = build('compute', 'v1')
    instances = service.instances()

    req = instances.start(project=project,
                          zone=zone,
                          instance=name)
    res = req.execute()

    return res

def set_machine_type(
    user=config['LOCAL']['user'],
    machine_type=config['GCP']['machine_type'],
    name=config['GCP']['instance_name'],
    project=config['GCP']['gcp_project_id'],
    zone=config['GCP']['gcp_zone'],
):
    # Add user to instance name if necessary
    if user not in name:
        name = '-'.join([name, user])

    service = build('compute', 'v1')
    instances = service.instances()

    req = instances.setMachineType(
        project=project,
        zone=zone,
        instance=name,
        body={
            "machineType": 'zones/{zone}/machineTypes/{machine_type}'.format(zone=zone,
                                                                             machine_type=machine_type),
        }
    )
    res = req.execute()

    return res

def set_label(
    label_key,
    label_value,
    user=config['LOCAL']['user'],
    name=config['GCP']['instance_name'],
    project=config['GCP']['gcp_project_id'],
    zone=config['GCP']['gcp_zone'],
):
    # Add user to instance name if necessary
    if user not in name:
        name = '-'.join([name, user])

    service = build('compute', 'v1')
    instances = service.instances()

    # Get label fingerprint as it is required
    req = instances.get(project=project,
                        zone=zone,
                        instance=name)
    res = req.execute()
    labels = res['labels']
    label_fingerprint = res['labelFingerprint']
    # Set new label value
    labels[label_key] = label_value

    req = instances.setLabels(
        project=project,
        zone=zone,
        instance=name,
        body={
            "labelFingerprint": label_fingerprint,
            "labels": labels,
        }
    )
    res = req.execute()

    return res
