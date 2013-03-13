#!/usr/bin/python -u
# -*- coding: utf-8 -*-

from amazonCheckTrans import strings as s
from amazonCheckLib import get_min_price, get_avg_price, get_max_price, get_info_for, get_time, notify, print_help_text, print_notification, shorten_amazon_link
from colors import BOLD_WHITE, BLUE, GREEN, RED, YELLOW, NOCOLOR
import pygtk
pygtk.require( '2.0' )
import gtk
import gobject
import threading
import appindicator
from webbrowser import open as open_in_browser
from os.path import exists, expanduser
from urllib import urlopen
from time import ctime, time, sleep
from json import dumps, loads
from sys import argv, exit
from re import search
from os import name


gtk.gdk.threads_init()
gobject.threads_init()


if name == 'nt':
    IMAGE_WRITE_MODE = 'wb'
else:
    IMAGE_WRITE_MODE = 'w'


CONFIG_FILE = expanduser( '~/.amazonCheck/aC.config' )
DATA_FILE = expanduser( '~/.amazonCheck/aC.data' )
LOG_FILE = expanduser( '~/.amazonCheck/aC.log' )
ICON_FILE = expanduser( '~/.amazonCheck/aC.png' )

IMAGE_PATH = expanduser( '~/.amazonCheck/pics/' )

SILENT = False
UPDATES_ONLY = False
VERBOSE = True

MIN_SLEEP_TIME = 180
MAX_SLEEP_TIME = 300
TIMEOUT_TIME = 5

SLEEP_TIME = 2

CONFIG_VARS = 5

open( LOG_FILE, 'w' ).close()


class RefreshThread( threading.Thread ):
    def __init__( self, wind_obj ):
        self.stop_flag = False
        self.wind_obj = wind_obj
        threading.Thread.__init__(self)


    def stop( self ):
        self.stop_flag = True


    def run( self ):
        global SLEEP_TIME, VERBOSE, SILENT

        write_log_file( 'Refresh Thread ' + str( threading.active_count() - 1 ) + ' started', True )

        runs = 0

        while not self.stop_flag:
            #Reading data
            ( links, titles, currencies, pictures, prices ) = read_data_file()

            start_time = time()

            if len( links ) == 0:
                write_log_file( s[ 'dat-empty' ], True )

            runs = runs + 1

            write_log_file( 'Thread ' + str( threading.active_count() - 1 ) + ': ' + s[ 'strtg-run' ] + str( runs ) + ':', True )

            #Updates the information

            write_log_file( s[ 'getng-dat' ], True )

            for index in range( 0, len( links ) ):
                if self.stop_flag:
                    write_log_file( 'Halted Refresh Thread ' + str( threading.active_count() - 1 ), True )
                    return

                info = get_info_for( links[ index ] )

                if info == ( -1, -1, -1, -1 ):
                    write_log_file( s[ 'err-con-s' ], True )
                    write_log_file( s[ 'artcl-skp' ] + str( links[ index ] ), True )
                    continue
                elif info == ( -2, -2, -2, -2 ):
                    write_log_file( 'ValueError happened', True )
                    write_log_file( s[ 'artcl-skp' ] + str( links[ index ] ), True )
                    continue

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

                        try:
                            notify( title, body, IMAGE_PATH + pictures[ index ] )

                            if VERBOSE:
                                print_notification( title, body, '' )
                        except:
                            print_notification( title, body, '' )

                    prices[ index ].append( [ info[2], int( round( time() ) ) ] )

            #Saving data to file

            write_log_file( s[ 'svng-data' ], True )

            write_data_file( links, titles, currencies, pictures, prices )

            #End time

            end_time = time()

            #Calculating the length of operating

            diff_time = round( end_time - start_time, 2 )

            write_log_file( s[ 'it-took' ] + str( int( diff_time ) ) + s[ 'seconds' ], True )

            #Calculating sleeptime

            if 2 * diff_time > MAX_SLEEP_TIME:
                SLEEP_TIME = MAX_SLEEP_TIME
            elif 2 * diff_time < MIN_SLEEP_TIME:
                SLEEP_TIME = MIN_SLEEP_TIME
            else:
                SLEEP_TIME = int( 2 * diff_time )

            #Sleeping for agreed amount

            write_log_file( s[ 'sleep-for' ] + str( int( round( SLEEP_TIME ) ) ) + s[ 'seconds' ], True )

            gobject.idle_add( self.wind_obj.update_list_store )

            if self.stop_flag:
                write_log_file( 'Refresh Thread ' + str( threading.active_count() - 1 ) + ' was halted before sleeping', True )
                return

            for i in range( 0, 10 * SLEEP_TIME ):
                if not self.stop_flag:
                    sleep( 1/10. )
                else:
                    write_log_file( 'Refresh Thread ' + str( threading.active_count() - 1 ) + ' was halted while sleeping', True )
                    return

        write_log_file( 'Refresh-Thread ' + str( threading.active_count() - 1 ) + ' was stopped' )


