#!/usr/bin/python2.7 -u
# -*- coding: utf-8 -*-

from sys import version_info, exit

if version_info >= (2, 8):
    exit( '--Please use Python 2.7 with this program--' )

from amazonCheckTrans import strings as s
from amazonCheckLib import get_min_price, get_avg_price, get_max_price, get_info_for, get_time, notify, print_help_text, print_notification, shorten_amazon_link
from colors import BOLD_WHITE, BLUE, GREEN, RED, YELLOW, NOCOLOR

import pygtk
pygtk.require( '2.0' )
import gtk
import gobject

from dbus.mainloop.glib import DBusGMainLoop
from appindicator import Indicator, STATUS_ACTIVE, STATUS_PASSIVE, STATUS_ATTENTION, CATEGORY_APPLICATION_STATUS
from dbus.service import Object as dbusServiceObject, BusName, method as dbusServiceMethod
from webbrowser import open as open_in_browser
from threading import Thread, active_count
from os.path import exists, expanduser
from urllib import urlopen
from time import ctime, time, sleep
from json import dumps, loads
from dbus import SessionBus
from sys import argv, exit
from re import search
from os import name, remove


CONFIG_FILE = expanduser( '~/.amazonCheck/aC.config' )
DATA_FILE = expanduser( '~/.amazonCheck/aC.data' )
LOG_FILE = expanduser( '~/.amazonCheck/aC.log' )
ICON_FILE = expanduser( '~/.amazonCheck/aC.png' )

IMAGE_WRITE_MODE = 'w'
IMAGE_PATH = expanduser( '~/.amazonCheck/pics/' )

SHOW_NOTIFICATIONS = True
SHOW_DEL_DIALOG = True
ALTERNATING_ROW_COLOR = True

MIN_SLEEP_TIME = 180
MAX_SLEEP_TIME = 300
TIMEOUT_TIME = 5

SLEEP_TIME = 2

CONFIG_VARS = 5

SERVICE_NAME = 'org.amazonCheck.alive'


DBusGMainLoop( set_as_default = True )


for service_name in SessionBus().list_names():
    if service_name == SERVICE_NAME:
        to_execute = SessionBus().get_object( SERVICE_NAME, '/alive' ).get_dbus_method( 'toggle_window', SERVICE_NAME )

        to_execute()

        exit( 'Program already running' )


gtk.gdk.threads_init()
gobject.threads_init()


open( LOG_FILE, 'w' ).close()


class DBusService( dbusServiceObject ):
    def __init__( self, wind_obj ):
        self.wind_obj = wind_obj
        self.bus_name = BusName( SERVICE_NAME, bus=SessionBus() )
        dbusServiceObject.__init__( self, self.bus_name, '/alive' )


    @dbusServiceMethod( SERVICE_NAME )
    def toggle_window( self ):
        self.wind_obj.toggle_window_visibility()


