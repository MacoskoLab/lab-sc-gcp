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

def confirm(prompt):
    while True:
        answer = input(prompt + ' (y/n): ').lower().strip()
        if answer in ('y', 'yes', 'n', 'no'):
            return answer in ('y', 'yes')

def input_cv(prompt, controlled_values=None):
    inputval = input(prompt).strip()
    if controlled_values and inputval not in controlled_values:
        inputval = input_cv("Value not included in list of controlled values. Try again: ",
                            controlled_values=controlled_values)
        return inputval
    else:
        return inputval