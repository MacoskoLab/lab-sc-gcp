#!/bin/bash

# Add user if necessary
id '${USER}' >/dev/null 2>&1
if [ $? -eq 1 ] ; then
   adduser --disabled-password --gecos '' '${USER}'
fi
# Set password for user (for rstudio)
echo '${USER}:${R_PASS}' | chpasswd
usermod -a -G staff '${USER}'
usermod -a -G google-sudoers '${USER}'