class RefreshThread( Thread ):
    def __init__( self, wind_obj ):
        self.stop_flag = False
        self.wind_obj = wind_obj
        Thread.__init__( self )


    def stop( self ):
        self.stop_flag = True


    def run( self ):
        global SLEEP_TIME, ALTERNATING_ROW_COLOR, SHOW_NOTIFICATIONS

        write_log_file( 'Refresh Thread ' + str( active_count() - 1 ) + ' started', True )

        runs = 0

        while not self.stop_flag:
            #Reading data
            ( links, titles, currencies, pictures, prices ) = read_data_file()

            start_time = time()

            if len( links ) == 0:
                write_log_file( s[ 'dat-empty' ], True )

            runs = runs + 1

            write_log_file( 'Thread ' + str( active_count() - 1 ) + ': ' + s[ 'strtg-run' ] + str( runs ) + ':', True )

            #Updates the information

            write_log_file( s[ 'getng-dat' ], True )

            for index in range( 0, len( links ) ):
                if self.stop_flag:
                    write_log_file( s[ 'svng-data' ], True )
                    write_data_file( links, titles, currencies, pictures, prices )

                    write_log_file( 'Halted Refresh Thread ' + str( active_count() - 1 ), True )

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
                elif info == ( -3, -3, -3, -3 ):
                    write_log_file( 'Shipping couldn\'t be determined.', True )
                    write_log_file( s[ 'artcl-skp' ] + str( links[ index ] ), True )
                    continue
                elif info == None:
                    write_log_file( 'Unknown Error occured.', True )
                    write_log_file( s[ 'artcl-skp' ] + str( links[ index ] ), True )
                    continue

                if info[2] != 'N/A':
                    current_price = round( info[2], 2 )
                else:
                    current_price = info[2]

                if current_price == prices[ index ][-1][0]:
                    pass
                else:
                    open( IMAGE_PATH + self.wind_obj.picture_dict[ titles[ index ] ], IMAGE_WRITE_MODE ).write( urlopen( info[3] ).read() )

                    if prices[ index ][-1][0] == s[ 'N/A' ] and not current_price == s[ 'N/A' ]:
                        title = s[ 'bec-avail' ] + NOCOLOR + ':'

                    elif current_price == s[ 'N/A' ]:
                        title = s[ 'bec-unava' ] + NOCOLOR + ':'

                    elif current_price < prices[ index ][-1][0]:
                        title = s[ 'price-dwn' ] + '%.2f' % prices[ index ][-1][0] + ' > ' + '%.2f' % current_price + ' )' + NOCOLOR + ':'

                    elif current_price > prices[ index ][-1][0]:
                        title = s[ 'price-up' ] + '%.2f' % prices[ index ][-1][0] + ' > ' + '%.2f' % current_price + ' )' + NOCOLOR + ':'

                    body = str( info[0] ).decode( 'ascii', 'ignore' )

                    if SHOW_NOTIFICATIONS:
                        notify( title, body, IMAGE_PATH + pictures[ index ] )

                    print_notification( title, body, '' )
                    gobject.idle_add( self.wind_obj.set_indicator_attention )
                    prices[ index ].append( [ current_price, int( round( time() ) ) ] )
                    self.wind_obj.price_dict[ info[0].decode( 'ascii', 'ignore' ) ].append( [ current_price, int( round( time() ) ) ] )

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
                write_log_file( 'Refresh Thread ' + str( active_count() - 1 ) + ' was halted before sleeping', True )
                return

            for i in range( 0, 10 * SLEEP_TIME ):
                if not self.stop_flag:
                    sleep( 1/10. )
                else:
                    write_log_file( 'Refresh Thread ' + str( active_count() - 1 ) + ' was halted while sleeping', True )
                    return

        write_log_file( 'Refresh-Thread ' + str( active_count() - 1 ) + ' was stopped' )


