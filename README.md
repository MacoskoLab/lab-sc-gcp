# lab-sc-gcp
Python package enabling easy set up of GCP projects for lab-wide interactive single cell analysis.
Provides user-friendly CLI wrapper to allow simple interaction with compute and storage resources.
Relies on GCP images with RStudio Server and common single cell packages like Seurat and liger installed. 

* [Requirements](#requirements)
* [Installation](#installation)
    1. [Install Google-Cloud-SDK](#1-install-google-cloud-sdk)
    2. [Install the lab-sc-gcp package](#2-install-the-lab-sc-gcp-package)
    3. [Configure user defaults](#3-configure-user-defaults)
* [Basic Workflow](#basic-workflow)
    1. Create an instance with desired resources.
    2. Transfer your data. 
    3. Run interactive analyses.
    4. Stop your instance when you stop working.
    5. Resize your instance (if desired) and restart it when you're ready to continue.
* [Utilities](#utilities)
    * [`lab-gcp create-instance`](#lab-gcp-create-instance)
    * [`lab-gcp list-instances`](#lab-gcp-list-instances)
    * [`lab-gcp stop-instance`](#lab-gcp-stop-instance)
    * [`lab-gcp set-machine-type`](#lab-gcp-set-machine-type)
    * [`lab-gcp upload-libs`](#lab-gcp-upload-libs)
* [Bucket to instance transfer](#bucket-to-instance-transfer)
* [Time management exceptions](#time-management-exceptions)
* [Connecting to instances through SSH](#connecting-to-instances-through-ssh)

## Requirements

* Python3.x
* [Google-Cloud-SDK](https://cloud.google.com/sdk/install)
* Anaconda/[miniconda](https://docs.conda.io/en/latest/miniconda.html) (recommended)
* A Google Cloud billing [account](https://broad.io/billingaccountrequest) attached to a Broad cost object OR
* Edit permissions for compute/storage resources on an existing Google Cloud Project 
    * Ask someone in the lab to give you these permissions
* A GitHub account with collaborator access to this repo. Ask someone in the Macosko lab to add you.

## Installation
If you plan to work with single cell libraries (from 10x or another pipeline), you 
must also follow the secondary instructions for installing on a Broad cluster compute node.

### 1. Install Google-Cloud-SDK. 
* Configure your default project if you have one by running `gcloud init` after installation. 
* *On Broad compute:* Google-Cloud-SDK is available as a dotkit; activate by running:
```
use Google-Cloud-SDK
gcloud init
```
* After setting your default project, run `gcloud auth application-default login` and follow
the instructions for authentication. This will allow you to authenticate automatically later on.

### 2. Install the lab-sc-gcp package. 
It's recommended (but not required) to do this in a `conda` or other Python environment.
```
pip install git+https://github.com/MacoskoLab/lab-sc-gcp.git#egg=lab_sc_gcp
```
You may be asked to provide your GitHub credentials.
* *On Broad compute:* You must first create a `conda` environment and install inside:
```
use Anaconda3
conda create -n lab-sc-gcp python=3.6
# follow prompts above to create environment
# activate environment
source activate lab-sc-gcp
pip install git+https://github.com/MacoskoLab/lab-sc-gcp.git#egg=lab_sc_gcp
```
* You must activate this environment each time you want to access the package:
```
use Anaconda3
source activate lab-sc-gcp
```

### 3. Configure user defaults.
```
lab-gcp init 
# Follow instructions to set required defaults 
```
* You will be prompted to run this command if you skip it. You can set additional default 
values by modifying the `~/.lab-sc-gcp/config.ini` file created during this process.

Note the defaults that are provided:
```
[GCP]
GCP_PROJECT_ID =
BUCKET =     # eg macosko_data
INSTANCE_NAME = rstudio-sc
GCP_ZONE = us-central1-f
# 8 CPU, 52G RAM
MACHINE_TYPE = n1-highmem-8
# in GB
BOOT_DISK_SIZE = 200
# Image with R 3.5, Seurat 2.3.4, liger 0.5.0
IMAGE = rstudio-sc-small-3-5-seurat-2

[LOCAL]
USER =         # your Broad username
LIB_DIR_SC =   # for us, /broad/macosko/data/libraries
``` 

#### Note on selecting default project
Current Macosko Lab projects and corresponding cost objects can be viewed on the Computational Analysis 
Setup Guidelines. 

## Basic Workflow
### 1. Create an instance with desired resources. 
* Use the command `lab-gcp create-instance`. 
* Run `lab-gcp list-machine-types` to see the resources for different kinds of machines. 
* You must provide a password with the `--rpass` argument. 
* Access RStudio Server in your browser at the provided IP address (with Broad username and provided password).
* *Important:* If you're offsite, you must first connect to [VPN](https://intranet.broadinstitute.org/bits/service-catalog/networking/vpn), 
with the Z-Duo-Broad-NonSplit-VPN option, in order to access your instance online. 
* Note that all instance names have user name appended by default to allow us to distinguish
instances. 

### 2. Transfer your data. 
* For single cell count libraries, you must transfer your data first to a bucket, and then
to your instance (the second step uses `gsutil` utilities as described below.)
* Relevant commands are:
```
# upload one or more libraries to a bucket
lab-gcp upload_libs 
# upload a directory to an instance directly
lab-gcp upload-dir-instance
```
### 3. Run interactive analyses. 
* Remember to save your files and objects periodically. 
* Analyses can only be run when instances are on (not stopped).

### 4. Stop your instance when you stop working. (THIS SAVES US MONEY!) 
* Every instance will automatically be stopped at midnight every night 
(see Time Management Exceptions below). 
* You can also delete your instance, but that will cause you to lose the data on it.

### 5. Resize your instance (if desired) and restart it when you're ready to continue.
* You can change the machine type (and resources) of your instance with 
`lab-gcp set-machine-type`, and restart your instance with `lab-gcp start instance`. 

*Note:* Users are limited to two instances at a time by default. 

## Utilities

```
usage: lab-gcp 
positional arguments:
    create-instance     Create instance with specified parameters.
    list-instances      List instances.
    stop-instance       Stop running instance.
    delete-instance     Delete instance.
    start-instance      Start stopped instance.
    set-machine-type    Set machine type of stopped instance.
    list-machine-types  List available machine types for zone.
    set-time-label      Toggle time-managed label on instance. Turns time-
                        management on by default.
    upload-libs         Upload one or more single cell count libraries to
                        default bucket.
    upload-dir-instance
                        Upload file or directory to GCP instance.
    init                Initialize default settings.

optional arguments:
  -h, --help            show this help message and exit
  --project PROJECT     Project ID (defaults to id specified in config file).
```

#### `lab-gcp create-instance`

```
usage: lab-gcp create-instance [-h] --rpass RPASS [--user USER]
                              [--instance INSTANCE] [--zone ZONE]
                              [--machine-type MACHINE_TYPE]
                              [--boot-disk-size BOOT_DISK_SIZE]
                              [--image IMAGE]
optional arguments:
  -h, --help            show this help message and exit
  --rpass RPASS         Password to use for Rstudio Server.
  --user USER           User name to associate with instance.
  --instance INSTANCE   Name to use for instance. Will append user name if
                        necessary.
  --zone ZONE           Zone in which to create instance.
  --machine-type MACHINE_TYPE
                        Machine type. List possible machine types with "lab-
                        gcp list-machine-types".
  --boot-disk-size BOOT_DISK_SIZE
                        Size of boot disk in GB (at least 20).
  --image IMAGE         Image to use in creating instance.

```

#### `lab-gcp list-instances`

```
usage: lab-gcp list-instances [-h] [--zone ZONE]

optional arguments:
  -h, --help   show this help message and exit
  --zone ZONE  GCP zone to show instances for.
```

#### `lab-gcp stop-instance`

```
usage: lab-gcp stop-instance [-h] [--user USER] [--zone ZONE]
                            [--instance INSTANCE]

optional arguments:
  -h, --help           show this help message and exit
  --user USER          User name to associate with instance.
  --zone ZONE          GCP zone.
  --instance INSTANCE  Name of instance to stop.
```

#### `lab-gcp set-machine-type`

```
usage: lab-gcp set-machine-type [-h] [--user USER]
                               [--machine-type MACHINE_TYPE] [--zone ZONE]
                               [--instance INSTANCE]

optional arguments:
  -h, --help            show this help message and exit
  --user USER           User name to associate with instance.
  --machine-type MACHINE_TYPE
                        Machine type to set for instance. List possible
                        machine types with "lab-gcp list-machine-types".
  --zone ZONE           GCP zone.
  --instance INSTANCE   Name of instance to start.
```

#### `lab-gcp upload-libs`

```
usage: lab-gcp upload-libs [-h] [--user USER] [--bucket BUCKET] --libraries
                          LIBRARIES [--library-dir LIBRARY_DIR]

optional arguments:
  -h, --help            show this help message and exit
  --user USER           User name to associate with instance.
  --bucket BUCKET       Bucket to which to upload libraries.
  --libraries LIBRARIES
                        Name of library (not full path) to upload or path to
                        file containing library names. If file, libraries must
                        be listed one per line with no other separators.
  --library-dir LIBRARY_DIR
                        Path to directory where libraries stored (defaults to
                        /broad/macosko/data/libraries).
```


## Bucket to instance transfer 
Once you've uploaded single cell data to a bucket, the easiest way to transfer it to your
instance is with the [`gsutil`](https://cloud.google.com/storage/docs/gsutil/commands/cp) command. You can use the Terminal functionality of RStudio
(next to Console tab in browser RStudio window).

Here are some example commands for transferring single cell libraries from the `macosko_data`
bucket to the `/home/data/libraries` directory on your instance.

```
# transfer all available libraries
gsutil -m -cp -r gs://macosko_data/libraries/* /home/data/libraries/

# transfer a subset of libraries using wildcards (all BICCN libraries):
gsutil -m cp -r gs://macosko_data/libraries/*BICCN* /home/data/libraries

```
You can transfer data from your instance to the bucket in a similar way, just switch the 
order of the source and destination paths. 

*IMPORTANT NOTE:* When copying into a subdirectory in the bucket (which may or may not 
yet exist), you must include the trailing forward slash to avoid unintended behavior. 
For example, if john doe is trying to move something and create a new subdirectory 
called `johndoe` at the same time, he should do this: 
```
gsutil cp /home/johndoe/object.RDS gs://macosko_data/johndoe/
```
NOT THIS:
```
gsutil cp /home/johndoe/object.RDS gs://macosko_data/johndoe
```

## Time management exceptions

If you need to run an analysis overnight, you can toggle the label of your instance 
which determines whether it's turned off using the `lab-gcp set-time-label` command. 

For example, running this will set your default instance to unmanaged mode, and it 
will not turn off at midnight.
```
lab-gcp set-time-label --turn-off
```
If you do this, it's very important to toggle your instance back to managed mode the next
day (or as soon as your analysis is done).
```
# this turns the label back on 
lab-gcp set-time-label 
```

## Connecting to instances through SSH

You can connect to your instance via SSH with the following template command:
```
gcloud compute ssh --project <project-name> --zone us-central1-f <instance-name>
```
Note that you will need to be connected to the nonsplit VPN.