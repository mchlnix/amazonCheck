#!/usr/bin/python -u
# -*- coding: utf-8 -*-

from amazonCheckTrans import strings as s
from amazonCheckLib import get_min_price, get_avg_price, get_max_price, get_info_for, get_time, notify, print_help_text, print_notification, shorten_amazon_link, TimeoutException
from colors import BOLD_WHITE, BLUE, GREEN, RED, YELLOW, NOCOLOR

import pygtk
pygtk.require( '2.0' )
import gtk
import gobject
from multiprocessing import Process

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



class MainWindow:
    def destroy( self, wigdet, data=None):
        gtk.main_quit()


    def __init__( self ):
        #Setting up the Liststore
        self.data_store = gtk.ListStore( bool, str, str, str, str, str, str )

        #Setting up the TreeView
        self.data_view = gtk.TreeView( self.data_store )

        toggle_renderer = gtk.CellRendererToggle()
        toggle_renderer.connect( 'toggled', self.toggle_handler )

        text_renderer = gtk.CellRendererText()

        self.data_view.append_column( gtk.TreeViewColumn( '',         toggle_renderer,  active=0 ) )
        self.data_view.append_column( gtk.TreeViewColumn( 'Currency', text_renderer,    text=1 ) )
        self.data_view.append_column( gtk.TreeViewColumn( 'Price',    text_renderer,    text=2 ) )
        self.data_view.append_column( gtk.TreeViewColumn( 'Minimum',  text_renderer,    text=3 ) )
        self.data_view.append_column( gtk.TreeViewColumn( 'Average',  text_renderer,    text=4 ) )
        self.data_view.append_column( gtk.TreeViewColumn( 'Maximum',  text_renderer,    text=5 ) )
        self.data_view.append_column( gtk.TreeViewColumn( 'Title',    text_renderer,    text=6 ) )

        #Fill the TreeView
        ( links, titles, currencies, not_used, prices ) = read_data_file()

        self.update_list_store( links, titles, currencies, prices )

        #Setting up control buttons
        self.add_button = gtk.Button( 'Add' )
        self.delete_button = gtk.Button( 'Delete' )
        self.op_mode_change_button = gtk.Button( 'Change' )

        #Setting up the GUI boxes
        self.outer_layer = gtk.VBox()
        self.inner_layer = gtk.HBox()

        #Setting up inner layer
        self.inner_layer.pack_start( self.add_button,            False, False, 5 )
        self.inner_layer.pack_start( self.delete_button,         False, False, 5 )
        self.inner_layer.pack_start( self.op_mode_change_button, False, False, 5 )

        #Setting up outer layer

        self.outer_layer.pack_start( self.data_view )
        self.outer_layer.pack_start( self.inner_layer, False, False, 5 )

        #Setting up the main window
        self.window = gtk.Window( gtk.WINDOW_TOPLEVEL )
        self.window.connect( 'destroy', self.destroy )

        self.window.add( self.outer_layer )
        self.window.show_all()

        #Setting up the data thread
        self.data_refresher = gobject.timeout_add( 5000, Process( None, self.refresh_data, None, [], {} ).start )


    def toggle_handler( self, widget, data=None ):
        pass


    def refresh_data( self ):
        #Reading data
        print( 'running' )

        ( links, titles, currencies, pictures, prices ) = read_data_file()

        if len( links ) == 0:
            write_log_file( s[ 'dat-empty' ] )
            exit( s[ 'dat-empty' ] )

        sleeptime = MIN_SLEEP_TIME
        avgs = []
        mins = []
        maxs = []
        progs = []

        #runs = runs + 1

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

        self.update_list_store( links, titles, currencies, prices )

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

        #sleep( sleeptime )

        return True


    def update_list_store( self, links, titles, currencies, prices ):
        #print( BOLD_WHITE + s[ 'show-head' ] + NOCOLOR )
#
        #color_min = GREEN
        #color_max = RED
        #color_avg = YELLOW
#
        #color_plain = NOCOLOR
#
        #color_price = NOCOLOR
#
        #print( '' )

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

            try:
                self.data_store[ index ][2] = price
                self.data_store[ index ][3] = mins
                self.data_store[ index ][4] = avgs
                self.data_store[ index ][5] = maxs
            except IndexError:
                self.data_store.append( [ False, currencies[ index ], price, mins, avgs, maxs, titles[ index ] ] )




            #if maxs == mins:
                #color_price = NOCOLOR
#
            #elif price == mins:
                #color_price = BLUE
#
            #elif price > avgs:
                #color_price = RED
