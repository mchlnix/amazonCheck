#!/usr/bin/python -u
# -*- coding: utf-8 -*-

from amazonCheckLib import get_info_for, get_time, shorten_amazon_link
from os.path import exists, expanduser
from time import ctime, time, sleep
from json import dumps, loads
from sys import argv, exit
from re import search
from os import name


CONFIG_FILE = expanduser( '~/.amazonCheck.config' )
DATA_FILE = expanduser( '~/.amazonCheck.data' )
LOGFILE = expanduser( '~/.amazonCheck.log' )


SILENT = True
UPDATES_ONLY = False
VERBOSE = False


MIN_SLEEP_TIME = 180
MAX_SLEEP_TIME = 300


CONFIG_VARS = 5


def add_article( url ):
    data_file = open( DATA_FILE, 'a' )
    ( title, currency, price ) = get_info_for( url )

    try:
        data_file.write( dumps( [ url, title, currency, [ [ price, time() ] ] ] ) )
    except UnicodeDecodeError:
        data_file.write( dumps( [ url, 'Encoutered error', currency, [ [ price, time() ] ] ] ) )

    data_file.close()


def get_avg_price( price_list ):
    avg = 0
    length = len( price_list )

    if length == 1:
        return price_list[0][1]

    div_time = price_list[ -1 ][1] - price_list[0][1]

    for i in range( 2, length + 1 ):

        index = length - i

        if price_list[ index ][0] == 'N/A':
            div_time -= price_list[ index + 1 ][1] - price_list[ index ][1]
            continue

        avg += price_list[ index ][0] * ( price_list[ index + 1 ][1] - price_list[ index ][1] )

    return avg / div_time


def print_result( links, titles, currency, prices ):

    for index in range( 0, len( links ) ):

        if len( prices ) == 1:
            avgs.append( get_avg_price( prices[ index ] ) )
            mins.append( get_min_price( prices[ index ] ) )
            maxs.append( get_max_price( prices[ index ] ) )
            #progs.append( get_prognosis( prices[ index ] ) )
            print( '' )


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


def read_data_file():
    if not exists( DATA_FILE ):
        logfile.write( get_time() + ' Data File does not exist' + '\n' )
        logfile.write( get_time() + ' Program halted' + '\n' )
        exit( 'Data File does not exist.' )

    logfile.write( get_time() + ' Data File is being read' + '\n' )

    data_file = open( DATA_FILE, 'r' )

    data = data_file.readlines()

    data_file.close()

    logfile.write( get_time() + ' Data is being processed' + '\n' )

    #Break up into links, titles and prices

    links = []
    titles = []
    currencies =[]
    prices = []

    for index in range( 0,  len( data ) ):
        info = loads( data[ index ] )

        links.append( info[0] )
        titles.append( info[1] )
        currencies.append( info[2] )
        prices.extend( info[ 3: ] )

    return ( links, titles, currencies, prices )





if __name__ == '__main__':

    logfile = open( LOGFILE, 'a' )
    logfile.write( get_time() + ' -------------------------------' + '\n' )
    logfile.write( get_time() + ' Started Program' + '\n' )

    [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ] = read_config_file()

    if len( argv ) == 2 and argv[1] == 'show':
        ( links, titles, currencies, prices ) = read_data_file()

        print_list( links, titles, currencies, prices )


    if len( argv ) > 2:
        if argv[1] == '-a' or argv[1] == 'add':
            add_article( shorten_amazon_link( argv[2] ) )
            logfile.write( get_time() + ' Program halted after adding article' + '\n' )
            exit()


    write_config = False

    if len( argv ) > 1:

        for argument in argv[ 1 : ]:

            logfile.write( get_time() + ' Program called with \'' + argument + '\'' + '\n' )

            if argument == '-s' or argument == '--silent':

                SILENT = True

                write_config = True

            elif argument == '-v' or argument == '--verbose':

                VERBOSE == True

                write_config = True

            elif argument == '-u' or argument == '--update-only':

                UPDATES_ONLY = True

                write_config = True

            elif argument.find( '--min_sleep=' ) != -1:

                try:
                    MIN_SLEEP_TIME = float( argument[ 12 : ] )

                    write_config = True

                except ValueError:
                    logfile.write( get_time() + ' Given min_sleep argument was not a number' + '\n' )

            elif argument.find( '--min_sleep=' ) != -1:

                try:
                    MAX_SLEEP_TIME = float( argument[ 12 : ] )

                    write_config = True

                except ValueError:
                    logfile.write( get_time() + ' Given max_sleep argument was not a number' + '\n' )

            else:

                logfile.write( get_time() + ' Illegal argument \'' + argument + '\' detected' + '\n' )
                continue

        if write_config:
            write_config_file( [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ] )

    #Read data [ link, title, currency, prices, ... ]

    ( links, titles, currencies, prices ) = read_data_file()

    runs = 0

    try:

        logfile.write( get_time() + ' Starting main loop' + '\n' )
        logfile.close()

        while 1:
            runs = runs + 1

            logfile = open( LOGFILE, 'a' )
            logfile.write( get_time() + ' Starting run ' + str( runs ) + ':' + '\n' )

            sleeptime = MIN_SLEEP_TIME
            avgs = []
            mins = []
            maxs = []
            progs = []

            #Startzeit
            start_time = time()
            #Schleife mit get_info
            logfile.write( get_time() + '   Getting info' + '\n' )
            for index in range( 0, len( links ) ):
                prices[ index ].append( [ get_info_for( links[ index ] )[2], time() ] )
                #avg price
                #min price
                #mins.append( get_min_price( prices[ index ] ) )
                #max price
                #maxs.append( get_max_price( prices[ index ] ) )
                #prog
                #progs.append( get_prognosis( prices[ index ] ) )
            #Endzeit

            logfile.write( get_time() + '   Saving data' + '\n' )

            data_file = open( DATA_FILE, 'w' )

            for index in range( 0, len( links ) ):
                data_file.write( dumps( [ links[ index] , titles[ index ] , currencies[ index ] , prices[ index ] ] ) + '\n' )

            data_file.close()

            end_time = time()


            #Differenz berechnen
            diff_time = end_time - start_time
            logfile.write( get_time() + '   It took ' + str( int( round( diff_time ) ) ) + ' seconds' + '\n' )

            #Sleeptime berechnen
            if 2 * diff_time > MAX_SLEEP_TIME:
                sleeptime = MAX_SLEEP_TIME
            elif 2 * diff_time < MIN_SLEEP_TIME:
                sleeptime = MIN_SLEEP_TIME
            else:
                sleeptime = 2 * diff_time


            logfile.write( get_time() + '   Sleeping for ' + str( int( round( sleeptime ) ) ) + ' seconds' + '\n' )
            logfile.close()
            sleep( sleeptime )

    except KeyboardInterrupt:
        logfile.write( get_time() + ' Program halted by user' + '\n' )
        logfile.write( get_time() + ' Exited normally' + '\n' )
        exit()
    #except:
        #logfile.write( get_time() + ' Something went wrong' + '\n' )
        #exit()


    write_config_file( [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ] )

    logfile.write( get_time() + ' Exited normally' + '\n' )
    logfile.close()

