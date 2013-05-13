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
from itertools import izip
from os.path import exists, expanduser
from urllib import urlopen
from time import ctime, time, sleep
from json import dumps, loads
from dbus import SessionBus
from glib import GError
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


class Article():
    def __init__( self,
                  url = '',
                  name = 'No Name Found',
                  currency = '',
                  pic_url = '',
                  pic_name = '',
                  ):
        self.url = url
        self.name = name
        self.price_data = []
        self.currency = currency
        self.pic_url = pic_url
        self.pic_name = pic_name

        self.bad_conn = False
        self.bad_url = False

    def update( self ):
        try:
            self.name, self.currency, price, self.pic_url = get_info_for( self.url )

            if price != self.price:
                self.price_data.append( [ price, int( time() ) ] )

            self.pic_name = search( '\/[A-Z0-9]{10}\/', self.url ).group()[1: -1] + '.jpg'

        except IOError:
            self.bad_conn = True
        except ValueError:
            self.bad_url = True

    def __getattr__( self, name ):
        if name=='bad_conn':
            if self.bad_conn:
                self.bad_conn = False
                return True

            return False

        if name=='bad_url':
            if self.bad_url:
                self.bad_url = False
                return True

            return False

        if name=='price':
            try:
                return self.price_data[-1][0]
            except IndexError:
                return 0



class RefreshThread( Thread ):
    def __init__( self, articles, upd_list_store, set_ind, upd_art ):
        self.stop_flag = False
        self.articles = articles
        self.callbacks = ( upd_list_store,
                           set_ind,
                           upd_art
                           )
        Thread.__init__( self )


    def stop( self ):
        self.stop_flag = True


    def run( self ):
        global SLEEP_TIME, ALTERNATING_ROW_COLOR, SHOW_NOTIFICATIONS

        write_log_file( 'Refresh Thread ' + str( active_count() - 1 ) + ' started' )

        runs = 0

        while not self.stop_flag:
            start_time = time()

            no_of_articles = len( self.articles )

            if no_of_articles == 0:
                write_log_file( s[ 'dat-empty' ], True )

            runs = runs + 1

            #Updates the information

            write_log_file( s[ 'getng-dat' ] )

            for art in self.articles.values():
                if self.stop_flag:
                    write_log_file( s[ 'svng-data' ] )
                    write_data_file( self.articles )

                    write_log_file( 'Halted Refresh Thread ' + str( active_count() - 1 ) )

                    return

                old_price = art.price

                art.update()

                new_price = art.price

                if new_price != old_price:
                    open( IMAGE_PATH + art.pic_name, IMAGE_WRITE_MODE ).write( urlopen( art.pic_url ).read() )

                    if old_price == s[ 'N/A' ]: #Überdenken
                        title = s[ 'bec-avail' ] + NOCOLOR + ':'

                    elif new_price == s[ 'N/A' ]:
                        title = s[ 'bec-unava' ] + NOCOLOR + ':'

                    elif new_price < old_price:
                        title = s[ 'price-dwn' ] + '%.2f' % old_price + ' > ' + '%.2f' % new_price + ' )' + NOCOLOR + ':'

                    elif new_price > old_price:
                        title = s[ 'price-up' ] + '%.2f' % old_price + ' > ' + '%.2f' % new_price + ' )' + NOCOLOR + ':'

                    body = art.name

                    if SHOW_NOTIFICATIONS:
                        notify( title, body, IMAGE_PATH + art.pic_name )

                    print_notification( title, body, '' )

                    gobject.idle_add( self.callbacks[1] )

                    gobject.idle_add( self.callbacks[0] )

            #Saving data to file

            write_log_file( s[ 'svng-data' ] )

            write_data_file( self.articles )

            #End time

            end_time = time()

            #Calculating the length of operating

            diff_time = int( end_time - start_time )

            write_log_file( s[ 'it-took' ] + str( diff_time ) + s[ 'seconds' ] )

            #Calculating sleeptime

            SLEEP_TIME = min( max( 2 * diff_time, MIN_SLEEP_TIME ), MAX_SLEEP_TIME )

            #Sleeping for agreed amount

            write_log_file( s[ 'sleep-for' ] + str( int( round( SLEEP_TIME ) ) ) + s[ 'seconds' ] )

            if self.stop_flag:
                write_log_file( 'Refresh Thread ' + str( active_count() - 1 ) + ' was halted before sleeping' )
                return

            for i in xrange( 10 * SLEEP_TIME ):
                if not self.stop_flag:
                    sleep( 1/10. )
                else:
                    write_log_file( 'Refresh Thread ' + str( active_count() - 1 ) + ' was halted while sleeping' )
                    return

        write_log_file( 'Refresh-Thread ' + str( active_count() - 1 ) + ' was stopped' )


