#!/usr/bin/python -u
# -*- coding: utf-8 -*-


# TODO:
#   - get_prognosis
#   - prognosis in print_list
#   - way to delete articles
#   - test, what happens, when price is 'N/A'



from amazonCheckLib import get_min_price, get_avg_price, get_max_price, get_info_for, get_time, shorten_amazon_link
from amazonCheckLib import BOLD_WHITE, BLUE, GREEN, RED, YELLOW, NOCOLOR
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
        data_file.write( dumps( [ url, title, currency, [ [ price, time() ] ] ] ) + '\n' )
    except UnicodeDecodeError:
        data_file.write( dumps( [ url, 'Encountered error', currency, [ [ price, time() ] ] ] )  + '\n' )

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
            mins = get_min_price( prices[ index ] )
            maxs = get_max_price( prices[ index ] )
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

    write_log_file( ' Read Config File at ' + CONFIG_FILE )

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

    write_log_file( ' Reset Config File at ' + CONFIG_FILE )



def write_config_file( options ):

    if type( options[ 0 ] ) != type( True ) or type( options[ 1 ] ) != type( True ) or type( options[ 2 ] ) != type( True ) or type( options[ 3 ] ) != type( 1 ) or type( options[ 3 ] ) != type( 1 ):

        config_file = open( CONFIG_FILE, 'w' )

        config_file.write( dumps( options ) )

        config_file.close()

    write_log_file( ' Wrote to Config File at ' + CONFIG_FILE )



def read_data_file():
    if not exists( DATA_FILE ):
        write_log_file( ' Data File does not exist' )
        write_log_file( ' Program halted' )
        exit( 'Data File does not exist.' )

    write_log_file( ' Data File is being read' )

    data_file = open( DATA_FILE, 'r' )

    data = data_file.readlines()

    data_file.close()

    write_log_file( ' Data is being processed' )

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

    logfile.write( get_time() + string + '\n' )

    logfile.close()


#-----------------------------------------------------------------------


if __name__ == '__main__':

    write_log_file( ' -------------------------------' )
    write_log_file( ' Started Program' )

    [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ] = read_config_file()

    if len( argv ) == 2 and argv[1] == 'show':
        ( links, titles, currencies, prices ) = read_data_file()

        write_log_file( ' Showing list' )

        print_result( links, titles, currencies, prices )

        write_log_file( ' Program halted after output' )
        exit(0)


    if len( argv ) > 2:
        if argv[1] == '-a' or argv[1] == 'add':
            add_article( shorten_amazon_link( argv[2] ) )
            write_log_file( ' Program halted after adding article' )
            exit(0)


    write_config = False

    if len( argv ) > 1:

        for argument in argv[ 1 : ]:

            write_log_file( ' Program called with \'' + argument + '\'' )

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
                    write_log_file( ' Given min_sleep argument was not a number' )

            elif argument.find( '--min_sleep=' ) != -1:

                try:
                    MAX_SLEEP_TIME = float( argument[ 12 : ] )

                    write_config = True

                except ValueError:
                    write_log_file( ' Given max_sleep argument was not a number' )

            else:

                write_log_file( ' Illegal argument \'' + argument + '\' detected' )
                continue

        if write_config:
            write_config_file( [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ] )

    #Read data [ link, title, currency, prices, ... ]

    ( links, titles, currencies, prices ) = read_data_file()

    runs = 0

    try:

        write_log_file( ' Starting main loop' )

        while 1:
            runs = runs + 1

            write_log_file( ' Starting run ' + str( runs ) + ':' )

            sleeptime = MIN_SLEEP_TIME
            avgs = []
            mins = []
            maxs = []
            progs = []

            #Startzeit
            start_time = time()
            #Schleife mit get_info
            write_log_file( '   Getting info' )
            for index in range( 0, len( links ) ):
                info = get_info_for( links[ index ] )

                titles[ index ] = info[0]
                currencies[ index ] = info[1]
                prices[ index ].append( [ info[2], int( round( time() ) ) ] )

            #Endzeit

            write_log_file( '   Saving data' )

            write_data_file( links, titles, currencies, prices )

            end_time = time()


            #Differenz berechnen
            diff_time = round( end_time - start_time, 2 )
            write_log_file( '   It took ' + str( int( diff_time ) ) + ' seconds' )

            #Sleeptime berechnen
            if 2 * diff_time > MAX_SLEEP_TIME:
                sleeptime = MAX_SLEEP_TIME
            elif 2 * diff_time < MIN_SLEEP_TIME:
                sleeptime = MIN_SLEEP_TIME
            else:
                sleeptime = 2 * diff_time


            write_log_file( '   Sleeping for ' + str( int( round( sleeptime ) ) ) + ' seconds' )
            sleep( sleeptime )

    except KeyboardInterrupt:
        write_log_file( ' Program halted by user' )
        write_log_file( ' Exited normally' )
        exit(0)
    #except:
        #write_log_file( ' Something went wrong' )
        #write_log_file( ' Exited abnormally' )
        #exit(1)

