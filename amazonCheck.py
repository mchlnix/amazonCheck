#!/usr/bin/python -u
# -*- coding: utf-8 -*-

from amazonCheckLib import get_min_price, get_avg_price, get_max_price, get_info_for, get_time, notify, print_help_text, print_notification, shorten_amazon_link
from amazonCheckLib import BOLD_WHITE, BLUE, GREEN, RED, YELLOW, NOCOLOR
from os.path import exists, expanduser
from signal import alarm, signal, SIGALRM
from urllib import urlopen
from time import ctime, time, sleep
from json import dumps, loads
from sys import argv, exit
from re import search
from os import name



if name == 'nt':
    IMAGE_WRITE_MODE = 'wb'
else:
    IMAGE_WRITE_MODE = 'w'

CONFIG_FILE = expanduser( '~/.amazonCheck/aC.config' )
DATA_FILE = expanduser( '~/.amazonCheck/aC.data' )
LOG_FILE = expanduser( '~/.amazonCheck/aC.log' )

IMAGE_PATH = expanduser( '~/.amazonCheck/pics/' )

SILENT = True
UPDATES_ONLY = False
VERBOSE = False

MIN_SLEEP_TIME = 180
MAX_SLEEP_TIME = 300
TIMEOUT_TIME = 15

CONFIG_VARS = 5



def add_article( url ):
    data_file = open( DATA_FILE, 'a' )
    ( title, currency, price, pic_url ) = get_info_for( url )

    if ( title, currency, price, pic_url ) == ( -1, -1, -1, -1 ):
        write_log_file( 'Error while connecting', True )
        write_log_file( 'Program is terminating', True )
        data_file.close()
        exit( 'Could not connect to website. Please check the provided link or your internet connection.' )

    pic_name = search( '\/[A-Z0-9]{10}\/', url ).group()[1: -1] + '.jpg'

    open( IMAGE_PATH + pic_name, IMAGE_WRITE_MODE ).write( urlopen( pic_url ).read() )

    try:
        data_file.write( dumps( [ url, title, currency, pic_name, [ [ price, int( round( time() ) ) ] ] ] ) + '\n' )
    except UnicodeDecodeError:
        data_file.write( dumps( [ url, 'Encountered error', currency, pic_name, [ [ price, int( round( time() ) ) ] ] ] )  + '\n' )

    data_file.close()



def print_result( titles, currencies, prices ):
    print( BOLD_WHITE + '\tPrice\tMin\tAvg\tMax\tTitle\t' + NOCOLOR )

    color_min = GREEN
    color_max = RED
    color_avg = YELLOW

    color_plain = NOCOLOR

    color_price = NOCOLOR


    for index in range( 0, len( titles ) ):
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
        write_log_file( 'Did not write to Config File. Options did not match necessary types', True )
        for option in options:
            write_log_file( str( type( option ) ) )



def read_data_file():
    if not exists( DATA_FILE ):
        write_log_file( 'Data File does not exist', True )
        write_log_file( 'Program halted', True )
        exit( 'Data File does not exist.' )

    write_log_file( 'Data File is being read' )

    data_file = open( DATA_FILE, 'r' )

    data = data_file.readlines()

    data_file.close()

    write_log_file( 'Data is being processed' )

    #Break up into links, titles currencies, pictures and prices

    links = []
    titles = []
    currencies =[]
    pictures = []
    prices = []

    for index in range( 0,  len( data ) ):
        info = loads( data[ index ] )

        links.append( info[0] )
        titles.append( info[1] )
        currencies.append( info[2] )
        pictures.append( info[3] )
        prices.extend( info[ 4: ] )

    return ( links, titles, currencies, pictures, prices )



def write_data_file( links, titles, currencies, pictures, prices ):
    data_file = open( DATA_FILE, 'w' )

    for index in range( 0, len( links ) ):
        data_file.write( dumps( [ links[ index] , titles[ index ] , currencies[ index ] , pictures[ index ], prices[ index ] ] ) + '\n' )

    data_file.close()



def timeout( seconds ):
    alarm( seconds )



def timeout_handler( signum, frame ):
    raise Exception