class MainWindow:
    def __init__( self ):
        #Setting up the toolbar
        self.toolbar = self.setup_toolbar()


        #Setting up the data holding dictionary
        self.articles = dict()


        #Setting up the dbus service
        self.dbus_service = DBusService( self )


        #Setting up the config window
        self.config_window = self.setup_config_window()


        #Setting up the indicator
        self.indicator = self.setup_indicator()


        #Setting up the Liststore
        self.data_store = gtk.ListStore( bool, str, str, str, str, str, str )
        self.sortable = gtk.TreeModelSort( self.data_store )


        #Setting the costum sort function on columns 2 - 5
        for i in [ 2, 3, 4, 5 ]:
            self.sortable.set_sort_func( i, my_sort_function, i )


        #Setting up the TreeView
        self.data_view = self.setup_treeview()


        #Fill the TreeView
        articles = read_data_file()

        for article in articles:
            self.articles[ article.url ] = article

        self.update_list_store()


        #Setting up text box for on_add_article
        self.add_textbox = gtk.Entry( 0 )


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
        inner_layer.pack_start( self.toolbar,                False, False, 5  )
        inner_layer.pack_start( gtk.Label( '' ),             True,  True,  0  )
        inner_layer.pack_start( self.add_textbox,           True,  True,  5  )

        self.preview_box = gtk.HBox()
        info_box = gtk.VBox()
        title_link = gtk.Label()
        title_link.set_markup( '<a href="https://www.github.com/mchlnix/amazonCheck-Daemon">amazonCheck</a>' )

        info_box.pack_start( gtk.Label( '' ),                                 True, True,   0 )
        info_box.pack_start( title_link ,                                     False, False, 5 )
        info_box.pack_start( gtk.Label( 'Check up on your favorite stuff!' ), False, False, 5 )
        info_box.pack_start( gtk.Label( 'By Me' ),                            False, False, 5 )
        info_box.pack_start( gtk.Label( '' ),                                 True, True,   0 )

        self.preview_box.pack_start( info_box,               False, False, 5  )
        self.preview_box.pack_start( self.image_preview,     False, False, 10 )
        inner_layer.pack_start( self.preview_box,            False, False, 5  )


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
        self.add_textbox.hide()

        #Set self.window as parent of config window
        self.config_window.set_transient_for( self.window )


        #Setting up refresh thread
        self.refresh_thread = RefreshThread( self.articles,
                                             self.update_list_store,
                                             self.set_indicator_attention,
                                             '',
                                             )


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


    def find_article( self, name ):
        for url,art in self.articles.items():
            if art.name == name:
                return art

        else:
            raise LookupError


    def on_add_article( self, widget ):
        if type( widget ) == gtk.Button:
            textbox = self.add_textbox
            pos_label = textbox.get_parent().get_children()[2]

            textbox.set_visible( not textbox.get_visible() )
            pos_label.set_visible( not pos_label.get_visible() )

            if textbox.get_visible():
                return

            url = shorten_amazon_link( textbox.get_text() )
            textbox.set_text( '' )

        elif type( widget ) == gtk.MenuItem:
            url = gtk.Clipboard().wait_for_text()
            if url:
                url = shorten_amazon_link( url )
            else:
                write_log_file( "Couldn't add article: Clipboard was empty.", True )

        if url in self.articles:
            write_log_file( 'Article already in the database', True )
            return

        if url.find( 'amazon.co.jp' ) != -1:
            write_log_file( 'Japanese Amazon articles cannot be parsed at the moment. Sorry.', True )
            return

        new_art = Article( url )

        new_art.update()

        if new_art.bad_conn:
            write_log_file( s[ 'err-con-s' ], True )
            return
        elif new_art.bad_url:
            write_log_file( 'Couldn\'t parse the url.', True )
            return

        self.refresh_thread.stop()

        download_image( url=new_art.pic_url, dest=IMAGE_PATH + new_art.pic_name )

        self.refresh_thread.join()

        self.articles[ new_art.url ] = new_art

        try:
            with open( DATA_FILE, 'a' ) as data_file:
                data_file.write( dumps( new_art.__dict__ ) )
                data_file.write( '\n' )
        except IOError:
            write_log_file( 'Couldn\'t write to data file.', True )

        self.update_list_store()

        self.start_thread()


    def on_cell_toggled( self, widget, path ):
        title = self.sortable[path][6]

        for row in self.data_store:
            if row[6] == title:
                row[0] = not row[0]


    def on_changed_max_sleep( self, widget ):
        min_spin_button = self.config_window.get_children()[0].get_children()[0].get_children()[0].get_children()[2]
        max_spin_button = self.config_window.get_children()[0].get_children()[0].get_children()[1].get_children()[2]

        if ( max_spin_button.get_value() < min_spin_button.get_value() ):
            min_spin_button.set_value( max_spin_button.get_value() )

        return True


    def on_changed_min_sleep( self, widget ):
        min_spin_button = self.config_window.get_children()[0].get_children()[0].get_children()[0].get_children()[2]
        max_spin_button = self.config_window.get_children()[0].get_children()[0].get_children()[1].get_children()[2]

        if ( min_spin_button.get_value() > max_spin_button.get_value() ):
            max_spin_button.set_value( min_spin_button.get_value() )

        return True


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


    def on_delete_articles( self, widget=None ):

        delete_queue = []
        tree_length = len( self.data_store )

        for index, row in enumerate( reversed( list( self.data_store ) ) ):
            if row[0] == True:
                delete_queue.append( ( index, row[6] ) )

        if len( delete_queue ) == 0:
            return False

        if SHOW_DEL_DIALOG:
            dialog = gtk.Dialog( "",
                                 None,
                                 gtk.DIALOG_MODAL
                               | gtk.DIALOG_DESTROY_WITH_PARENT,
                                 ( gtk.STOCK_CANCEL,
                                   gtk.RESPONSE_REJECT,
                                   gtk.STOCK_OK,
                                   gtk.RESPONSE_ACCEPT,
                                   ),
                                 )

            hbox = gtk.HBox()
            hbox.show()

            if len( delete_queue ) == 1:
                label = gtk.Label( 'Really delete the selected article?' )
            else:
                label = gtk.Label( 'Really delete the selected articles?' )

            label.show()

            hbox.pack_start( label,       True, True, 10 )
            dialog.vbox.pack_start( hbox, True, True, 10 )

            response = dialog.run()
            dialog.destroy()

            if response != -3:
                return False


        self.refresh_thread.stop()
        self.refresh_thread.join()

        for index, name in delete_queue:

            try:
                art = self.find_article( name )

                pic_name = art.pic_name
                del self.articles[ art.url ]

            except KeyError:
                write_log_file( 'KeyError happened' )
                print name
                continue
            except LookupError:
                write_log_file( 'Couldn\'t find article in database.', True )
                continue

            try:
                remove( IMAGE_PATH + pic_name )
            except OSError:
                write_log_file( 'Picture file was already deleted' )

            self.data_store.remove( self.data_store.get_iter( index ) )

        write_data_file( self.articles )

        self.update_list_store()

        if len( self.data_store ) == 0:
            self.image_preview.set_from_file( IMAGE_PATH + 'no-pic.png' )

            fields = self.preview_box.get_children()[0].get_children()

            fields[1].set_markup( '<a href="https://www.github.com/mchlnix/amazonCheck-Daemon">amazonCheck</a>' )
            fields[2].set_markup( 'Check up on your favorite stuff!' )
            fields[3].set_markup( 'By Me' )
        else:
            self.data_view.set_cursor( 0 )

        self.start_thread()


    def on_row_selected( self, treeview ):
        try:
            index = treeview.get_selection().get_selected_rows()[1][0][0]
            art_name = unicode( self.data_view.get_model()[ index ][-1] )

            art = self.find_article( name=art_name )

            avgs = get_avg_price( art.price_data )
            price = art.price
            currency = art.currency

            try:
                pixbuf = gtk.gdk.pixbuf_new_from_file( IMAGE_PATH + art.pic_name )
            except GError:
                write_log_file( 'Selected article doesn\'t have an image associated with it.', True )
                write_log_file( 'Trying to fix.', True )
                download_image( url=art.pic_url, dest=IMAGE_PATH + art.pic_name )
                pixbuf = gtk.gdk.pixbuf_new_from_file( IMAGE_PATH + art.pic_name )


            if pixbuf.get_width() < pixbuf.get_height():
                scaled_buf = pixbuf.scale_simple( dest_width=int( pixbuf.get_width() * 100 / pixbuf.get_height()), dest_height=100, interp_type=gtk.gdk.INTERP_BILINEAR )
            else:
                scaled_buf = pixbuf.scale_simple( dest_width=100, dest_height=int( pixbuf.get_height() * 100 / pixbuf.get_width()), interp_type=gtk.gdk.INTERP_BILINEAR )

            self.image_preview.set_from_pixbuf( scaled_buf )


            if len( art.name ) > 55:
                disp_title = art.name[0:51] + '...'
            else:
                disp_title = art.name

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

            limit = min( len( art.price_data ), 3 )

            for i in xrange( limit ):
                tmp_price = art.price_data[i - limit][0]

                if tmp_price == 'N/A':
                    last_3_prices += '<span color="#FF3D3D">' + 'N/A' + '</span>'
                else:
                    if tmp_price > avgs:
                        color = '<span foreground="#FF3D3D">'

                    elif tmp_price < avgs:
                        color = '<span foreground="#27B81F">'

                    elif tmp_price == avgs:
                        color = '<span foreground="#FCCA00">'

                    last_3_prices += color + '%.2f</span>' % tmp_price

                if i < limit - 1:
                    last_3_prices += ' > '

            fields = self.preview_box.get_children()[0].get_children()

            fields[1].set_markup( '<a href="' + art.url + '">' + disp_title.replace( '&', '&amp;' ) + '</a>' )
            fields[2].set_markup( 'Current price: ' + '<u>' + price + '</u> ' + currency )
            fields[3].set_markup( last_3_prices )

        except IndexError:
            pass


    def on_show_config_window( self, widget ):
        self.config_window.show_all()


    def on_visit_page( self, widget, path, column ):
        if column.get_title() == '':
            return

        art_name = unicode( self.data_view.get_model()[ path ][-1] )

        article = self.find_article( name=art_name )

        open_in_browser( article.url )


    def set_indicator_active( self, widget, direction=None ):
        reset_label = self.indicator.get_menu().get_children()[3]
        reset_label.set_sensitive( False )

        self.indicator.set_status( STATUS_ACTIVE )


    def set_indicator_attention( self ):
        reset_label = self.indicator.get_menu().get_children()[3]
        reset_label.set_sensitive( True )

        self.indicator.set_status( STATUS_ATTENTION )


    def setup_indicator( self ):
        indicator = Indicator( 'amazonCheck-indicator',
                               'amazonCheck_indicator',
                               CATEGORY_APPLICATION_STATUS,
                               '/usr/share/pixmaps/',
                               )

        indicator.set_attention_icon( 'amazonCheck_indicator_attention' )
        indicator.set_status( STATUS_ACTIVE )

        item_show      = gtk.MenuItem( 'Hide window' )
        item_add_clip  = gtk.MenuItem( 'Add from clipboard' )
        item_exit      = gtk.MenuItem( 'Exit'        )
        item_seperator = gtk.SeparatorMenuItem()
        item_reset     = gtk.MenuItem( 'Reset'       )

        item_show.connect(     'activate', self.toggle_window_visibility )
        item_add_clip.connect( 'activate', self.on_add_article           )
        item_exit.connect(     'activate', self.exit_application         )
        item_reset.connect(    'activate', self.set_indicator_active     )

        menu = gtk.Menu()

        menu.append( item_show          )
        menu.append( item_add_clip      )
        menu.append( item_exit          )
        menu.append( item_seperator     )
        menu.append( item_reset         )

        menu.show_all()

        indicator.set_menu( menu )

        return indicator


    def setup_toolbar( self ):
        toolbar = gtk.Toolbar()
        toolbar.set_orientation( gtk.ORIENTATION_VERTICAL )
        toolbar.set_style( gtk.TOOLBAR_ICONS )

        i = [ gtk.STOCK_ADD, gtk.STOCK_REMOVE, gtk.STOCK_PREFERENCES ]
        l = [ 'Add', 'Remove', 'Config' ]
        c = [ self.on_add_article,
              self.on_delete_articles,
              self.on_show_config_window,
              ]

        for icon, label, callback in izip( i, l, c ):
            image = gtk.Image();
            image.set_from_stock( icon, gtk.ICON_SIZE_LARGE_TOOLBAR )

            toolbar.append_item( None, label, None, image, callback )

        return toolbar


    def setup_config_window( self ):
        window = gtk.Window( gtk.WINDOW_TOPLEVEL )
        window.set_position( gtk.WIN_POS_CENTER  )
        window.set_resizable( False )
        window.set_modal(     True  )
        window.connect( 'delete-event', self.on_config_cancel )

        outer_layer = gtk.VBox()
        config_box  = gtk.VBox()
        button_box  = gtk.HBox()

        checkbutton_notifications = gtk.CheckButton()
        checkbutton_delete_dialog = gtk.CheckButton()
        checkbutton_alt_row_color = gtk.CheckButton()

        checkbutton_notifications.set_active( SHOW_NOTIFICATIONS    )
        checkbutton_delete_dialog.set_active( SHOW_DEL_DIALOG       )
        checkbutton_alt_row_color.set_active( ALTERNATING_ROW_COLOR )

        spin_min_sleep = gtk.SpinButton( adjustment=gtk.Adjustment( value=MIN_SLEEP_TIME,
                                                                    lower=30,
                                                                    upper=3600,
                                                                    step_incr=1,
                                                                    page_incr=5,
                                                                    page_size=0,
                                                                    ),
                                         climb_rate=0.0,
                                         digits=0,
                                         )

        spin_max_sleep = gtk.SpinButton( adjustment=gtk.Adjustment( value=MAX_SLEEP_TIME,
                                                                    lower=30,
                                                                    upper=3600,
                                                                    step_incr=1,
                                                                    page_incr=5,
                                                                    page_size=0,
                                                                    ),
                                         climb_rate=0.0,
                                         digits=0,
                                         )

        spin_min_sleep.connect( 'value-changed', self.on_changed_min_sleep )
        spin_max_sleep.connect( 'value-changed', self.on_changed_max_sleep )

        hbox_min_sleep = gtk.HBox()
        hbox_min_sleep.pack_start( gtk.Label( 'Min. Interval between updates: ' ), False, False, 5 )
        hbox_min_sleep.pack_start( gtk.Label( '' ),                                True,  True,  5 )
        hbox_min_sleep.pack_start( spin_min_sleep,                                 False, False, 5 )

        hbox_max_sleep = gtk.HBox()
        hbox_max_sleep.pack_start( gtk.Label( 'Max. Interval between updates: ' ), False, False, 5 )
        hbox_max_sleep.pack_start( gtk.Label( '' ),                                True,  True,  5 )
        hbox_max_sleep.pack_start( spin_max_sleep,                                 False, False, 5 )

        hbox_notifications = gtk.HBox()
        hbox_notifications.pack_start( gtk.Label( 'Show notification bubbles?' ), False, False, 5 )
        hbox_notifications.pack_start( gtk.Label( '' ),                           True,  True,  5 )
        hbox_notifications.pack_start( checkbutton_notifications,                 False, False, 5 )

        hbox_delete_dialog = gtk.HBox()
        hbox_delete_dialog.pack_start( gtk.Label( 'Confirm deleting articles?' ), False, False, 5 )
        hbox_delete_dialog.pack_start( gtk.Label( '' ),                           True,  True,  5 )
        hbox_delete_dialog.pack_start( checkbutton_delete_dialog,                 False, False, 5 )

        hbox_alt_row_color = gtk.HBox()
        hbox_alt_row_color.pack_start( gtk.Label( 'Alternate row colors?' ), False, False, 5 )
        hbox_alt_row_color.pack_start( gtk.Label( '' ),                      True,  True,  5 )
        hbox_alt_row_color.pack_start( checkbutton_alt_row_color,            False, False, 5 )

        config_box.pack_start( hbox_min_sleep,                              False, False, 5 )
        config_box.pack_start( hbox_max_sleep,                              False, False, 5 )
        config_box.pack_start( hbox_notifications,                          False, False, 5 )
        config_box.pack_start( hbox_delete_dialog,                          False, False, 5 )
        config_box.pack_start( hbox_alt_row_color,                          False, False, 5 )

        button_cancel = gtk.Button( 'Cancel'     )
        button_ok     = gtk.Button( '    OK    ' )

        button_cancel.connect( 'clicked', self.on_config_cancel    )
        button_ok.connect(     'clicked', self.on_config_confirm   )

        button_box.pack_start( gtk.Label( '' ), True,  True,  5 )
        button_box.pack_start( button_cancel,   False, False, 5 )
        button_box.pack_start( button_ok,       False, False, 5 )

        outer_layer.pack_start( config_box,      False, False, 5 )
        outer_layer.pack_start( gtk.Label( '' ), True,  True,  5 )
        outer_layer.pack_start( button_box,      False, False, 5 )

        window.add( outer_layer )

        return window


    def setup_treeview( self ):
        data_view = gtk.TreeView( self.sortable )
        data_view.set_headers_clickable( True )
        data_view.connect( 'row-activated',  self.on_visit_page   )
        data_view.connect( 'cursor-changed', self.on_row_selected )
        data_view.set_rules_hint( ALTERNATING_ROW_COLOR )

        toggle_rend = gtk.CellRendererToggle()
        toggle_rend.connect( 'toggled', self.on_cell_toggled )

        cur_rend   = gtk.CellRendererText()
        price_rend = gtk.CellRendererText()
        title_rend = gtk.CellRendererText()
        min_rend   = gtk.CellRendererText()
        avg_rend   = gtk.CellRendererText()
        max_rend   = gtk.CellRendererText()

        min_rend.set_property( 'foreground', '#27B81F' )
        avg_rend.set_property( 'foreground', '#FCCA00' )
        max_rend.set_property( 'foreground', '#FF3D3D' )

        toggle_col = gtk.TreeViewColumn( '',      toggle_rend,   active=0 )
        cur_col    = gtk.TreeViewColumn( 'CY',    cur_rend,      text=1   )
        price_col  = gtk.TreeViewColumn( 'Price', price_rend,    markup=2 )
        min_col    = gtk.TreeViewColumn( 'Min',   min_rend,      text=3   )
        avg_col    = gtk.TreeViewColumn( 'Avg',   avg_rend,      text=4   )
        max_col    = gtk.TreeViewColumn( 'Max',   max_rend,      text=5   )
        title_col  = gtk.TreeViewColumn( 'Title', title_rend,    text=6   )

        columns = [ toggle_col,
                    cur_col,
                    price_col,
                    min_col,
                    avg_col,
                    max_col,
                    title_col,
                    ]

        for index, column in enumerate( columns ):
            column.set_sort_column_id( index )

            data_view.append_column( column )

        return data_view


    def start_thread( self ):
        self.refresh_thread = RefreshThread( self.articles,
                                             self.update_list_store,
                                             self.set_indicator_attention,
                                             '',
                                             )
        self.refresh_thread.start()


    def toggle_window_visibility( self, widget=None, event=None ):
        menu_entry = self.indicator.get_menu().get_children()[0]

        if self.window.get_visible():
            self.window.set_visible( False )
            menu_entry.set_label( 'Show Window' )
        else:
            self.window.set_visible( True  )
            self.update_list_store()
            self.indicator.set_status( STATUS_ACTIVE )
            menu_entry.set_label( 'Hide Window' )

        return True


    def update_list_store( self ):
        write_log_file( 'Gui is updating' )

        self.data_store.clear()

        for art in self.articles.values():
            price = art.price

            if not len( art.price_data ) > 1:
                avgs = mins = maxs = art.price_data[0][0]
            else:
                avgs = get_avg_price( art.price_data )
                if avgs == -1: avgs = s[ 'N/A' ]

                mins = get_min_price( art.price_data )
                if mins == -1: mins = s[ 'N/A' ]

                maxs = get_max_price( art.price_data )
                if maxs == -1: maxs = s[ 'N/A' ]

            if maxs == mins:
                color = '<span>'

            elif price == mins:
                color = '<span foreground="#0000C7">'

            elif price > avgs:
                color = '<span foreground="#FF3D3D">'

            elif price < avgs:
                color = '<span foreground="#27B81F">'

            else: #price == avgs
                color = '<span foreground="#FCCA00">'

            if mins != s[ 'N/A' ]:  mins = '%.2f' % mins #1.00 not 1.0

            if maxs != s[ 'N/A' ]:  maxs = '%.2f' % maxs

            if avgs != s[ 'N/A' ]:  avgs = '%.2f' % avgs

            if price != s[ 'N/A' ]: price = '%.2f' % price

            try:
                for index in xrange( len( self.articles ) ):
                    if self.data_store[ index ][6] == art.name:
                        self.data_store[ index ][2] = color + str( price ) + '</span>'
                        self.data_store[ index ][3] = mins
                        self.data_store[ index ][4] = avgs
                        self.data_store[ index ][5] = maxs
                        break

            except IndexError:
                self.data_store.append( [ False,
                                          art.currency,
                                          color + str( price )+ '</span>',
                                          mins,
                                          avgs,
                                          maxs,
                                          art.name,
                                        ] )

        write_log_file( 'Gui updated' )


