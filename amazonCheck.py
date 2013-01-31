#!/usr/bin/env python
# -*- coding: utf-8 -*-

from amazonCheckLib import get_info_for, get_time
from os.path import expanduser, exists
from json import dumps, loads
from sys import argv
from os import name


CONFIG_FILE = expanduser( '~/.amazonCheck.config' )
DATA_FILE = expanduser( '~/.amazonCheck.data' )
LOGFILE = expanduser( '~/.amazonCheck.log' )


SILENT = True
UPDATES_ONLY = False
VERBOSE = False


CONFIG_VARS = 3


def read_config_file():

    if not exists( CONFIG_FILE ):

        reset_config_file()

        return [ SILENT, UPDATES_ONLY, VERBOSE ]

    config_file = open( CONFIG_FILE, 'r' )

    options = loads( config_file.read() )

    logfile.write( get_time() + ' Read Config File at ' + CONFIG_FILE + '\n' )

    if type( options[ 0 ] ) != type( True ) or type( options[ 1 ] ) != type( True ) or type( options[ 2 ] ) != type( True ):

        reset_config_file()

        return [ SILENT, UPDATES_ONLY, VERBOSE ]
    else:
        return options


def reset_config_file():

    new_config_file = open( CONFIG_FILE, 'w' )

    options = [ SILENT, UPDATES_ONLY, VERBOSE ]

    new_config_file.write( dumps( options ) )

    new_config_file.close()

    logfile.write( get_time() + ' Reset Config File at ' + CONFIG_FILE + '\n' )


def write_config_file( options ):

    if type( options[ 0 ] ) != type( True ) or type( options[ 1 ] ) != type( True ) or type( options[ 2 ] ) != type( True ):

        config_file = open( CONFIG_FILE, 'w' )

        config_file.write( dumps( options ) )

        config_file.close()

    logfile.write( get_time() + ' Wrote to Config File at ' + CONFIG_FILE + '\n' )


if __name__ == '__main__':

    logfile = open( LOGFILE, 'a' )
    logfile.write( get_time() + ' -------------------------------' + '\n' )
    logfile.write( get_time() + ' Started Program' + '\n' )

    [ SILENT, UPDATES_ONLY, VERBOSE ] = read_config_file()


    if len( argv ) > 1:

        for argument in argv[ 1 : ]:

            if argument == '-s' or argument == '--silent':
                SILENT = True
            elif argument == '-v' or argument == '--verbose':
                VERBOSE == True
            elif argument == '-u' or argument == '--update-only':
                UPDATES_ONLY = True
            else:
                logfile.write( get_time() + ' Illegal argument \'' + argument + '\' detected' + '\n' )
                continue

            logfile.write( get_time() + ' Program called with \'' + argument + '\'' + '\n' )








    logfile.write( get_time() + ' Exited normally' + '\n' )
    logfile.close()