def write_log_file( string, output=False ):
    logfile = open( LOG_FILE, 'a' )

    if VERBOSE and output:
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
        ( not_used, titles, currencies, not_used, prices ) = read_data_file()

        write_log_file( 'Showing list' )

        print_result( titles, currencies, prices )

        write_log_file( 'Program halted after output' )
        write_log_file( '-------------------------------' )
        exit(0)

    if len( argv ) == 2 and (argv[1] == 'help' or argv[1] == '-h' or argv[1] == '--help'):
        write_log_file( 'Showing help-text' )

        print_help_text()

        write_log_file( 'Program halted after output' )
        write_log_file( '-------------------------------' )
        exit(0)


    if len( argv ) > 2:
        if argv[1] == '-a' or argv[1] == 'add':
            url = shorten_amazon_link( argv[2] )
            write_log_file( 'Adding article from: ' + url )
            add_article( url )
            write_log_file( 'Program halted after adding article' )
            write_log_file( '---------------------------------------' )
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
                write_log_file( 'Changed output-mode to SILENT', True )

            elif argument == '-v' or argument == '--verbose':

                UPDATES_ONLY = True
                SILENT = False
                VERBOSE = True

                write_config = True
                write_log_file( 'Changed output-mode to VERBOSE', True )

            elif argument == '-u' or argument == '--updates_only':

                SILENT = False
                VERBOSE = False
                UPDATES_ONLY = True

                write_config = True
                write_log_file( 'Changed output-mode to UPDATES_ONLY', True )

            elif argument.find( '--min_sleep=' ) != -1:

                try:
                    MIN_SLEEP_TIME = int( argument[ 12 : ] )

                    write_config = True
                    write_log_file( 'Changed MIN_SLEEP_TIME to ' + str( MIN_SLEEP_TIME ), True )

                except ValueError:
                    write_log_file( 'Given min_sleep argument was not a number', True )

            elif argument.find( '--max_sleep=' ) != -1:

                try:
                    MAX_SLEEP_TIME = int( argument[ 12 : ] )

                    write_config = True
                    write_log_file( 'Changed MAX_SLEEP_TIME to ' + str( MAX_SLEEP_TIME ), True )

                except ValueError:
                    write_log_file( 'Given max_sleep argument was not a number', True )

            else:

                write_log_file( 'Illegal argument \'' + argument + '\' detected', True )
                continue

    if write_config:
        write_config_file( [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ] )

    #Reading data

    ( links, titles, currencies, pictures, prices ) = read_data_file()

    signal( SIGALRM, timeout_handler )

    try:

        write_log_file( 'Starting main loop' )

        while 1:
            sleeptime = MIN_SLEEP_TIME
            avgs = []
            mins = []
            maxs = []
            progs = []

            runs = runs + 1

            write_log_file( 'Starting run ' + str( runs ) + ':', True )

            #Getting the start time

            start_time = time()

            #Updates the information

            write_log_file( '  Getting data', True )

            for index in range( 0, len( links ) ):

                try:
                    timeout( TIMEOUT_TIME )
                    info = get_info_for( links[ index ] )
                    timeout( 0 )
                except Exception:
                    write_log_file( '  Connection timed out. ', True )
                    write_log_file( '    Article from ' + str( links[ index ] ) + ' was skipped', True )
                    continue

                if info == ( -1, -1, -1, -1 ):
                    write_log_file( '  Error while connecting', True )
                    write_log_file( '    Article from ' + str( links[ index ] ) + ' was skipped', True )
                    continue

                titles[ index ] = info[0]
                currencies[ index ] = info[1]

                if info[2] == prices[ index ][-1][0]:
                    pass
                else:
                    if UPDATES_ONLY:
                        if prices[ index ][-1][0] == 'N/A' and not info[2] == 'N/A':
                            title = 'Just became ' + GREEN + 'available' + NOCOLOR + ':'

                        elif info[2] == 'N/A':
                            title = 'Just became ' + RED + 'not available' + NOCOLOR + ':'

                        elif info[2] < prices[ index ][-1][0]:
                            title = 'Price went ' + GREEN + 'down ( ' + str( prices[ index ][-1][0] ) + ' > ' + str( info[2] ) + ' )' + NOCOLOR + ':'

                        elif info[2] > prices[ index ][-1][0]:
                            title = 'Price went ' + RED + 'up ( ' + str( prices[ index ][-1][0] ) + ' > ' + str( info[2] ) + ' )' + NOCOLOR + ':'

                        body = str( info[0] )


                        notify( title, body, IMAGE_PATH + pictures[ index ] )

                        if VERBOSE:
                            print_notification( title, body, '' )

                    prices[ index ].append( [ info[2], int( round( time() ) ) ] )



            #Saving data to file

            write_log_file( '  Saving data', True )

            write_data_file( links, titles, currencies, pictures, prices )

            #Getting the time the operation finished

            end_time = time()

            #Calculating the length of operating

            diff_time = round( end_time - start_time, 2 )

            write_log_file( '  It took ' + str( int( diff_time ) ) + ' seconds', True )

            #Calculating sleeptime

            if 2 * diff_time > MAX_SLEEP_TIME:
                sleeptime = MAX_SLEEP_TIME
            elif 2 * diff_time < MIN_SLEEP_TIME:
                sleeptime = MIN_SLEEP_TIME
            else:
                sleeptime = 2 * diff_time

            #Sleeping for agreed amount

            write_log_file( '  Sleeping for ' + str( int( round( sleeptime ) ) ) + ' seconds', True )

            sleep( sleeptime )

    except KeyboardInterrupt:
        write_log_file( 'Program halted by user', True )
        write_log_file( 'Exited normally', True )
        exit(0)
    #except:
        #write_log_file( 'Something went wrong' )
        #write_log_file( 'Exited abnormally' )
        #exit(1)

