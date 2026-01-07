#!/usr/bin/env python

import os
import sys
from setuptools import setup
os.listdir

setup(
   name='as7327_56x',
   version='1.0',
   description='Module to initialize Accton AS7327-56X platforms',

   packages=['as7327_56x'],
   package_dir={'as7327_56x': 'as7327_56x/classes'},
)

