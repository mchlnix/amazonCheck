#!/usr/bin/python2.7 -u
# -*- coding: utf-8 -*-

from os import name

if name == 'posix':
    BOLD_WHITE = '\033[1;97m'
    GRAY = '\033[90m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    LIGHT_BLUE = '\033[96m'
    NOCOLOR = '\033[0m'

else:
    BOLD_WHITE = ''
    GRAY = ''
    RED = ''
    GREEN = ''
    YELLOW = ''
    BLUE = ''
    PURPLE = ''
    LIGHT_BLUE = ''
    NOCOLOR = ''

