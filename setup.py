#! /usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
      name='lab_sc_gcp',
      version='0.1',
      description='Package enabling easy set up of GCP project for interactive single cell analysis',
      url='',
      author='Velina Kozareva',
      author_email='vkozarev@broadinstitute.org',
      license='MIT',
      packages=['lab_sc_gcp'],
      # package_dir={'lab_sc_gcp': 'lab_sc_gcp'},
      package_data={'lab_sc_gcp': ['startup/*']},
      install_requires=[
          'google-api-python-client',
          'google-cloud-storage',
      ],
      entry_points={
            'console_scripts': ['lab-gcp=lab_sc_gcp.cli:main'],
      },
      zip_safe=False
)