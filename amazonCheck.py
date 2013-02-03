#!/usr/bin/python -u
# -*- coding: utf-8 -*-

from amazonCheckLib import get_min_price, get_avg_price, get_max_price, get_info_for, get_time, shorten_amazon_link
from amazonCheckLib import BOLD_WHITE, BLUE, GREEN, RED, YELLOW, NOCOLOR
from os.path import exists, expanduser
from time import ctime, time, sleep
from json import dumps, loads
from sys import argv, exit
from re import search
from os import name


# TODO:
#   - get_prognosis
#   - prognosis in print_list
#   - way to delete articles
#   - test, what happens, when price is 'N/A'



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

    if ( title, currency, price) == ( -1, -1, -1 ):
        write_log_file( 'Error while connecting' )
        write_log_file( 'Program is terminating' )
        data_file.close()
        exit(1)

    try:
        data_file.write( dumps( [ url, title, currency, [ [ price, int( round( time() ) ) ] ] ] ) + '\n' )
    except UnicodeDecodeError:
        data_file.write( dumps( [ url, 'Encountered error', currency, [ [ price, int( round( time() ) ) ] ] ] )  + '\n' )

    data_file.close()



def print_result( links, titles, currencies, prices ):
    print( BOLD_WHITE + '\tPrice\tMin\tAvg\tMax\tTitle\t' + NOCOLOR )

    color_min = GREEN
    color_max = RED
    color_avg = YELLOW

    color_plain = NOCOLOR

    color_price = NOCOLOR


    for index in range( 0, len( links ) ):
        price = prices[ index ][-1][0]

        if len( prices ) == 1:
            avgs = prices
            mins = prices
            maxs = prices
            #progs = prices
        else:
            avgs = get_avg_price( prices[ index ] )
            if avgs == -1: avgs = 'N/A'
            mins = get_min_price( prices[ index ] )
            if mins == -1: mins = 'N/A'
            maxs = get_max_price( prices[ index ] )
            if maxs == -1: maxs = 'N/A'
            #progs.append( get_prognosis( prices[ index ] ) )

        if maxs == mins:
            color_price = NOCOLOR

        elif price == mins:
            color_price = BLUE

        elif price > avgs:
            color_price = RED

        elif price < avgs:
            color_price = GREEN

        print( str( currencies[ index ] ) + '\t' + color_price + str( price ) + '\t' + color_min + str( mins ) + '\t' + color_avg + str( avgs ) + '\t' + color_max + str( maxs ) + '\t' + color_plain + titles[ index ] )

        write_data_file( links, titles, currencies, prices )



def read_config_file():

    if not exists( CONFIG_FILE ):

        reset_config_file()

        return [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ]

    config_file = open( CONFIG_FILE, 'r' )

    options = loads( config_file.read() )

    write_log_file( 'Read Config File at ' + CONFIG_FILE )

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

    write_log_file( 'Reset Config File at ' + CONFIG_FILE )



def write_config_file( options ):

    if not ( type( options[ 0 ] ) != type( True ) or type( options[ 1 ] ) != type( True ) or type( options[ 2 ] ) != type( True ) or type( options[ 3 ] ) != type( 1 ) or type( options[ 4 ] ) != type( 1 ) ):

        config_file = open( CONFIG_FILE, 'w' )

        config_file.write( dumps( options ) )

        config_file.close()

        write_log_file( 'Wrote to Config File at ' + CONFIG_FILE )

    else:
        write_log_file( 'Did not write to Config File. Options did not match necessary types' )
        for option in options:
            write_log_file( str( type( option ) ) )



def read_data_file():
    if not exists( DATA_FILE ):
        write_log_file( 'Data File does not exist' )
        write_log_file( 'Program halted' )
        exit( 'Data File does not exist.' )

    write_log_file( 'Data File is being read' )

    data_file = open( DATA_FILE, 'r' )

    data = data_file.readlines()

    data_file.close()

    write_log_file( 'Data is being processed' )

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



def write_data_file( links, titles, currencies, prices ):
    data_file = open( DATA_FILE, 'w' )

    for index in range( 0, len( links ) ):
        data_file.write( dumps( [ links[ index] , titles[ index ] , currencies[ index ] , prices[ index ] ] ) + '\n' )

    data_file.close()



def write_log_file( string ):
    logfile = open( LOGFILE, 'a' )

    if VERBOSE:
        print( get_time() + ' ' + string + '\n' ),

    logfile.write( get_time() + ' ' + string + '\n' )

    logfile.close()


#-----------------------------------------------------------------------


