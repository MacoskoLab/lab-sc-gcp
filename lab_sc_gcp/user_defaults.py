#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Global defaults for Google Cloud Project interaction.
"""

# Default settings and names
USER="vkozarev"
GCP_PROJECT_ID = "velina-208320"
GCP_ZONE = "us-central1-f"
MACHINE_TYPE = "n1-highmem-8"  # 8 CPU, 52G RAM
BOOT_DISK_SIZE = "200"  # in GB
INSTANCE_NAME = "rstudio-sc2"

GCP_INSTANCE_SCOPES = "default,bigquery,cloud-platform,storage-rw"
IMAGE_NAME = "rstudio-sc-basic-small-2"
LIB_DIR_SC = "/broad/macosko/data/libraries"
BUCKET = "macosko_data"
TO = "data/"