class MainWindow:
    def exit_application( self, widget ):
        self.window.set_visible( False )
        self.refresh_thread.stop()
        gtk.main_quit()

    def toggle_window_visibility( self, widget ):
        if self.window_visible:
            self.window.set_visible( False )
            self.window_visible = False
            self.indicator.get_menu().get_children()[0].set_label( 'Show Window' )
        else:
            self.window.set_visible( True )
            self.window_visible = True
            self.indicator.get_menu().get_children()[0].set_label( 'Hide Window' )


    def __init__( self ):
        self.window_visible = True
        #Setting up the indicator
        self.indicator = appindicator.Indicator( 'amazonCheck-indicator', 'amazonCheck', appindicator.CATEGORY_APPLICATION_STATUS, '/usr/share/pixmaps/' )
        self.indicator.set_status( appindicator.STATUS_ACTIVE )

        indicator_menu = gtk.Menu()

        menu_item_show = gtk.MenuItem( 'Hide window' )
        menu_item_exit = gtk.MenuItem( 'Exit' )
        menu_item_show.connect( 'activate', self.toggle_window_visibility )
        menu_item_exit.connect( 'activate', self.exit_application )

        indicator_menu.append( menu_item_show )
        indicator_menu.append( menu_item_exit )

        indicator_menu.show_all()

        self.indicator.set_menu( indicator_menu )

        #Setting up the Liststore
        self.data_store = gtk.ListStore( bool, str, str, str, str, str, str )

        #Setting up the TreeView
        self.data_view = gtk.TreeView( self.data_store )

        toggle_renderer = gtk.CellRendererToggle()
        toggle_renderer.connect( 'toggled', self.toggle_handler )

        currency_renderer = gtk.CellRendererText()
        price_renderer = gtk.CellRendererText()
        title_renderer = gtk.CellRendererText()
        min_renderer = gtk.CellRendererText()
        avg_renderer = gtk.CellRendererText()
        max_renderer = gtk.CellRendererText()

        #self.data_view.connect( 'row-activated', self.visit_page )

        min_renderer.set_property( 'foreground', '#27B81F' )
        avg_renderer.set_property( 'foreground', '#FCCA00' )
        max_renderer.set_property( 'foreground', '#FF3D3D' )

        self.data_view.append_column( gtk.TreeViewColumn( '',         toggle_renderer,   active=0 ) )
        self.data_view.append_column( gtk.TreeViewColumn( 'Currency', currency_renderer, text=1 ) )
        self.data_view.append_column( gtk.TreeViewColumn( 'Price',    price_renderer,    markup=2 ) )
        self.data_view.append_column( gtk.TreeViewColumn( 'Minimum',  min_renderer,      text=3 ) )
        self.data_view.append_column( gtk.TreeViewColumn( 'Average',  avg_renderer,      text=4 ) )
        self.data_view.append_column( gtk.TreeViewColumn( 'Maximum',  max_renderer,      text=5 ) )
        self.data_view.append_column( gtk.TreeViewColumn( 'Title',    title_renderer,    markup=6 ) )

        #Fill the TreeView
        ( links, titles, currencies, not_used, prices ) = read_data_file()

        self.update_list_store()

        #Setting up text box for add_article
        self.add_text_box = gtk.Entry( 0 )

        #Setting up control buttons
        self.visit_button = gtk.Button( 'Visit' )
        self.visit_button.connect( 'clicked', self.visit_page )

        self.add_button = gtk.Button( 'Add' )
        self.add_button.connect( 'clicked', self.add_article )

        self.delete_button = gtk.Button( 'Delete' )
        self.delete_button.connect( 'clicked', self.delete_selection )

        self.op_mode_change_button = gtk.Button()

        if VERBOSE:
            self.op_mode_change_button.set_label( 'Verbose' )
        elif SILENT:
            self.op_mode_change_button.set_label( 'Silent' )

        self.op_mode_change_button.connect( 'clicked', self.change_op_mode )

        #Setting up the GUI boxes
        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_size_request( 640, 480 )
        self.scroll.add( self.data_view )

        self.outer_layer = gtk.VBox()
        self.inner_layer = gtk.HBox()

        #Setting up inner layer
        self.inner_layer.pack_start( self.visit_button,          False, False, 5 )
        self.inner_layer.pack_start( self.delete_button,         False, False, 5 )
        self.inner_layer.pack_start( self.op_mode_change_button, False, False, 5 )
        self.inner_layer.pack_start( self.add_button,            False, False, 5 )
        self.inner_layer.pack_start( self.add_text_box,          True,  True,  5 )

        #Setting up outer layer
        self.outer_layer.pack_start( self.scroll )
        self.outer_layer.pack_start( self.inner_layer,           False, False, 5 )

        #Setting up the main window
        self.window = gtk.Window( gtk.WINDOW_TOPLEVEL )
        self.window.connect( 'destroy', self.exit_application )

        self.window.set_icon_from_file( ICON_FILE )
        self.window.set_title( 'amazonCheck - Monitor your favorite books, movies, games...' )

        self.window.add( self.outer_layer )

        self.window.show_all()

        #Hide text box
        self.add_text_box.hide()

        #Setting up refresh thread
        self.refresh_thread = RefreshThread( self )


    def change_op_mode( self, widget ):
        global VERBOSE
        global SILENT

        if VERBOSE:
            self.op_mode_change_button.set_label( 'Silent' )
        if SILENT:
            self.op_mode_change_button.set_label( 'Verbose' )

        VERBOSE = not VERBOSE
        SILENT = not SILENT


    def add_article( self, widget ):
        self.add_text_box.set_visible( not self.add_text_box.get_visible() )

        if self.add_text_box.get_visible():
            return

        url = shorten_amazon_link( self.add_text_box.get_text() )

        self.add_text_box.set_text( '' )

        data_file = open( DATA_FILE, 'a' )

        ( title, currency, price, pic_url ) = get_info_for( url )

        if ( title, currency, price, pic_url ) == ( -1, -1, -1, -1 ):
            write_log_file( s[ 'err-con-s' ], True )
            return False
        elif ( title, currency, price, pic_url ) == ( -2, -2, -2, -2 ):
            write_log_file( 'ValueError happened', True )
            return False

        self.refresh_thread.stop()

        pic_name = search( '\/[A-Z0-9]{10}\/', url ).group()[1: -1] + '.jpg'

        open( IMAGE_PATH + pic_name, IMAGE_WRITE_MODE ).write( urlopen( pic_url ).read() )

        self.refresh_thread.join()

        try:
            data_file.write( dumps( [ url, title, currency, pic_name, [ [ price, int( round( time() ) ) ] ] ] ) + '\n' )
        except UnicodeDecodeError:
            data_file.write( dumps( [ url, s[ 'err-gener' ], currency, pic_name, [ [ price, int( round( time() ) ) ] ] ] )  + '\n' )
            write_log_file( 'Title could not get written: ' + title )

        data_file.close()

        self.update_list_store()

        self.start_thread()


    def start_thread( self ):
        self.refresh_thread = RefreshThread( self )
        self.refresh_thread.start()



    def toggle_handler( self, widget, path ):
        self.data_store[path][0] = not self.data_store[path][0]


    def delete_selection( self, widget ):
        delete_queue = []

        tree_length = len( self.data_store )

        for index in range( 0, tree_length ):
            index = tree_length - 1 - index
            if self.data_store[ index ][0] == True:
                delete_queue.append( index )

        if len( delete_queue ) == 0:
            return False

        self.refresh_thread.stop()

        ( links, titles, currencies, pictures, prices ) = read_data_file()

        for index in delete_queue:
            links.pop( index )
            titles.pop( index )
            currencies.pop( index )
            pictures.pop( index )
            prices.pop( index )

            self.data_store.remove( self.data_store.get_iter( index ) )

        write_data_file( links, titles, currencies, pictures, prices )

        self.refresh_thread.join()
        self.start_thread()


    def visit_page( self, widget ):
        ( links, titles, currencies, pictures, prices ) = read_data_file()

        tree_length = len( self.data_store )

        for index in range( 0, tree_length ):
            index = tree_length - 1 - index
            if self.data_store[ index ][0] == True:
                open_in_browser( links[ index ] )


    def update_list_store( self ):
        write_log_file( 'Gui is updating', True )

        ( links, titles, currencies, pictures, prices ) = read_data_file()

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
                color = '<span>'

            elif price == mins:
                color = '<span foreground="#0000C7">'

            elif price > avgs:
                color = '<span foreground="#FF3D3D">'

            elif price < avgs:
                color = '<span foreground="#27B81F">'

            elif price == avgs:
                color = '<span foreground="#FCCA00">'

            if mins != s[ 'N/A' ]:
                mins = '%.2f' % mins

            if maxs != s[ 'N/A' ]:
                maxs = '%.2f' % maxs

            if avgs != s[ 'N/A' ]:
                avgs = '%.2f' % avgs

            if price != s[ 'N/A' ]:
                price = '%.2f' % price

            try:
                self.data_store[ index ][2] = color + str( price ) + '</span>'
                self.data_store[ index ][3] = mins
                self.data_store[ index ][4] = avgs
                self.data_store[ index ][5] = maxs
            except IndexError:
                self.data_store.append( [ False, currencies[ index ], color + str( price ) + '</span>', mins, avgs, maxs, titles[ index ] ] )

        write_log_file( 'Gui updated', True )


    def main( self ):
        #Starting the data thread
        self.start_thread()
        try:
            gtk.main()
        except KeyboardInterrupt:
            write_log_file( 'Gui crashed', True )
            self.refresh_thread.stop()
            self.refresh_thread.join()


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
            print( titles[ index ] )

    data_file.close()



def write_log_file( string, output=False ):
    if VERBOSE and output:
        print( get_time() + ' ' + string + '\n' ),

    try:
        logfile = open( LOG_FILE, 'a' )

    except IOError:
        print( s[ 'log-no-pm' ] )
        return false

    logfile.write( get_time() + ' ' + string + '\n' )
    logfile.close()

#-----------------------------------------------------------------------
#-----------------------------------------------------------------------


if __name__ == '__main__':
    write_log_file( s[ 'dashes' ] )
    write_log_file( s[ 'str-prgm' ] )

    [ SILENT, UPDATES_ONLY, VERBOSE, MIN_SLEEP_TIME, MAX_SLEEP_TIME ] = read_config_file()

    write_log_file( s[ 'str-mn-lp' ] )

    mywindow = MainWindow()
    mywindow.main()

#except KeyboardInterrupt:
    #write_log_file( s[ 'pg-hlt-us' ], True )
    #write_log_file( s[ 'exit-norm' ], True )
    #write_log_file( s[ 'dashes' ] )
    #exit(0)
#except:
    #write_log_file( 'Something went wrong' )
    #write_log_file( 'Exited abnormally' )
    #exit(1)