if __name__ == '__main__':


    [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ] = read_config_file()

    write_log_file( '-------------------------------' )
    write_log_file( 'Started Program' )

    runs = 0

    if len( argv ) == 2 and argv[1] == 'show':
        ( links, titles, currencies, prices ) = read_data_file()

        write_log_file( 'Showing list' )

        print_result( links, titles, currencies, prices )

        write_log_file( 'Program halted after output' )
        write_log_file( '-------------------------------' )
        exit(0)


    if len( argv ) > 2:
        if argv[1] == '-a' or argv[1] == 'add':
            url = shorten_amazon_link( argv[2] )
            write_log_file( 'Adding article from: ' + url )
            add_article( url )
            write_log_file( 'Program halted after adding article' )
            exit(0)


    write_config = False

    if len( argv ) > 1:

        for argument in argv[ 1 : ]:

            write_log_file( 'Program called with \'' + argument + '\'' )

            if argument == '-s' or argument == '--silent':

                UPDATES_ONLY = False
                VERBOSE = False
                SILENT = True

                write_config = True
                write_log_file( 'Changed output-mode to SILENT' )

            elif argument == '-v' or argument == '--verbose':

                UPDATES_ONLY = False
                SILENT = False
                VERBOSE = True

                write_config = True
                write_log_file( 'Changed output-mode to VERBOSE' )

            elif argument == '-u' or argument == '--updates_only':

                SILENT = False
                VERBOSE = False
                UPDATES_ONLY = True

                write_config = True
                write_log_file( 'Changed output-mode to UPDATES_ONLY' )

            elif argument.find( '--min_sleep=' ) != -1:

                try:
                    MIN_SLEEP_TIME = int( argument[ 12 : ] )

                    write_config = True
                    write_log_file( 'Changed MIN_SLEEP_TIME to ' + str( MIN_SLEEP_TIME ) )

                except ValueError:
                    write_log_file( 'Given min_sleep argument was not a number' )

            elif argument.find( '--max_sleep=' ) != -1:

                try:
                    MAX_SLEEP_TIME = int( argument[ 12 : ] )

                    write_config = True
                    write_log_file( 'Changed MAX_SLEEP_TIME to ' + str( MAX_SLEEP_TIME ) )

                except ValueError:
                    write_log_file( 'Given max_sleep argument was not a number' )

            else:

                write_log_file( 'Illegal argument \'' + argument + '\' detected' )
                continue

    if write_config:
        write_config_file( [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ] )

    #Reading data

    ( links, titles, currencies, prices ) = read_data_file()

    write_data_file( links, titles, currencies, prices )

    try:

        write_log_file( 'Starting main loop' )

        while 1:
            sleeptime = MIN_SLEEP_TIME
            avgs = []
            mins = []
            maxs = []
            progs = []

            runs = runs + 1

            write_log_file( 'Starting run ' + str( runs ) + ':' )

            #Getting the start time

            start_time = time()

            #Updates the information

            write_log_file( '  Getting data' )

            for index in range( 0, len( links ) ):
                info = get_info_for( links[ index ] )

                if info == ( -1, -1, -1):
                    write_log_file( '   Error while connecting' )
                    write_log_file( '   Article from ' + str( links[ index ] ) + ' was skipped' )
                    continue

                titles[ index ] = info[0]
                currencies[ index ] = info[1]

                if info[2] == prices[ index ][-1][0]:
                    pass
                else:
                    if UPDATES_ONLY:
                        if prices[ index ][-1][0] == 'N/A' and not info[2] == 'N/A':
                            print( get_time() + ' Just became ' + GREEN + 'available' + NOCOLOR + ': ' + str( info[0] ) )

                        elif info[2] == 'N/A':
                            print( get_time() + ' Just became ' + RED + 'not available' + NOCOLOR + ': ' + str( info[0] ) )

                        elif info[2] > prices[ index ][-1][0]:
                            print( get_time() + ' Just became ' + GREEN + 'cheaper' + NOCOLOR + ': ' + str( info[0] ) )

                        elif info[2] < prices[ index ][-1][0]:
                            print( get_time() + ' Just became ' + RED + 'more expensive' + NOCOLOR + ': ' + str( info[0] ) )

                    prices[ index ].append( [ info[2], int( round( time() ) ) ] )



            #Saving data to file

            write_log_file( '  Saving data' )

            write_data_file( links, titles, currencies, prices )

            #Getting the time the operation finished

            end_time = time()

            #Calculating the length of operating

            diff_time = round( end_time - start_time, 2 )

            write_log_file( '  It took ' + str( int( diff_time ) ) + ' seconds' )

            #Calculating sleeptime

            if 2 * diff_time > MAX_SLEEP_TIME:
                sleeptime = MAX_SLEEP_TIME
            elif 2 * diff_time < MIN_SLEEP_TIME:
                sleeptime = MIN_SLEEP_TIME
            else:
                sleeptime = 2 * diff_time

            #Sleeping for agreed amount

            write_log_file( '  Sleeping for ' + str( int( round( sleeptime ) ) ) + ' seconds' )

            sleep( sleeptime )

    except KeyboardInterrupt:
        write_log_file( 'Program halted by user' )
        write_log_file( 'Exited normally' )
        exit(0)
    #except:
        #write_log_file( 'Something went wrong' )
        #write_log_file( 'Exited abnormally' )
        #exit(1)

