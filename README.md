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
    1. [Create an instance with default resources](#1-create-an-instance-with-default-resources).
    2. [Transfer your data](#2-transfer-your-data). 
    3. [Run interactive analyses](#3-run-interactive-analyses)
    4. [Stop your instance when you stop working](#4-stop-your-instance-when-you-stop-working-this-saves-us-money)
    5. [Resize your instance (if desired) and restart it when you're ready to continue](#5-resize-your-instance-if-desired-and-restart-it-when-youre-ready-to-continue)
* [Utilities](#utilities)
    * [`lab-gcp create-instance`](#lab-gcp-create-instance)
    * [`lab-gcp list-instances`](#lab-gcp-list-instances)
    * [`lab-gcp stop-instance`](#lab-gcp-stop-instance)
    * [`lab-gcp stop-instance`](#lab-gcp-start-instance)
    * [`lab-gcp set-machine-type`](#lab-gcp-set-machine-type)
    * [`lab-gcp upload-libs`](#lab-gcp-upload-libs)
    * [`lab-gcp download-from-inst`](#lab-gcp-download-from-inst)
* [Bucket to instance transfer](#bucket-to-instance-transfer)
* [Time management exceptions](#time-management-exceptions)
* [Connecting to instances through SSH](#connecting-to-instances-through-ssh)
* [Creating and configuring new projects](#creating-and-configuring-new-projects)

## Requirements

* Python3.x
* [Google-Cloud-SDK](https://cloud.google.com/sdk/install)
* A Google Cloud billing [account](https://broad.io/billingaccountrequest) attached to a Broad cost object OR
* Edit permissions for compute/storage resources on an existing Google Cloud Project 
    * Ask someone in the lab to give you these permissions
* A GitHub account with collaborator access to this repo. Ask someone in the Macosko lab to add you.
* Anaconda/[miniconda](https://docs.conda.io/en/latest/miniconda.html) (recommended)
* Read access to the Macosko Lab Computational guidelines document (ask to be given access as 
several private lab-specific settings are explained there)

## Installation
If you plan to work with or upload single cell libraries (from 10x or another pipeline), you 
must also follow the secondary instructions for installing on a Broad cluster compute node,
in addition to instructions for your local machine.

### 1. Install Google-Cloud-SDK. 
* Follow your platform specific installation instructions from the link above. Then configure
your default project if you have one by running the following:
```
gcloud init
```
* Check the computatational guidelines doc for information about Macosko lab projects.  
* *On Broad compute:* Google-Cloud-SDK is available as a dotkit; activate it and set your defaults with:
```
use Google-Cloud-SDK
gcloud init
```
* After setting your default project, run 
```
gcloud auth application-default login --disable-quota-project
``` 
and follow the instructions for authentication. This will allow you to authenticate automatically later on.

### 2. Install the lab-sc-gcp package. 
It's recommended (but not required) to do this in a `conda` or other Python environment (see Broad compute
instructions for an example of how to create a conda environment).
```
pip install git+https://github.com/MacoskoLab/lab-sc-gcp.git#egg=lab_sc_gcp
```
You may be asked to provide your GitHub credentials.
* *On Broad compute:* You *must* first create a `conda` environment and install inside:
```
use Anaconda3
conda create -n lab-sc-gcp python=3.6
# follow prompts above to create environment
# activate environment
source activate lab-sc-gcp
pip install git+https://github.com/MacoskoLab/lab-sc-gcp.git#egg=lab_sc_gcp
```
* When you first create the environment, it's recommended you do it from an interactive UGER node. 
* You must activate this environment each time you want to access the package:
```
use Anaconda3
source activate lab-sc-gcp
```

### 3. Configure user defaults.
Next you will configure required user defaults, including default project and bucket. 
```
lab-gcp init 
# Follow instructions to set required defaults 
```
* Check the guidelines document for additional instructions on how to set your defaults. 
You can set additional (non-required) default values by modifying the `~/.lab-sc-gcp/config.ini` 
file created during this process.

Note the defaults that are provided by the installation:
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
# Source project for images
IMAGE_PROJECT =
# Name of snapshot schedule to attach to instance disks
SNAPSHOT_SCHEDULE = daily-schedule

[LOCAL]
USER =         # your Broad username
LIB_DIR_SC =   # for us, /broad/macosko/data/libraries
``` 

#### Note on selecting default project and other values
Current Macosko Lab projects and corresponding cost objects, plus other recommendations,
can be viewed on the Computational Guidelines document. 

## Basic Workflow
Once you have the package installed, you can quickly get started with this basic workflow.
### 1. Create an instance with default resources. 
```
lab-gcp create-instance --rpass <new_password>
```
* By default, instances are created with a machine type and disk size as described in your config file. You can also 
run `lab-gcp list-machine-types` to see the resources for different kinds of machines. 
* You must provide a password with the `--rpass` argument. 
* Access RStudio Server in your browser at the provided IP address (with Broad username and new password).
* *Important:* If you're offsite, you must first connect to [VPN](https://intranet.broadinstitute.org/bits/service-catalog/networking/vpn), 
with the Z-Duo-Broad-NonSplit-VPN option, in order to access your instance online. 
* Note that all instance names have user name appended by default to allow us to distinguish
instances (for example, user jdoe would have an instance named `rstudio-sc-jdoe` by default). 

### 2. Transfer your data. 
* For single cell count libraries, you must transfer your data first to a bucket, and then
to your instance (the second step uses [`gsutil`](#bucket-to-instance-transfer) utilities as described below.)
* Relevant commands are:
```
# upload one or more libraries to a bucket
lab-gcp upload-libs 
# upload a directory to an instance directly
lab-gcp upload-dir-instance
```
You can easily upload multiple libraries with a single command by passing a path to a file that
lists the libraries. For example, if file `/path/to/lib_names.txt` looks like this:
```
library_1_name
library_2_name
      .
      .
```
you can upload these libraries to your default bucket with:
```
lab-gcp upload-libs --libraries /path/to/lib_names.txt
```
Note that this command uploads to the `libraries` directory in your bucket.

### 3. Run interactive analyses. 
* Remember to save your files and objects periodically. 
* Analyses can only be run when instances are on (not stopped).

### 4. Stop your instance when you stop working. (THIS SAVES US MONEY!) 
```
# Stop default instance (eg. rstudio-sc-jdoe for user jdoe)
lab-gcp stop-instance
```
* Every instance will also automatically be stopped at midnight every night 
(see [Time Management Exceptions](#time-management-exceptions) below). Note that this may cause some data loss if you have not saved your analyses.
* You can also delete your instance, but that will cause you to lose the data on it.

### 5. Resize your instance (if desired) and restart it when you're ready to continue.
* You can change the machine type (and resources) of your instance with 
`lab-gcp set-machine-type`, and restart your instance with `lab-gcp start-instance`.
For example, to switch your instance to a machine type with 30G RAM:
```
lab-gcp set-machine-type --machine-type n1-standard-8 
lab-gcp start-instance
``` 

*Note:* Users are limited to two instances at a time by default. 

## Utilities

```
usage: lab-gcp 
positional arguments:
    init                Initialize (or reset) primary default configuration
                        settings (user, project, bucket, single cell library
                        directory).
    create-project      Create new Google Cloud project.
    create-bucket       Create new Google Cloud bucket associated with
                        project.
    enable-apis         Enable APIs relevant for resource manipulation.
    configure-network   Configure new network and subnetwork for increased GCE
                        security.
    create-schedule     Create shutdown (and startup if desired) schedule for
                        instances.
    create-instance     Create instance with specified parameters.
    list-instances      List instances.
    stop-instance       Stop running instance.
    delete-instance     Delete instance permanently.
    start-instance      Start stopped instance.
    set-machine-type    Set machine type of stopped instance.
    list-machine-types  List available machine types for zone.
    set-time-label      Toggle time-managed label on instance. Turns time-
                        management on by default.
    upload-libs         Upload one or more single cell count libraries to
                        default bucket. Currently accepts 10x count outputs or
                        slide-seq pipeline outputs.
    upload-dir-instance
                        Upload file or directory to GCP instance.
    download-from-inst  Download file or directory from GCP instance.
    
optional arguments:
  -h, --help            show this help message and exit
  --project PROJECT     Project ID (defaults to project specified in config
                        file). Flag applies to all subcommands.

```

#### `lab-gcp create-instance`

```
usage: lab-gcp create-instance [-h] --rpass RPASS [--user USER]
                              [--instance INSTANCE] [--zone ZONE]
                              [--machine-type MACHINE_TYPE]
                              [--boot-disk-size BOOT_DISK_SIZE]
                              [--image IMAGE] [--image-project IMAGE_PROJECT]

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
  --image IMAGE         Name of image to use in creating instance.
  --image-project IMAGE_PROJECT
                        Source project for image to use in creating instance.

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

#### `lab-gcp start-instance`

```
usage: lab-gcp start-instance [-h] [--user USER] [--zone ZONE]
                            [--instance INSTANCE]

optional arguments:
  -h, --help           show this help message and exit
  --user USER          User name to associate with instance.
  --zone ZONE          GCP zone.
  --instance INSTANCE  Name of instance to start.
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
usage: lab-gcp upload-libs [-h] [--bucket BUCKET] --libraries LIBRARIES
                          [--library-dir LIBRARY_DIR]

optional arguments:
  -h, --help            show this help message and exit
  --bucket BUCKET       Bucket to which to upload libraries."gs://" prefix is
                        not necessary.
  --libraries LIBRARIES
                        Name of library (not full path) to upload or path to
                        file containing library names. If file, libraries must
                        be listed one per line with no other separators.
  --library-dir LIBRARY_DIR
                        Path to directory where libraries stored (defaults to
                        /broad/macosko/data/libraries).
```

#### `lab-gcp download-from-inst`

```
usage: lab-gcp download-from-inst [-h] --source-path SOURCE_PATH
                                 [--dest-path DEST_PATH] [--user USER]
                                 [--zone ZONE] [--instance INSTANCE]

optional arguments:
  -h, --help            show this help message and exit
  --source-path SOURCE_PATH
                        File path (on instance) to data to download.
  --dest-path DEST_PATH
                        Destination for download files (defaults to current
                        directory).
  --user USER           User name to associate with instance.
  --zone ZONE           GCP zone.
  --instance INSTANCE   Name of instance from which to download data.

```


## Bucket to instance transfer 
Once you've uploaded single cell data to a bucket, the easiest way to transfer it to your
instance is with the [`gsutil`](https://cloud.google.com/storage/docs/gsutil/commands/cp) command. You can use the Terminal functionality of RStudio
(next to the Console tab on your RStudio page).

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
Note that you will need to be connected to the nonsplit VPN in order to connect.
This command relies on the Google-Cloud-SDK CLI (so if you have your default project specified
you may not need to explicitly list your project in the command).

## Creating and configuring new projects

You can create and easily configure new projects for interactive instance use if
you have user access to a billing account. To set up a new project, run the following:
```
# Create new project and set it as your default
lab-gcp --project NEW_ID create-project --billing-account XXXXXX-XXXXXX-XXXXXX --set-default
# Create default bucket inside new project
lab-gcp create-bucket --name NEW_BUCKET --set-default
# Enable necessary APIs for project
lab-gcp enable-apis
# Configure network and firewall rules for project (as recommended by Broad)
# This allows incoming traffic on default ports for RStudio Server and Jupyter
lab-gcp configure-network
# Create midnight shutdown schedule for all time-managed instances in default zone
lab-gcp create-schedule
```

After your project is set up, grant other users the minimum necessary permissions
to create and manage their own instances in the project (via the Google Cloud console).

One additional step you may need to take for a new project (if you wish to have storage read/write 
access to buckets in another project), is to grant storage read/write access for existing projects to the compute engine
service account of your new project. 