class MainWindow:
    def __init__( self ):
        #Setting up the toolbar
        toolbar = gtk.Toolbar()
        toolbar.set_orientation( gtk.ORIENTATION_VERTICAL )
        toolbar.set_style( gtk.TOOLBAR_ICONS )

        image = gtk.Image(); image.set_from_stock( gtk.STOCK_ADD, gtk.ICON_SIZE_LARGE_TOOLBAR )
        toolbar.append_item( None, 'Add', None, image, self.on_add_article )

        image = gtk.Image(); image.set_from_stock( gtk.STOCK_REMOVE, gtk.ICON_SIZE_LARGE_TOOLBAR )
        toolbar.append_item( None, 'Remove', None, image, self.on_delete_articles )

        image = gtk.Image(); image.set_from_stock( gtk.STOCK_PREFERENCES, gtk.ICON_SIZE_LARGE_TOOLBAR )
        toolbar.append_item( None, 'Config', None, image, self.on_show_config_window )


        #Setting up the data holding dictionary
        self.link_dict = {}
        self.currency_dict = {}
        self.price_dict = {}
        self.picture_dict = {}


        #Setting up the dbus service
        self.dbus_service = DBusService( self )


        #Setting up config window
        self.config_window = gtk.Window( gtk.WINDOW_TOPLEVEL )
        self.config_window.set_position( gtk.WIN_POS_CENTER  )
        self.config_window.set_resizable( False )
        self.config_window.set_modal(     True  )
        self.config_window.connect( 'delete-event', self.on_config_cancel )

        config_outer_layer = gtk.VBox()
        config_config_box  = gtk.VBox()
        config_button_box  = gtk.HBox()

        config_checkbutton_notifications = gtk.CheckButton()
        config_checkbutton_delete_dialog = gtk.CheckButton()
        config_checkbutton_alt_row_color = gtk.CheckButton()

        config_checkbutton_notifications.set_active( SHOW_NOTIFICATIONS    )
        config_checkbutton_delete_dialog.set_active( SHOW_DEL_DIALOG       )
        config_checkbutton_alt_row_color.set_active( ALTERNATING_ROW_COLOR )

        config_spinbutton_min_sleep = gtk.SpinButton( adjustment=gtk.Adjustment( value=MIN_SLEEP_TIME, lower=30, upper=3600, step_incr=1, page_incr=5, page_size=0 ), climb_rate=0.0, digits=0 )
        config_spinbutton_max_sleep = gtk.SpinButton( adjustment=gtk.Adjustment( value=MAX_SLEEP_TIME, lower=30, upper=3600, step_incr=1, page_incr=5, page_size=0 ), climb_rate=0.0, digits=0 )

        config_spinbutton_min_sleep.connect( 'value-changed', self.on_changed_min_sleep )
        config_spinbutton_max_sleep.connect( 'value-changed', self.on_changed_max_sleep )

        config_hbox_min_sleep = gtk.HBox()
        config_hbox_min_sleep.pack_start( gtk.Label( 'Min. Interval between updates: ' ), False, False, 5 )
        config_hbox_min_sleep.pack_start( gtk.Label( '' ),                                True,  True,  5 )
        config_hbox_min_sleep.pack_start( config_spinbutton_min_sleep,                    False, False, 5 )

        config_hbox_max_sleep = gtk.HBox()
        config_hbox_max_sleep.pack_start( gtk.Label( 'Max. Interval between updates: ' ), False, False, 5 )
        config_hbox_max_sleep.pack_start( gtk.Label( '' ),                                True,  True,  5 )
        config_hbox_max_sleep.pack_start( config_spinbutton_max_sleep,                    False, False, 5 )

        config_hbox_notifications = gtk.HBox()
        config_hbox_notifications.pack_start( gtk.Label( 'Show notification bubbles?' ),  False, False, 5 )
        config_hbox_notifications.pack_start( gtk.Label( '' ),                            True,  True,  5 )
        config_hbox_notifications.pack_start( config_checkbutton_notifications,           False, False, 5 )

        config_hbox_delete_dialog = gtk.HBox()
        config_hbox_delete_dialog.pack_start( gtk.Label( 'Confirm deleting articles?' ),  False, False, 5 )
        config_hbox_delete_dialog.pack_start( gtk.Label( '' ),                            True,  True,  5 )
        config_hbox_delete_dialog.pack_start( config_checkbutton_delete_dialog,           False, False, 5 )

        config_hbox_alt_row_color = gtk.HBox()
        config_hbox_alt_row_color.pack_start( gtk.Label( 'Alternate row colors?' ),       False, False, 5 )
        config_hbox_alt_row_color.pack_start( gtk.Label( '' ),                            True,  True,  5 )
        config_hbox_alt_row_color.pack_start( config_checkbutton_alt_row_color,           False, False, 5 )


        config_config_box.pack_start( config_hbox_min_sleep,                              False, False, 5 )
        config_config_box.pack_start( config_hbox_max_sleep,                              False, False, 5 )
        config_config_box.pack_start( config_hbox_notifications,                          False, False, 5 )
        config_config_box.pack_start( config_hbox_delete_dialog,                          False, False, 5 )
        config_config_box.pack_start( config_hbox_alt_row_color,                          False, False, 5 )

        config_button_cancel = gtk.Button( 'Cancel'     )
        config_button_ok     = gtk.Button( '    OK    ' )

        config_button_cancel.connect( 'clicked', self.on_config_cancel      )
        config_button_ok.connect(     'clicked', self.on_config_confirm     )

        config_button_box.pack_start( gtk.Label( '' ),           True,  True,  5 )
        config_button_box.pack_start( config_button_cancel,      False, False, 5 )
        config_button_box.pack_start( config_button_ok,          False, False, 5 )

        config_outer_layer.pack_start( config_config_box,        False, False, 5 )
        config_outer_layer.pack_start( gtk.Label( '' ),          True,  True,  5 )
        config_outer_layer.pack_start( config_button_box,        False, False, 5 )

        self.config_window.add( config_outer_layer )


        #Setting up the indicator
        self.indicator = Indicator( 'amazonCheck-indicator', 'amazonCheck_indicator', CATEGORY_APPLICATION_STATUS, '/usr/share/pixmaps/' )
        self.indicator.set_attention_icon( 'amazonCheck_indicator_attention' )
        self.indicator.set_status( STATUS_ACTIVE )

        menu_item_show      = gtk.MenuItem( 'Hide window' )
        menu_item_exit      = gtk.MenuItem( 'Exit'        )
        menu_item_seperator = gtk.SeparatorMenuItem()
        menu_item_reset     = gtk.MenuItem( 'Reset'       )

        menu_item_show.connect(  'activate', self.toggle_window_visibility )
        menu_item_exit.connect(  'activate', self.exit_application         )
        menu_item_reset.connect( 'activate', self.set_indicator_active     )

        indicator_menu = gtk.Menu()

        indicator_menu.append( menu_item_show      )
        indicator_menu.append( menu_item_exit      )
        indicator_menu.append( menu_item_seperator )
        indicator_menu.append( menu_item_reset     )

        indicator_menu.show_all()

        self.indicator.set_menu( indicator_menu )


        #Setting up the Liststore
        self.data_store = gtk.ListStore( bool, str, str, str, str, str, str )
        self.sortable = gtk.TreeModelSort( self.data_store )

        self.sortable.set_sort_func( 2, my_sort_function, 2 )
        self.sortable.set_sort_func( 3, my_sort_function, 3 )
        self.sortable.set_sort_func( 4, my_sort_function, 4 )
        self.sortable.set_sort_func( 5, my_sort_function, 5 )


        #Setting up the TreeView
        self.data_view = gtk.TreeView( self.sortable )
        self.data_view.set_headers_clickable( True )
        self.data_view.connect( 'row-activated',  self.on_visit_page   )
        self.data_view.connect( 'cursor-changed', self.on_row_selected )
        self.data_view.set_rules_hint( ALTERNATING_ROW_COLOR )

        toggle_renderer = gtk.CellRendererToggle()
        toggle_renderer.connect( 'toggled', self.on_cell_toggled )

        currency_renderer = gtk.CellRendererText()
        price_renderer    = gtk.CellRendererText()
        title_renderer    = gtk.CellRendererText()
        min_renderer      = gtk.CellRendererText()
        avg_renderer      = gtk.CellRendererText()
        max_renderer      = gtk.CellRendererText()

        min_renderer.set_property( 'foreground', '#27B81F' )
        avg_renderer.set_property( 'foreground', '#FCCA00' )
        max_renderer.set_property( 'foreground', '#FF3D3D' )

        toggle_column   = gtk.TreeViewColumn( '',      toggle_renderer,   active=0 )
        currency_column = gtk.TreeViewColumn( 'CY',    currency_renderer, text=1   )
        price_column    = gtk.TreeViewColumn( 'Price', price_renderer,    markup=2 )
        minimum_column  = gtk.TreeViewColumn( 'Min',   min_renderer,      text=3   )
        average_column  = gtk.TreeViewColumn( 'Avg',   avg_renderer,      text=4   )
        maximum_column  = gtk.TreeViewColumn( 'Max',   max_renderer,      text=5   )
        title_column    = gtk.TreeViewColumn( 'Title', title_renderer,    text=6 )

        toggle_column.set_sort_column_id(   0 )
        currency_column.set_sort_column_id( 1 )
        price_column.set_sort_column_id(    2 )
        minimum_column.set_sort_column_id(  3 )
        average_column.set_sort_column_id(  4 )
        maximum_column.set_sort_column_id(  5 )
        title_column.set_sort_column_id(    6 )

        self.data_view.append_column( toggle_column   )
        self.data_view.append_column( currency_column )
        self.data_view.append_column( price_column    )
        self.data_view.append_column( minimum_column  )
        self.data_view.append_column( average_column  )
        self.data_view.append_column( maximum_column  )
        self.data_view.append_column( title_column    )


        #Fill the TreeView
        ( links, titles, currencies, pictures, prices ) = read_data_file()

        for index in range( 0, len( links ) ):
            self.link_dict[ titles[index] ] = links[ index ]
            self.currency_dict[ titles[index] ] = currencies[ index ]
            self.picture_dict[ titles[index] ] = pictures[ index ]
            self.price_dict[ titles[index] ] = prices[ index ]

        self.update_list_store()


        #Setting up text box for on_add_article
        self.add_text_box = gtk.Entry( 0 )


        #Setting up the GUI boxes
        scroll = gtk.ScrolledWindow()
        scroll.set_size_request( 640, 480 )
        scroll.add( self.data_view )

        outer_layer = gtk.VBox()
        inner_layer = gtk.HBox()


        #Setting up the imagebox
        self.image_preview = gtk.Image()
        self.image_preview.set_from_file( IMAGE_PATH + 'no-pic.png' )


        #Setting up inner layer
        inner_layer.pack_start( gtk.Label( '' ),             False, False, 2  )
        inner_layer.pack_start( toolbar,                     False, False, 5  )
        inner_layer.pack_start( gtk.Label( '' ),             True,  True,  0  )
        inner_layer.pack_start( self.add_text_box,           True,  True,  5  )

        self.preview_box = gtk.HBox()
        info_box = gtk.VBox()
        title_link = gtk.Label()
        title_link.set_markup( '<a href="https://www.github.com/mchlnix/amazonCheck-Daemon">amazonCheck</a>' )

        info_box.pack_start( gtk.Label( '' ),                                 True, True, 0 )
        info_box.pack_start( title_link ,                                     False, False, 5  )
        info_box.pack_start( gtk.Label( 'Check up on your favorite stuff!' ), False, False, 5  )
        info_box.pack_start( gtk.Label( 'By Me' ),                            False, False, 5  )
        info_box.pack_start( gtk.Label( '' ),                                 True, True, 0 )

        self.preview_box.pack_start( info_box,               False, False, 5  )
        self.preview_box.pack_start( self.image_preview,     False, False, 10 )
        inner_layer.pack_start( self.preview_box,            False, False, 5 )


        #Setting up outer layer
        scroll_hbox = gtk.HBox()
        scroll_hbox.pack_start( gtk.Label( '' ),             False, False, 5  )
        scroll_hbox.pack_start( scroll,                      True,  True,  0  )
        scroll_hbox.pack_start( gtk.Label( '' ),             False, False, 5  )


        outer_layer.pack_start( scroll_hbox,                 True,  True,  0  )
        outer_layer.pack_start( inner_layer,                 False, False, 10 )


        #Setting up the main window
        self.window = gtk.Window( gtk.WINDOW_TOPLEVEL )
        self.window.set_position( gtk.WIN_POS_CENTER  )
        self.window.connect( 'delete-event',   self.toggle_window_visibility )
        self.window.connect( 'focus-in-event', self.set_indicator_active     )

        self.window.set_icon_from_file( '/usr/share/pixmaps/amazonCheck.png' )
        self.window.set_title( 'amazonCheck - Monitor your favorite books, movies, games...' )

        self.window.add( outer_layer )

        self.window.show_all()

        self.window_visible = True


        #Hide hidden widgets
        self.add_text_box.hide()

        #Set self.window as parent of config window
        self.config_window.set_transient_for( self.window )


        #Setting up refresh thread
        self.refresh_thread = RefreshThread( self )


    def main( self ):
        #Starting the data thread
        self.start_thread()

        try:
            gtk.main()

        except KeyboardInterrupt:
            write_log_file( 'Gui crashed', True )
            self.refresh_thread.stop()
            self.refresh_thread.join()


    def exit_application( self, widget ):
        self.window.set_visible( False )
        self.indicator.set_status( STATUS_PASSIVE )
        self.refresh_thread.stop()
        gtk.main_quit()


    def on_add_article( self, widget ):
        self.add_text_box.set_visible( not self.add_text_box.get_visible() )
        self.window.get_child().get_children()[1].get_children()[2].set_visible( not self.window.get_child().get_children()[1].get_children()[2].get_visible() )

        if self.add_text_box.get_visible():
            return

        url = shorten_amazon_link( self.add_text_box.get_text() )

        self.add_text_box.set_text( '' )

        data_file = open( DATA_FILE, 'a' )

        ( title, currency, price, pic_url ) = get_info_for( url )

        if ( title, currency, price, pic_url ) == ( -1, -1, -1, -1 ):
            write_log_file( s[ 'err-con-s' ], True )
            return
        elif ( title, currency, price, pic_url ) == ( -2, -2, -2, -2 ):
            write_log_file( 'ValueError happened', True )
            return

        if title in self.price_dict:
            write_log_file( 'Article already in the database', True )
            return

        self.refresh_thread.stop()

        pic_name = search( '\/[A-Z0-9]{10}\/', url ).group()[1: -1] + '.jpg'

        open( IMAGE_PATH + pic_name, IMAGE_WRITE_MODE ).write( urlopen( pic_url ).read() )

        self.refresh_thread.join()

        self.link_dict[ title ]     = url
        self.price_dict[ title ]    = [ [ price, int( round( time() ) ) ] ]
        self.currency_dict[ title ] = currency
        self.picture_dict[ title ]  = pic_name

        try:
            data_file.write( dumps( [ url, title, currency, pic_name, [ [ price, int( round( time() ) ) ] ] ] ) + '\n' )
        except UnicodeDecodeError:
            data_file.write( dumps( [ url, title.decode( 'ascii', 'ignore' ), currency, pic_name, [ [ price, int( round( time() ) ) ] ] ] )  + '\n' )

        data_file.close()

        self.update_list_store()

        self.start_thread()


    def on_cell_toggled( self, widget, path ):
        title = self.sortable[path][6]

        index = 0

        while 1:
            if self.data_store[ index ][6] == title:
                self.data_store[ index ][0] = not self.data_store[ index ][0]
                return
            index += 1


    def on_changed_max_sleep( self, widget ):
        min_spin_button = self.config_window.get_children()[0].get_children()[0].get_children()[0].get_children()[2]
        max_spin_button = self.config_window.get_children()[0].get_children()[0].get_children()[1].get_children()[2]

        if ( max_spin_button.get_value() < min_spin_button.get_value() ):
            min_spin_button.set_value( max_spin_button.get_value() )

        return


    def on_changed_min_sleep( self, widget ):
        min_spin_button = self.config_window.get_children()[0].get_children()[0].get_children()[0].get_children()[2]
        max_spin_button = self.config_window.get_children()[0].get_children()[0].get_children()[1].get_children()[2]

        if ( min_spin_button.get_value() > max_spin_button.get_value() ):
            max_spin_button.set_value( min_spin_button.get_value() )

        return


    def on_config_confirm( self, widget ):
        global SHOW_NOTIFICATIONS, SHOW_DEL_DIALOG, MIN_SLEEP_TIME, MAX_SLEEP_TIME

        checkboxes = self.config_window.get_children()[0].get_children()[0].get_children()
        min_spin_button = self.config_window.get_children()[0].get_children()[0].get_children()[0].get_children()[2]
        max_spin_button = self.config_window.get_children()[0].get_children()[0].get_children()[1].get_children()[2]

        SHOW_NOTIFICATIONS       = checkboxes[2].get_children()[2].get_active()
        SHOW_DEL_DIALOG          = checkboxes[3].get_children()[2].get_active()
        ALTERNATING_ROW_COLOR    = checkboxes[4].get_children()[2].get_active()
        MIN_SLEEP_TIME           = min_spin_button.get_value_as_int()
        MAX_SLEEP_TIME           = max_spin_button.get_value_as_int()

        self.data_view.set_rules_hint( ALTERNATING_ROW_COLOR )

        write_config_file( [ SHOW_NOTIFICATIONS, SHOW_DEL_DIALOG, ALTERNATING_ROW_COLOR, MIN_SLEEP_TIME, MAX_SLEEP_TIME ] )

        self.config_window.hide()


    def on_config_cancel( self, widget, event=None ):

        self.config_window.hide()

        checkboxes = self.config_window.get_children()[0].get_children()[0].get_children()
        min_spin_button = self.config_window.get_children()[0].get_children()[0].get_children()[0].get_children()[2]
        max_spin_button = self.config_window.get_children()[0].get_children()[0].get_children()[1].get_children()[2]

        checkboxes[2].get_children()[2].set_active( SHOW_NOTIFICATIONS    )
        checkboxes[3].get_children()[2].set_active( SHOW_DEL_DIALOG       )
        checkboxes[4].get_children()[2].set_active( ALTERNATING_ROW_COLOR )

        min_spin_button.set_value( MIN_SLEEP_TIME )
        max_spin_button.set_value( MAX_SLEEP_TIME )

        return True


    def on_delete_articles( self, widget ):

        self.on_really_delete_articles()


    def on_really_delete_articles( self, widget=None ):
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

            try:
                remove( IMAGE_PATH + pictures[ index ] )
            except OSError:
                write_log_file( 'Picture file was already deleted', True )

            del self.link_dict[ titles[ index ] ]
            del self.currency_dict[ titles[ index ] ]
            del self.picture_dict[ titles[ index ] ]
            del self.price_dict[ titles[ index ] ]

            links.pop(      index )
            titles.pop(     index )
            currencies.pop( index )
            pictures.pop(   index )
            prices.pop(     index )

            self.data_store.remove( self.data_store.get_iter( index ) )

        write_data_file( links, titles, currencies, pictures, prices )

        self.refresh_thread.join()
        self.start_thread()


    def on_reset_delete_button( self, widget=None ):
        self.window.get_children()[0].get_children()[-1].get_children()[1].show() # delete_button
        self.window.get_children()[0].get_children()[-1].get_children()[2].hide() # really_delete_button
        self.window.get_children()[0].get_children()[-1].get_children()[3].hide() # not_really_delete_button


    def on_row_selected( self, treeview ):
        try:
            title = self.data_view.get_model()[ treeview.get_selection().get_selected_rows()[1][0][0] ][-1]
            price = self.price_dict[ title ][-1][0]
            avgs = get_avg_price( self.price_dict[ title ] )
            currency = self.currency_dict[ title ]

            pixbuf = gtk.gdk.pixbuf_new_from_file( IMAGE_PATH + self.picture_dict[ title ] )

            if pixbuf.get_width() < pixbuf.get_height():
                scaled_buf = pixbuf.scale_simple( dest_width=int( pixbuf.get_width() * 100 / pixbuf.get_height()), dest_height=100, interp_type=gtk.gdk.INTERP_BILINEAR )
            else:
                scaled_buf = pixbuf.scale_simple( dest_width=100, dest_height=int( pixbuf.get_height() * 100 / pixbuf.get_width()), interp_type=gtk.gdk.INTERP_BILINEAR )

            self.image_preview.set_from_pixbuf( scaled_buf )


            if len( title ) > 55:
                disp_title = title[0:51] + '...'
            else:
                disp_title = title

            if price > avgs:
                color = '<span foreground="#FF3D3D">'

            elif price < avgs:
                color = '<span foreground="#27B81F">'

            elif price == avgs:
                color = '<span foreground="#FCCA00">'

            if price != 'N/A':
                price = color + '%.2f</span>' % price
            else:
                currency = ''

            last_3_prices = '    '

            limit = min( len( self.price_dict[ title ] ), 3 )

            for i in range( 0, limit ):
                temp_price = self.price_dict[ title ][-limit + i][0]

                if temp_price == 'N/A':
                    last_3_prices += '<span color="#FF3D3D">' + 'N/A' + '</span>'
                else:
                    if temp_price > avgs:
                        color = '<span foreground="#FF3D3D">'

                    elif temp_price < avgs:
                        color = '<span foreground="#27B81F">'

                    elif temp_price == avgs:
                        color = '<span foreground="#FCCA00">'

                    last_3_prices += color + '%.2f</span>' % temp_price

                if not i == min( len( self.price_dict[ title ] ), 3 ) - 1:
                    last_3_prices += ' > '


            self.preview_box.get_children()[0].get_children()[1].set_markup( '<a href="' + self.link_dict[ title ] + '">' + disp_title.replace( '&', '&amp;' ) + '</a>' )
            self.preview_box.get_children()[0].get_children()[2].set_markup( 'Current price: ' + '<u>' + price + '</u> ' + currency )
            self.preview_box.get_children()[0].get_children()[3].set_markup( last_3_prices )



        except IndexError:
            pass


    def on_show_config_window( self, widget ):
        self.config_window.show_all()


    def on_visit_page( self, widget, path, column ):
        if column.get_title() == '':
            return

        open_in_browser( self.link_dict[ self.data_view.get_model()[ path ][-1] ] )


    def set_indicator_active( self, widget, direction=None ):
        self.indicator.get_menu().get_children()[3].set_sensitive( False )
        self.indicator.set_status( STATUS_ACTIVE )


    def set_indicator_attention( self ):
        self.indicator.get_menu().get_children()[3].set_sensitive( True )
        self.indicator.set_status( STATUS_ATTENTION )


    def start_thread( self ):
        self.refresh_thread = RefreshThread( self )
        self.refresh_thread.start()


    def toggle_window_visibility( self, widget=None, event=None ):
        if self.window.get_visible():
            self.window.set_visible( False )
            self.indicator.get_menu().get_children()[0].set_label( 'Show Window' )
        else:
            self.window.set_visible( True )
            self.update_list_store()
            self.indicator.set_status( STATUS_ACTIVE )
            self.indicator.get_menu().get_children()[0].set_label( 'Hide Window' )

        return True


    def update_list_store( self ):
        write_log_file( 'Gui is updating', True )

        ( links, titles, currencies, pictures, prices ) = read_data_file()

        for index in range( 0, len( titles ) ):
            price = self.price_dict[ titles[ index ] ][-1][0]

            if len( prices[ index ] ) == 1:
                avgs = self.price_dict[ titles[ index ] ][0][0]
                mins = self.price_dict[ titles[ index ] ][0][0]
                maxs = self.price_dict[ titles[ index ] ][0][0]
                #progs = prices
            else:
                avgs = get_avg_price( self.price_dict[ titles[ index ] ] )
                if avgs == -1: avgs = s[ 'N/A' ]
                mins = get_min_price( self.price_dict[ titles[ index ] ] )
                if mins == -1: mins = s[ 'N/A' ]
                maxs = get_max_price( self.price_dict[ titles[ index ] ] )
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
                for store_index in range( 0, len( titles ) ):
                    if self.data_store[ store_index ][6] == titles[ index ]:
                        self.data_store[ store_index ][2] = color + str( price ) + '</span>'
                        self.data_store[ store_index ][3] = mins
                        self.data_store[ store_index ][4] = avgs
                        self.data_store[ store_index ][5] = maxs
                        break

            except IndexError:
                self.data_store.append( [ False, currencies[ index ], color + str( price ) + '</span>', mins, avgs, maxs, titles[ index ] ] )

        write_log_file( 'Gui updated', True )



