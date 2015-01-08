#!/usr/bin/env python
# coding=utf-8
from subprocess import call

call(['nosetests', '-v', '-s',
      '--with-coverage', '--cover-package=flask_resteasy', '--cover-branches',
      '--cover-erase', '--cover-html', '--cover-html-dir=tests/cover'])