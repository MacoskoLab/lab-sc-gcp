#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Helper functions for lab_sc_gcp module.
"""

def get_full_inst_name(name, user):
    # Append user to instance name if necessary
    if user not in name:
        name = '{}-{}'.format(name, user)
    return name

def confirm(question):
    while True:
        answer = input(question + ' (y/n): ').lower().strip()
        if answer in ('y', 'yes', 'n', 'no'):
            return answer in ('y', 'yes')