def my_sort_function( treemodel, iter1, iter2, index ):
    try:
        float1 = treemodel[iter1][index]
        float2 = treemodel[iter2][index]

        try:
            if float1.find( 'N/A' ) != -1:
                return 1
            elif float2.find( 'N/A' ) != -1:
                return -1
        except:
            print iter1, iter2
            return -1

        float1 = float( float1[ float1.find( '>' ) + 1 : float1.find( '<', 1 ) ] )
        float2 = float( float2[ float2.find( '>' ) + 1 : float2.find( '<', 1 ) ] )

        if float1 > float2:
            return -1
        elif float1 < float2:
            return 1
        else:
            return 0

    except ValueError:
        return 0



def read_config_file():
    if not exists( CONFIG_FILE ):

        reset_config_file()

        return [ SHOW_NOTIFICATIONS, SHOW_DEL_DIALOG, ALTERNATING_ROW_COLOR, MIN_SLEEP_TIME, MAX_SLEEP_TIME ]

    try:
        config_file = open( CONFIG_FILE, 'r' )
    except IOError:
        write_log_file( s[ 'cnf-no-pm' ], True )
        write_log_file( s[ 'us-def-op' ], True )
        return [ SHOW_NOTIFICATIONS, SHOW_DEL_DIALOG, ALTERNATING_ROW_COLOR, MIN_SLEEP_TIME, MAX_SLEEP_TIME ]

    try:
        options = loads( config_file.read() )
    except ValueError:
        reset_config_file()
        return [ SHOW_NOTIFICATIONS, SHOW_DEL_DIALOG, ALTERNATING_ROW_COLOR, MIN_SLEEP_TIME, MAX_SLEEP_TIME ]

    write_log_file( s[ 'rd-cf-fil' ] + CONFIG_FILE )

    if type( options[ 0 ] ) != type( True ) or type( options[ 1 ] ) != type( True ) or type( options[ 2 ] ) != type( True ) or type( options[ 3 ] ) != type( 1 ) or type( options[ 3 ] ) != type( 1 ):

        write_log_file( s[ 'err-rd-cf' ] )

        reset_config_file()

        return [ SHOW_NOTIFICATIONS, SHOW_DEL_DIALOG, ALTERNATING_ROW_COLOR, MIN_SLEEP_TIME, MAX_SLEEP_TIME ]
    else:
        return options



def reset_config_file():
    options = [ SHOW_NOTIFICATIONS, SHOW_DEL_DIALOG, ALTERNATING_ROW_COLOR, MIN_SLEEP_TIME, MAX_SLEEP_TIME ]

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

    links      = []
    titles     = []
    currencies = []
    pictures   = []
    prices     = []

    for index in range( 0,  len( data ) ):
        try:
            info = loads( data[ index ] )
        except ValueError:
            continue
            #exit( 'Problem encoding the value' )                        #Translating

        links.append(      info[0]    )
        titles.append(     info[1]    )
        currencies.append( info[2]    )
        pictures.append(   info[3]    )
        prices.extend(     info[ 4: ] )

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
            data_file.write( dumps( [ links[ index] , titles[ index ].decode( 'ascii', 'ignore' ) , currencies[ index ] , pictures[ index ], prices[ index ] ] ) + '\n' )

    data_file.close()



def write_log_file( string, output=True ):
    if output:
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

    [ SHOW_NOTIFICATIONS, SHOW_DEL_DIALOG, ALTERNATING_ROW_COLOR, MIN_SLEEP_TIME, MAX_SLEEP_TIME ] = read_config_file()

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

