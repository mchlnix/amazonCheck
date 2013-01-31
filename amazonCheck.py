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




def main():

    #if exists( CONFIG_FILE ):
        #data = loads( open( CONFIG_FILE , 'r' ).read() )
#
        #if len( data ) == CONFIG_VARS:
#
        #else:
            #reset_config_file()



	return 0

if __name__ == '__main__':
	main()

