#!/usr/bin/python -u
# -*- coding: utf-8 -*-

from amazonCheckTrans import strings as s
from amazonCheckLib import get_min_price, get_avg_price, get_max_price, get_info_for, get_time, notify, print_help_text, print_notification, shorten_amazon_link, TimeoutException
from colors import BOLD_WHITE, BLUE, GREEN, RED, YELLOW, NOCOLOR

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

open( LOG_FILE, 'w' ).close()



def add_article( url ):
    data_file = open( DATA_FILE, 'a' )
    ( title, currency, price, pic_url ) = get_info_for( url )

    if ( title, currency, price, pic_url ) == ( -1, -1, -1, -1 ):
        write_log_file( s[ 'err-conec' ], True )
        write_log_file( s[ 'prgm-term' ], True )
        write_log_file( s[ 'dashes' ] )
        data_file.close()
        exit( s[ 'no-conect' ] )

    pic_name = search( '\/[A-Z0-9]{10}\/', url ).group()[1: -1] + '.jpg'

    open( IMAGE_PATH + pic_name, IMAGE_WRITE_MODE ).write( urlopen( pic_url ).read() )

    try:
        data_file.write( dumps( [ url, title, currency, pic_name, [ [ price, int( round( time() ) ) ] ] ] ) + '\n' )
    except UnicodeDecodeError:
        data_file.write( dumps( [ url, s[ 'err-gener' ], currency, pic_name, [ [ price, int( round( time() ) ) ] ] ] )  + '\n' )

    data_file.close()



def print_delete_menu():

    write_log_file( s[ 'del-mn-cl' ] )

    ( links, titles, currencies, pictures, prices ) = read_data_file()

    selection = 0

    print( '' )

    for index in range(0, len( titles ) ):
        print( str( index + 1 ) + '\t' + currencies[ index ] + '\t' + str( prices[ index ][-1][0] ) + '\t' + titles[ index ] )

    print( '' )
    print( s[ 'del-selct' ] ),
    selection = raw_input()

    try:
        selection = int( selection )
    except ValueError:
        write_log_file( s[ 'slctn-nan' ] )
        exit( s[ 'input-nan' ] )

    if selection == 0:
        exit()

    elif selection > len( titles ):
        pass
        write_log_file( s[ 'slctn-nir' ] )
        exit( s[ 'indx-nofd' ] )

    else:
        selection -= 1
        links.pop( selection )
        titles.pop( selection )
        currencies.pop( selection )
        pictures.pop( selection )
        prices.pop( selection )

        write_data_file( links, titles, currencies, pictures, prices )

        write_log_file( s[ 'add-succs' ] )

        print( s[ 'add-succs' ] )
        exit()



def print_result( titles, currencies, prices ):
    print( BOLD_WHITE + s[ 'show-head' ] + NOCOLOR )

    color_min = GREEN
    color_max = RED
    color_avg = YELLOW

    color_plain = NOCOLOR

    color_price = NOCOLOR

    print( '' )

    for index in range( 0, len( titles ) ):
        price = prices[ index ][-1][0]

        if len( prices[ index ] ) == 1:
            avgs = prices[ index ][0][0]
            mins = prices[ index ][0][0]
            maxs = prices[ index ][0][0]
            #progs = prices
        else:
            avgs = get_avg_price( prices[ index ] )
            if avgs == -1: avgs = s[ 'N/A' ]
            mins = get_min_price( prices[ index ] )
            if mins == -1: mins = s[ 'N/A' ]
            maxs = get_max_price( prices[ index ] )
            if maxs == -1: maxs = s[ 'N/A' ]
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

    print( '' )



def read_config_file():

    if not exists( CONFIG_FILE ):

        reset_config_file()

        return [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ]

    try:
        config_file = open( CONFIG_FILE, 'r' )
    except IOError:
        write_log_file( s[ 'cnf-no-pm' ], True )
        write_log_file( s[ 'us-def-op' ], True )
        return [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ]

    try:
        options = loads( config_file.read() )
    except ValueError:
        reset_config_file()
        return [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ]

    write_log_file( s[ 'rd-cf-fil' ] + CONFIG_FILE )

    if type( options[ 0 ] ) != type( True ) or type( options[ 1 ] ) != type( True ) or type( options[ 2 ] ) != type( True ) or type( options[ 3 ] ) != type( 1 ) or type( options[ 3 ] ) != type( 1 ):

        write_log_file( s[ 'err-rd-cf' ] )

        reset_config_file()

        return [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ]
    else:
        return options



def reset_config_file():

    options = [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ]

    write_config_file( options )

    write_log_file( s[ 'rd-cf-fil' ] + CONFIG_FILE )