#
            #elif price < avgs:
                #color_price = GREEN



            #print( str( currencies[ index ] ) + '\t' + color_price + str( price ) + '\t' + color_min + str( mins ) + '\t' + color_avg + str( avgs ) + '\t' + color_max + str( maxs ) + '\t' + color_plain + titles[ index ] )
#
        #print( '' )


    def main( self ):
        gtk.main()

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



def process_arguments( argv ):
    [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ] = read_config_file()

    add_activated = False
    operation_mode = False
    write_config = False

    for argument in argv:
        write_log_file( s[ 'prgm-clld' ] + ' \'' + argument + '\'' )

        #Add articles
        if argument == 'add' or argument == '-a' or argument == '--add':
            add_activated = True
            continue

        if argument.find( 'amazon' ) != -1 and add_activated:
            url = shorten_amazon_link( argument )
            write_log_file( s[ 'add-artcl' ] + url )
            add_article( url )
            continue

        #Determine operation mode
        if argument == 'delete' or argument == '-d' or argument == '--delete':
            operation_mode = 'delete_mode'
            continue

        if argument == 'show' or argument == '--show':
            operation_mode = 'show_mode'
            continue

        if argument == 'help' or argument == '-h' or argument == '--help':
            operation_mode = 'help_mode'
            continue

        #Determine output mode
        if argument == '-s' or argument == '--silent':

            ( SILENT, VERBOSE, UPDATES_ONLY ) = ( True, False, False )

            write_config = True
            write_log_file( s[ 'ch-silent' ], True )
            continue

        if argument == '-v' or argument == '--verbose':

            ( SILENT, VERBOSE, UPDATES_ONLY ) = ( False, True, True )

            write_config = True
            write_log_file( s[ 'ch-verbos' ], True )
            continue

        if argument == '-u' or argument == '--updates_only':

            ( SILENT, VERBOSE, UPDATES_ONLY ) = ( False, False, True )

            write_config = True
            write_log_file( s[ 'ch-updonl' ], True )
            continue

        #Determine sleep times
        if argument.find( '--min_sleep=' ) != -1:
            try:
                MIN_SLEEP_TIME = int( argument[ 12 : ] )

                write_config = True
                write_log_file( s[ 'ch-mn-slp' ] + str( MIN_SLEEP_TIME ), True )
            except ValueError:
                write_log_file( s[ 'mn-slpnan' ], True )

            continue

        if argument.find( '--max_sleep=' ) != -1:
            try:
                MAX_SLEEP_TIME = int( argument[ 12 : ] )

                write_config = True
                write_log_file( s[ 'ch-mx-slp' ] + str( MAX_SLEEP_TIME ), True )
            except ValueError:
                write_log_file( s[ 'mx-slpnan' ], True )

            continue

        #Illegal Argument
        write_log_file( s[ 'ill-argmt' ] + '\'' + argument + '\'', True )
        continue

    #Write config file if necessary
    if write_config:
        write_config_file( [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ] )

    #Act on operation mode ( or not )
    if operation_mode == 'delete_mode':
        write_log_file( s[ 'sh-del-mn' ] )

        print_delete_menu()

        write_log_file( s[ 'pg-hlt-op' ] )
        write_log_file( s[ 'dashes' ] )
        exit(0)

    if operation_mode == 'show_mode':
        ( not_used, titles, currencies, not_used, prices ) = read_data_file()

        write_log_file( s[ 'sh-art-ls'] )

        print_result( titles, currencies, prices )

        write_log_file( s[ 'pg-hlt-op' ] )
        write_log_file( s[ 'dashes' ] )
        exit(0)

    if operation_mode == 'help_mode':
        write_log_file( s[ 'sh-hlp-mn' ] )

        print_help_text()

        write_log_file( s[ 'pg-hlt-op' ] )
        write_log_file( s[ 'dashes' ] )
        exit(0)

    if operation_mode == False and add_activated == False:
        return



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

    signal( SIGALRM, timeout_handler )

    runs = 0

    process_arguments( argv )

    [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ] = read_config_file()

    try:

        write_log_file( s[ 'str-mn-lp' ] )

        mywindow = MainWindow()
        mywindow.main()

    except KeyboardInterrupt:
        write_log_file( s[ 'pg-hlt-us' ], True )
        write_log_file( s[ 'exit-norm' ], True )
        write_log_file( s[ 'dashes' ] )
        exit(0)
    #except:
        #write_log_file( 'Something went wrong' )
        #write_log_file( 'Exited abnormally' )
        #exit(1)