def download_image( url, dest, write_mode=IMAGE_WRITE_MODE ):
    pic_data = urlopen( url ).read()

    try:
        with open( dest, write_mode ) as f:
            f.write( pic_data )
    except IOError:
        write_log_file( 'Couldn\'t download picture.', True )



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
    try:
        with open( CONFIG_FILE, 'r' ) as config_file:
            options = loads( config_file.read() )
            write_log_file( s[ 'rd-cf-fil' ] + CONFIG_FILE )

    except IOError:
        write_log_file( s[ 'cnf-no-pm' ], True )
        write_log_file( s[ 'us-def-op' ], True )
        return [ SHOW_NOTIFICATIONS, SHOW_DEL_DIALOG, ALTERNATING_ROW_COLOR, MIN_SLEEP_TIME, MAX_SLEEP_TIME ]
    except ValueError:
        reset_config_file()
        return [ SHOW_NOTIFICATIONS, SHOW_DEL_DIALOG, ALTERNATING_ROW_COLOR, MIN_SLEEP_TIME, MAX_SLEEP_TIME ]


    return options



def reset_config_file():
    options = [ SHOW_NOTIFICATIONS, SHOW_DEL_DIALOG, ALTERNATING_ROW_COLOR, MIN_SLEEP_TIME, MAX_SLEEP_TIME ]

    write_config_file( options )

    write_log_file( s[ 'rd-cf-fil' ] + CONFIG_FILE )