def write_config_file( options ):

    if not ( type( options[ 0 ] ) != type( True ) or type( options[ 1 ] ) != type( True ) or type( options[ 2 ] ) != type( True ) or type( options[ 3 ] ) != type( 1 ) or type( options[ 4 ] ) != type( 1 ) ):

        try:
            config_file = open( CONFIG_FILE, 'w' )
        except IOError:
            write_log_file( s[ 'cnf-no-pm' ], True )
            return False

        config_file.write( dumps( options ) )

        config_file.close()

        write_log_file( s[ 'wrt-cf-fl' ] + CONFIG_FILE )

    else:
        write_log_file( s[ 'opt-types' ], True )
        for option in options:
            write_log_file( str( type( option ) ) )



def read_data_file():
    if not exists( DATA_FILE ):
        write_log_file( s[ 'dat-fl-ms' ], True )
        write_log_file( s[ 'prgm-hltd' ], True )
        write_log_file( '---------------------------------------' )
        exit( s[ 'dat-fl-ms' ] )

    write_log_file( s[ 'dat-fl-rd' ] )

    try:
        data_file = open( DATA_FILE, 'r' )
    except IOError:
        write_log_file( s[ 'dat-no-pm' ], True )
        exit( s[ 'dat-no-pm' ] )

    data = data_file.readlines()

    data_file.close()

    write_log_file( s[ 'data-prcs' ] )

    #Break up into links, titles currencies, pictures and prices

    links = []
    titles = []
    currencies =[]
    pictures = []
    prices = []

    for index in range( 0,  len( data ) ):
        try:
            info = loads( data[ index ] )
        except ValueError:
            print( 'Bad Json found.' )
            continue
            #exit( 'Problem encoding the value' )                        #Translating

        links.append( info[0] )
        titles.append( info[1] )
        currencies.append( info[2] )
        pictures.append( info[3] )
        prices.extend( info[ 4: ] )

    return ( links, titles, currencies, pictures, prices )



def timeout( seconds ):
    alarm( seconds )



def timeout_handler( signum, frame ):
    raise TimeoutException( Exception )



def write_data_file( links, titles, currencies, pictures, prices ):
    try:
        data_file = open( DATA_FILE, 'w' )
    except IOError:
        write_log_file( s[ 'dat-no-pm' ], True )
        return false

    for index in range( 0, len( links ) ):
        try:
            data_file.write( dumps( [ links[ index] , titles[ index ] , currencies[ index ] , pictures[ index ], prices[ index ] ] ) + '\n' )
        except:
            data_file.write( dumps( [ links[ index] , s[ 'err-gener' ] , currencies[ index ] , pictures[ index ], prices[ index ] ] ) + '\n' )

    data_file.close()



def write_log_file( string, output=False ):
    if VERBOSE and output:
        print( get_time() + ' ' + string + '\n' ),

    try:
        logfile = open( LOG_FILE, 'a' )

    except IOError:
        #write_log_file( s[ 'log-no-pm' ] )
        return false

    logfile.write( get_time() + ' ' + string + '\n' )
    logfile.close()

#-----------------------------------------------------------------------
#-----------------------------------------------------------------------


