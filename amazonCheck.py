#!/usr/bin/env python
# -*- coding: utf-8 -*-

from amazonCheckLib import get_info_for
from os.path import expanduser, exists
from json import dumps, loads
from os import name

CONFIG_FILE = expanduser( '~/.amazonCheck.config' )


SILENT = True
UPDATES_ONLY = False
VERBOSE = False


CONFIG_VARS = 3


def reset_config_file():

    new_config_file = open( CONFIG_FILE, 'w' )

    options = [ SILENT, UPDATES_ONLY, VERBOSE ]

    new_config_file.write( dumps( options ) )

    new_config_file.close()


def read_config_file():

    config_file = open( CONFIG_FILE, 'r' )

    options = loads( config_file.read() )

    if type( options[ 0 ] ) != type( True ) or type( options[ 1 ] ) != type( True ) or type( options[ 2 ] ) != type( True ):
        return options
    else:
        reset_config_file()

        return [ SILENT, UPDATES_ONLY, VERBOSE ]


def write_config_file( options ):

    if type( options[ 0 ] ) != type( True ) or type( options[ 1 ] ) != type( True ) or type( options[ 2 ] ) != type( True ):
        config_file = open( CONFIG_FILE, 'w' )

        config_file.write( dumps( options ) )

        config_file.close()



def main():

    [ SILENT, UPDATES_ONLY, VERBOSE ] = read_config_file()

    return 0

if __name__ == '__main__':
	main()

