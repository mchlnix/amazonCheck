#!/usr/bin/env python
# -*- coding: utf-8 -*-

from amazonCheckLib import get_info_for, get_time, shorten_amazon_link
from os.path import exists, expanduser
from time import ctime, time
from json import dumps, loads
from sys import argv, exit
from os import name


CONFIG_FILE = expanduser( '~/.amazonCheck.config' )
DATA_FILE = expanduser( '~/.amazonCheck.data' )
LOGFILE = expanduser( '~/.amazonCheck.log' )


SILENT = True
UPDATES_ONLY = False
VERBOSE = False

MIN_SLEEP_TIME = 60
MAX_SLEEP_TIME = 300


CONFIG_VARS = 5

def add_article( url ):
    data_file = open( DATA_FILE, 'a' )
    ( title, price ) = get_info_for( url )

    price = price

    #get_currency, get_price dann speichern und testen


    data_file.write( dumps( [ url, title,  ] ) )


def get_avg_price( prices ):
    avg = 0
    length = len( prices )

    for i in range( 2, length + 1 ):
        index = length - i
        avg += prices[ index ][0] * ( prices[ index + 1 ][1] - prices[ index ][1] )

    return avg / ( prices[ -1 ][1] - prices[0][1] )


def read_config_file():

    if not exists( CONFIG_FILE ):

        reset_config_file()

        return [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ]

    config_file = open( CONFIG_FILE, 'r' )

    options = loads( config_file.read() )

    logfile.write( get_time() + ' Read Config File at ' + CONFIG_FILE + '\n' )

    if type( options[ 0 ] ) != type( True ) or type( options[ 1 ] ) != type( True ) or type( options[ 2 ] ) != type( True ) or type( options[ 3 ] ) != type( 1 ) or type( options[ 3 ] ) != type( 1 ):

        reset_config_file()

        return [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ]
    else:
        return options


def reset_config_file():

    new_config_file = open( CONFIG_FILE, 'w' )

    options = [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ]

    new_config_file.write( dumps( options ) )

    new_config_file.close()

    logfile.write( get_time() + ' Reset Config File at ' + CONFIG_FILE + '\n' )


def write_config_file( options ):

    if type( options[ 0 ] ) != type( True ) or type( options[ 1 ] ) != type( True ) or type( options[ 2 ] ) != type( True ) or type( options[ 3 ] ) != type( 1 ) or type( options[ 3 ] ) != type( 1 ):

        config_file = open( CONFIG_FILE, 'w' )

        config_file.write( dumps( options ) )

        config_file.close()

    logfile.write( get_time() + ' Wrote to Config File at ' + CONFIG_FILE + '\n' )




if __name__ == '__main__':

    logfile = open( LOGFILE, 'a' )
    logfile.write( get_time() + ' -------------------------------' + '\n' )
    logfile.write( get_time() + ' Started Program' + '\n' )

    [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ] = read_config_file()

    if len( argv ) > 2:
        if argv[1] == '-a' or argv[1] == 'add':
            add_article( shorten_amazon_link( argv[2] ) )
            logfile.write( get_time() + ' Program halted after adding article' + '\n' )
            exit()



    if len( argv ) > 1:

        for argument in argv[ 1 : ]:

            logfile.write( get_time() + ' Program called with \'' + argument + '\'' + '\n' )

            if argument == '-s' or argument == '--silent':

                SILENT = True

            elif argument == '-v' or argument == '--verbose':

                VERBOSE == True

            elif argument == '-u' or argument == '--update-only':

                UPDATES_ONLY = True

            elif argument.find( '--min_sleep=' ) != -1:

                try:
                    MIN_SLEEP_TIME = float( argument[ 12 : ] )
                except ValueError:
                    logfile.write( get_time() + ' Given min_sleep argument was not a number' + '\n' )

            elif argument.find( '--min_sleep=' ) != -1:

                try:
                    MAX_SLEEP_TIME = float( argument[ 12 : ] )
                except ValueError:
                    logfile.write( get_time() + ' Given max_sleep argument was not a number' + '\n' )

            elif argument == '-u' or argument == '--update-only':

                UPDATES_ONLY = True

            else:

                logfile.write( get_time() + ' Illegal argument \'' + argument + '\' detected' + '\n' )
                continue

    #Read data [ link, title, currency, prices, ... ]

    if not exists( DATA_FILE ):
        logfile.write( get_time() + ' Data File does not exist' + '\n' )
        logfile.write( get_time() + ' Program halted' + '\n' )
        exit( 'Data File does not exist.' )

    logfile.write( get_time() + ' Data File is being read' + '\n' )

    data_file = open( DATA_FILE, 'r' )

    data = data.readlines()

    data_file.close()

    logfile.write( get_time() + ' Data is being processed' + '\n' )

    #Break up into links, titles and prices

    links = []
    titles = []
    currencies =[]
    prices = []

    for index in len( data ):
        info = loads( data[ index ] )

        links.append = data[ index ][0]
        titles.append = data[ index ][1]
        currencies.append = data[ index ][2]
        prices.append = data[ index ][ 3: ]

    try:

        while 1:
            sleeptime = MIN_SLEEP_TIME
            avgs = []
            mins = []
            maxs = []
            progs = []

            #Startzeit
            start_time = time()
            #Schleife mit get_info
            for index in len( links ):
                prices[ index ].append( ( get_info_for( links( index ) )[1], time() ) )
                #avg price
                avgs.append( get_avg_price( prices[ index ] ) )
                #min price
                #mins.append( get_min_price( prices[ index ] ) )
                #max price
                #maxs.append( get_max_price( prices[ index ] ) )
                #prog
                #progs.append( get_prognosis( prices[ index ] ) )
            #Endzeit
            end_time = time()
            #Differenz berechnen
            diff_time = end_time - start_time
            #Sleeptime berechnen
            if 2 * diff_time > MAX_SLEEP_TIME:
                sleeptime = MAX_SLEEP_TIME
            elif 2 * diff_time < MIN_SLEEP_TIME:
                sleeptime = MIN_SLEEP_TIME
            else:
                sleeptime = 2 * diff_time

            sleep( sleep_time )

    except KeyboardInterrupt:
        logfile.write( get_time() + ' Program halted by user' + '\n' )
        logfile.write( get_time() + ' Exited normally' + '\n' )
        exit()





    write_config_file( [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ] )

    logfile.write( get_time() + ' Exited normally' + '\n' )
    logfile.close()