if __name__ == '__main__':

    write_log_file( s[ 'dashes' ] )
    write_log_file( s[ 'str-prgm' ] )

    [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ] = read_config_file()

    runs = 0

    if len( argv ) == 2 and argv[1] == 'show':
        ( not_used, titles, currencies, not_used, prices ) = read_data_file()

        write_log_file( s[ 'sh-art-ls'] )

        print_result( titles, currencies, prices )

        write_log_file( s[ 'pg-hlt-op' ] )
        write_log_file( s[ 'dashes' ] )
        exit(0)

    if len( argv ) == 2 and (argv[1] == 'help' or argv[1] == '-h' or argv[1] == '--help'):
        write_log_file( s[ 'sh-hlp-mn' ] )

        print_help_text()

        write_log_file( s[ 'pg-hlt-op' ] )
        write_log_file( s[ 'dashes' ] )
        exit(0)

    if len( argv ) == 2 and (argv[1] == 'delete' or argv[1] == '-d' or argv[1] == '--delete'):
        write_log_file( s[ 'sh-del-mn' ] )

        print_delete_menu()

        write_log_file( s[ 'pg-hlt-op' ] )
        write_log_file( s[ 'dashes' ] )
        exit(0)


    if len( argv ) > 2:
        if argv[1] == '-a' or argv[1] == 'add':
            url = shorten_amazon_link( argv[2] )
            write_log_file( s[ 'add-artcl' ] + url )
            add_article( url )
            write_log_file( s[ 'pg-hlt-ad' ] )
            write_log_file( s[ 'dashes' ] )
            exit(0)


    write_config = False

    if len( argv ) > 1:

        for argument in argv[ 1 : ]:

            write_log_file( s[ 'prgm-clld' ] + ' \'' + argument + '\'' )

            if argument == '-s' or argument == '--silent':

                UPDATES_ONLY = False
                VERBOSE = False
                SILENT = True

                write_config = True
                write_log_file( s[ 'ch-silent' ], True )

            elif argument == '-v' or argument == '--verbose':

                UPDATES_ONLY = True
                SILENT = False
                VERBOSE = True

                write_config = True
                write_log_file( s[ 'ch-verbos' ], True )

            elif argument == '-u' or argument == '--updates_only':

                SILENT = False
                VERBOSE = False
                UPDATES_ONLY = True

                write_config = True
                write_log_file( s[ 'ch-updonl' ], True )

            elif argument.find( '--min_sleep=' ) != -1:

                try:
                    MIN_SLEEP_TIME = int( argument[ 12 : ] )

                    write_config = True
                    write_log_file( s[ 'ch-mn-slp' ] + str( MIN_SLEEP_TIME ), True )

                except ValueError:
                    write_log_file( s[ 'mn-slpnan' ], True )

            elif argument.find( '--max_sleep=' ) != -1:

                try:
                    MAX_SLEEP_TIME = int( argument[ 12 : ] )

                    write_config = True
                    write_log_file( s[ 'ch-mx-slp' ] + str( MAX_SLEEP_TIME ), True )

                except ValueError:
                    write_log_file( s[ 'mx-slpnan' ], True )

            else:

                write_log_file( s[ 'ill-argmt' ] + '\'' + argument + '\'', True )
                continue

    if write_config:
        write_config_file( [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ] )

    signal( SIGALRM, timeout_handler )

    try:

        write_log_file( s[ 'str-mn-lp' ] )

        while 1:
            #Reading data

            ( links, titles, currencies, pictures, prices ) = read_data_file()

            sleeptime = MIN_SLEEP_TIME
            avgs = []
            mins = []
            maxs = []
            progs = []

            runs = runs + 1

            write_log_file( s[ 'strtg-run' ] + str( runs ) + ':', True )

            #Getting the start time

            start_time = time()

            #Updates the information

            write_log_file( s[ 'getng-dat' ], True )

            for index in range( 0, len( links ) ):

                try:
                    timeout( TIMEOUT_TIME )
                    info = get_info_for( links[ index ] )
                    timeout( 0 )
                except TimeoutException:
                    write_log_file( s[ 'con-tmout' ], True )
                    write_log_file( s[ 'artcl-skp' ] + str( links[ index ] ), True )
                    continue

                if info == ( -1, -1, -1, -1 ):
                    write_log_file( s[ 'err-con-s' ], True )
                    write_log_file( s[ 'artcl-skp' ] + str( links[ index ] ), True )
                    continue

                #titles[ index ] = info[0]
                #currencies[ index ] = info[1]

                if info[2] == prices[ index ][-1][0]:
                    pass
                else:
                    if UPDATES_ONLY:
                        if prices[ index ][-1][0] == s[ 'N/A' ] and not info[2] == s[ 'N/A' ]:
                            title = s[ 'bec-avail' ] + NOCOLOR + ':'

                        elif info[2] == s[ 'N/A' ]:
                            title = s[ 'bec-unava' ] + NOCOLOR + ':'

                        elif info[2] < prices[ index ][-1][0]:
                            title = s[ 'price-dwn' ] + str( prices[ index ][-1][0] ) + ' > ' + str( info[2] ) + ' )' + NOCOLOR + ':'

                        elif info[2] > prices[ index ][-1][0]:
                            title = s[ 'price-up' ] + str( prices[ index ][-1][0] ) + ' > ' + str( info[2] ) + ' )' + NOCOLOR + ':'

                        body = str( info[0] )

                        notify( title, body, IMAGE_PATH + pictures[ index ] )

                        if VERBOSE:
                            print_notification( title, body, '' )

                    prices[ index ].append( [ info[2], int( round( time() ) ) ] )



            #Saving data to file

            write_log_file( s[ 'svng-data' ], True )

            write_data_file( links, titles, currencies, pictures, prices )

            #Getting the time the operation finished

            end_time = time()

            #Calculating the length of operating

            diff_time = round( end_time - start_time, 2 )

            write_log_file( s[ 'it-took' ] + str( int( diff_time ) ) + s[ 'seconds' ], True )

            #Calculating sleeptime

            if 2 * diff_time > MAX_SLEEP_TIME:
                sleeptime = MAX_SLEEP_TIME
            elif 2 * diff_time < MIN_SLEEP_TIME:
                sleeptime = MIN_SLEEP_TIME
            else:
                sleeptime = 2 * diff_time

            #Sleeping for agreed amount

            write_log_file( s[ 'sleep-for' ] + str( int( round( sleeptime ) ) ) + s[ 'seconds' ], True )

            sleep( sleeptime )

    except KeyboardInterrupt:
        write_log_file( s[ 'pg-hlt-us' ], True )
        write_log_file( s[ 'exit-norm' ], True )
        write_log_file( s[ 'dashes' ] )
        exit(0)
    #except:
        #write_log_file( 'Something went wrong' )
        #write_log_file( 'Exited abnormally' )
        #exit(1)