def write_config_file( options ):                                       #Rewrite
    try:
        with open( CONFIG_FILE, 'w' ) as config_file:
            config_file.write( dumps( options ) )

            write_log_file( s[ 'wrt-cf-fl' ] + CONFIG_FILE )
    except IOError:
        write_log_file( s[ 'cnf-no-pm' ], True )
        return False



def read_data_file():
    write_log_file( s[ 'dat-fl-rd' ] )

    try:
        with open( DATA_FILE, 'r' ) as f:
            return_list = []

            for line in f.readlines():
                try:
                    new_art = Article()
                    new_art.__dict__ = loads( line )
                    return_list.append( new_art )
                except ValueError:
                    write_log_file( 'Problem reading data entry.', True )
                    continue
    except IOError:
        write_log_file( 'Couldn\'t read datafile.', True )
        return []

    return return_list


def write_data_file( articles ):
    try:
        with open( DATA_FILE, 'w' ) as data_file:
            for article in articles.values():
                data_file.write( dumps( article.__dict__ ) )
                data_file.write( '\n' )

    except IOError:
        write_log_file( s[ 'dat-no-pm' ], True )
        return False



def write_log_file( string, output=True ):
    if output:
        print( get_time() + ' ' + string + '\n' ),
    try:
        with open( LOG_FILE, 'a' ) as logfile:
            logfile.write( get_time() + ' ' + string + '\n' )
    except IOError:
        print( s[ 'log-no-pm' ] )
        return False

#-----------------------------------------------------------------------
#-----------------------------------------------------------------------


if __name__ == '__main__':
    write_log_file( s[ 'dashes' ] )
    write_log_file( s[ 'str-prgm' ] )

    [ SHOW_NOTIFICATIONS, SHOW_DEL_DIALOG, ALTERNATING_ROW_COLOR, MIN_SLEEP_TIME, MAX_SLEEP_TIME ] = read_config_file()

    write_log_file( s[ 'str-mn-lp' ] )

    mywindow = MainWindow()
    mywindow.main()

