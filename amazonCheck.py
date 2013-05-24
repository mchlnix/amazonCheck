#!/usr/bin/python2.7 -u
# -*- coding: utf-8 -*-

from sys import version_info, exit

if version_info >= (2, 8):
    exit( '--Please use Python 2.7 with this program--' )

from actrans import strings as s
from amazonlib import Article
from accolors import BOLD_WHITE, BLUE, GREEN, RED, YELLOW, NOCOLOR

import pygtk
pygtk.require( '2.0' )
import gtk
import gobject

from dbus.mainloop.glib import DBusGMainLoop
from appindicator import Indicator, STATUS_ACTIVE, STATUS_PASSIVE, \
                         STATUS_ATTENTION, CATEGORY_APPLICATION_STATUS
from dbus.service import Object as dbusServiceObject, BusName, \
                         method as dbusServiceMethod
from webbrowser import open as open_in_browser
from threading import Thread, active_count
from itertools import izip
from pynotify import init, Notification
from logging import  basicConfig, error, info, warning, DEBUG, INFO
from os.path import abspath, expanduser
from urllib import urlopen
from time import ctime, time, sleep, strftime
from json import dumps, loads
from dbus import SessionBus
from glib import GError
from sys import argv, exit
from re import search
from os import name, remove

IMAGE_WRITE_MODE = 'w'

IMAGE_PATH  = expanduser( path='~/.amazonCheck/pics/'               )
ICON_PATH   = expanduser( path='~/.amazonCheck/pics/icons/'         )
ICON_FILE   = expanduser( path='~/.amazonCheck/pics/icons/icon.png' )

CONFIG_FILE = expanduser( path='~/.amazonCheck/config' )
DATA_FILE   = expanduser( path='~/.amazonCheck/data'   )
LOG_FILE    = expanduser( path='~/.amazonCheck/log'    )

SHOW_NOTIFICATIONS    = True
SHOW_DEL_DIALOG       = True
ALTERNATING_ROW_COLOR = True

MIN_SLEEP_TIME = 180
MAX_SLEEP_TIME = 300

TV_AB_AVG = '#FF3D3D'
TV_BE_AVG = '#27B81F'
#TV_EX_AVG = '#FCCA00' #old color
TV_EX_AVG = '#FFA800'
TV_MIN    = '#0000C7'

SERVICE_NAME = 'org.amazonCheck.alive'


basicConfig( filename=LOG_FILE, level=0 )


DBusGMainLoop( set_as_default = True )


for service_name in SessionBus().list_names():
    if service_name == SERVICE_NAME:
        to_execute = SessionBus().get_object( SERVICE_NAME, '/alive' ).get_dbus_method( 'toggle_window', SERVICE_NAME )

        to_execute()

        exit( 'Program already running' )


gtk.gdk.threads_init() #No idea if those are necessary
gobject.threads_init() #Doesn't seem like it



class DBusService( dbusServiceObject ):
    def __init__( self, wind_obj ):
        self.wind_obj = wind_obj
        self.bus_name = BusName( SERVICE_NAME, bus=SessionBus() )
        dbusServiceObject.__init__( self, self.bus_name, '/alive' )


    @dbusServiceMethod( SERVICE_NAME )
    def toggle_window( self ):
        self.wind_obj.toggle_window_visibility()



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

        info( msg='Refresh Thread ' + str( active_count() - 1 ) + ' started' )

        runs = 0

        while not self.stop_flag:
            start_time = time()

            no_of_articles = len( self.articles )

            if no_of_articles == 0:
                warning( msg=s[ 'dat-empty' ] )

            runs = runs + 1

            #Updates the information

            info( msg=s[ 'getng-dat' ] )

            for art in self.articles.values():
                if self.stop_flag:
                    info( msg=s[ 'svng-data' ] )
                    write_data_file( content=self.articles )

                    info( msg='Halted Refresh Thread ' + str( active_count() - 1 ) )

                    return

                old_price = art.price

                try:
                    art.update()
                except:
                    error( msg='Couldn\'t update article %s.' % art.name )
                    continue

                if art.bad_conn:
                    warning( msg='Bad connection for %s' % art.name )
                elif art.bad_url:
                    warning( msg='Bad url for %s' % art.name )

                new_price = art.price

                if new_price != old_price:
                    open( name=IMAGE_PATH + art.pic_name,
                          mode=IMAGE_WRITE_MODE,
                          ).write( urlopen( url=art.pic_url ).read() )

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
                        osd_notify( title, body, IMAGE_PATH + art.pic_name )

                    print_notify( title, body, '' )

                    gobject.idle_add( self.callbacks[1] )

                    gobject.idle_add( self.callbacks[0] )

            #Saving data to file

            info( msg=s[ 'svng-data' ] )

            write_data_file( content=self.articles )

            #End time

            end_time = time()

            #Calculating the length of operating

            diff_time = int( end_time - start_time )

            info( msg=s[ 'it-took' ] + str( diff_time ) + s[ 'seconds' ] )

            #Calculating sleeptime

            sleeptime = min( max( 2*diff_time, MIN_SLEEP_TIME ), MAX_SLEEP_TIME )

            gobject.idle_add( self.callbacks[0] )

            #Sleeping for agreed amount

            info( msg=s[ 'sleep-for' ] + str( int( round( sleeptime ) ) ) + s[ 'seconds' ] )

            if self.stop_flag:
                info( msg='Refresh Thread ' + str( active_count() - 1 ) + ' was halted before sleeping' )
                return

            for i in xrange( 10*sleeptime ):
                if not self.stop_flag:
                    sleep( 1/10. )
                else:
                    info( msg='Refresh Thread ' + str( active_count() - 1 ) + ' was halted while sleeping' )
                    return

        info( msg='Refresh-Thread ' + str( active_count() - 1 ) + ' was stopped' )


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
        self.data_store = gtk.ListStore( bool, str, str, str, str, str, str, str )
        self.sortable = gtk.TreeModelSort( self.data_store )


        #Setting the costum sort function on columns 2 - 5
        for sort_column_id in [ 2, 3, 4, 5 ]:
            self.sortable.set_sort_func( sort_column_id,
                                         my_sort_function,
                                         sort_column_id, #user_data
                                         )


        #Fill the TreeStore
        articles = read_data_file()

        for article in articles:
            self.articles[ article.url ] = article


        #Setting up the TreeView
        self.data_view = self.setup_treeview()

        self.update_list_store()


        #Setting up text box for on_add_article
        self.add_textbox = gtk.Entry( max=0 )


        #Setting up the GUI boxes
        scroll = gtk.ScrolledWindow()
        scroll.set_size_request( width=640, height=480 )
        scroll.add( self.data_view )

        outer_layer = gtk.VBox()
        inner_layer = gtk.HBox()


        #Setting up the imagebox
        self.image_preview = gtk.Image()
        self.image_preview.set_from_file( ICON_FILE )


        #Setting up inner layer
        inner_layer.pack_start( gtk.Label( '' ),  False, False, 2  )
        inner_layer.pack_start( self.toolbar,     False, False, 5  )
        inner_layer.pack_start( gtk.Label( '' ),  True,  True,  0  )
        inner_layer.pack_start( self.add_textbox, True,  True,  5  )

        self.preview_box = gtk.HBox()
        info_box = gtk.VBox()

        title_link = gtk.Label()
        title_link.set_line_wrap( True )
        title_link.set_markup( '<a href="https://www.github.com/mchlnix/amazonCheck-Daemon">amazonCheck</a>' )

        info_box.pack_start( gtk.Label( '' ),                                 True, True,   0 )
        info_box.pack_start( title_link ,                                     False, False, 5 )
        info_box.pack_start( gtk.Label( 'Check up on your favorite stuff!' ), False, False, 5 )
        info_box.pack_start( gtk.Label( 'By Me' ),                            False, False, 5 )
        info_box.pack_start( gtk.Label( '' ),                                 True, True,   0 )

        self.preview_box.pack_start( info_box,           True, True,   5  )
        self.preview_box.pack_start( self.image_preview, False, False, 10 )
        inner_layer.pack_start( self.preview_box,        False, False, 5  )


        #Setting up outer layer
        scroll_hbox = gtk.HBox()
        scroll_hbox.pack_start( gtk.Label( '' ), False, False, 5  )
        scroll_hbox.pack_start( scroll,          True,  True,  0  )
        scroll_hbox.pack_start( gtk.Label( '' ), False, False, 5  )


        outer_layer.pack_start( scroll_hbox, True,  True,  0  )
        outer_layer.pack_start( inner_layer, False, False, 10 )


        #Setting up the main window
        self.window = gtk.Window( gtk.WINDOW_TOPLEVEL )
        self.window.set_position( gtk.WIN_POS_CENTER  )
        self.window.connect( 'delete-event',
                              self.toggle_window_visibility,
                              )
        self.window.connect( 'focus-in-event',
                              self.set_ind_active,
                              )

        self.window.set_icon_from_file( ICON_FILE )
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
                                             self.set_ind_attention,
                                             '',
                                             )

        self.link_col.set_visible( False )


    def main( self ):
        #Starting the data thread
        self.start_thread()

        try:
            gtk.main()

        except KeyboardInterrupt:
            error( msg='Gui crashed' )
            self.refresh_thread.stop()
            self.refresh_thread.join()


    def exit_application( self, widget ):
        self.window.set_visible( False )
        self.indicator.set_status( STATUS_PASSIVE )
        self.refresh_thread.stop()
        gtk.main_quit()


    def on_add_article( self, widget ):
        if type( widget ) == gtk.Button:
            textbox = self.add_textbox
            pos_label = textbox.get_parent().get_children()[2]

            textbox.set_visible( not textbox.get_visible() )
            pos_label.set_visible( not pos_label.get_visible() )

            if textbox.get_visible():
                return

            url = textbox.get_text()
            textbox.set_text( '' )

        elif type( widget ) == gtk.MenuItem:
            url = gtk.Clipboard().wait_for_text()
            if url is None:
                warning( msg="Couldn't add article: Clipboard was empty." )

        if url in self.articles:
            warning( msg='Article already in the database' )
            return

        if url.find( 'amazon.co.jp' ) != -1:
            print( 'Japanese Amazon articles cannot be parsed at the moment. Sorry.' )
            warning( msg='Japanese Amazon articles cannot be parsed at the moment. Sorry.' )
            return

        art = Article( url )

        art.update()

        if art.bad_conn:
            error( msg=s[ 'err-con-s' ] )
            return
        elif art.bad_url:
            error( msg='Couldn\'t parse the url.' )
            return

        self.refresh_thread.stop()

        download_image( url=art.pic_url, dest=IMAGE_PATH + art.pic_name )

        self.refresh_thread.join()

        self.articles[ art.url ] = art

        try:
            with open( DATA_FILE, 'a' ) as data_file:
                data_file.write( dumps( art.__dict__ ) )
                data_file.write( '\n' )
        except IOError:
            error( msg='Couldn\'t write to data file.' )

        self.data_store.append( [ False,
                                  art.currency,
                                  art.price,
                                  art.min,
                                  art.avg,
                                  art.max,
                                  art.name,
                                  art.url,
                                  ] )

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
        for row in self.data_store:
            if row[0]:
                break
        else:
            return

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

            label = gtk.Label( 'Really delete the selected articles?' )

            label.show()

            hbox.pack_start( label,       True, True, 10 )
            dialog.vbox.pack_start( hbox, True, True, 10 )

            response = dialog.run()
            dialog.destroy()

            if response != -3:
                return


        self.refresh_thread.stop()
        self.refresh_thread.join()
        for index, row in reversed( list( enumerate( self.data_store ) ) ):
            if row[0]:
                try:
                    remove( IMAGE_PATH + self.articles[ row[-1] ].pic_name )
                except OSError:
                    error( msg='Picture file was already deleted' )

                del self.articles[ row[-1] ]

                self.data_store.remove( self.data_store.get_iter( index ) )

        write_data_file( content=self.articles )

        self.update_list_store()

        if len( self.data_store ) == 0:
            self.image_preview.set_from_file( ICON_FILE )

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
        except IndexError:
            return False
        url = self.data_view.get_model()[ index ][7]

        art = self.articles[ url ]

        avgs = art.avg
        price = art.price
        currency = art.currency

        try:
            pixbuf = gtk.gdk.pixbuf_new_from_file( IMAGE_PATH + art.pic_name )
        except GError:
            error( msg='Selected article doesn\'t have an image associated with it: %s' % art.name )
            info( msg='Trying to reload image.' )
            download_image( url=art.pic_url,
                            dest=IMAGE_PATH + art.pic_name,
                            )
            pixbuf = gtk.gdk.pixbuf_new_from_file( IMAGE_PATH + art.pic_name )


        if pixbuf.get_width() < pixbuf.get_height():
            width  = int( pixbuf.get_width()*100 / pixbuf.get_height() )
            height = 100
        else:
            width  = 100
            height = int( pixbuf.get_height()*100 / pixbuf.get_width() )

        interpolation = gtk.gdk.INTERP_BILINEAR

        scaled_buf = pixbuf.scale_simple( dest_width=width,
                                          dest_height=height,
                                          interp_type=interpolation )

        self.image_preview.set_from_pixbuf( scaled_buf )

        if price > avgs:
            color = '<span foreground="' + TV_AB_AVG + '">'

        elif price < avgs:
            color = '<span foreground="' + TV_BE_AVG + '">'

        elif price == avgs:
            color = '<span foreground="' + TV_EX_AVG + '">'

        if price != 'N/A':
            price = color + '%.2f</span>' % price
        else:
            currency = ''

        last_3_prices = '    '

        limit = min( len( art.price_data ), 3 )

        for i in xrange( limit ):
            tmp_price = art.price_data[i - limit][0]

            if tmp_price == 'N/A':
                last_3_prices += '<span color="%s">N/A</span>' % TV_AB_AVG
            else:
                if tmp_price > avgs:
                    color = '<span foreground="%s">' % TV_AB_AVG

                elif tmp_price < avgs:
                    color = '<span foreground="%s">' % TV_BE_AVG

                elif tmp_price == avgs:
                    color = '<span foreground="%s">' % TV_EX_AVG

                last_3_prices += color + '%.2f</span>' % tmp_price

            if i < limit - 1:
                last_3_prices += ' > '

        fields = self.preview_box.get_children()[0].get_children()

        fields[1].set_markup( art.category.replace( '&', '&amp;' ) + ': <a href="' + art.url + '">' + art.name.replace( '&', '&amp;' ) + '</a>' )
        fields[2].set_markup( 'Current price: ' + '<u>' + price + '</u> ' + currency )
        fields[3].set_markup( last_3_prices )


    def on_show_config_window( self, widget ):
        self.config_window.show_all()


    def on_visit_page( self, widget, path, column ):
        if column.get_title() == '':
            return

        url = self.data_view.get_model()[ path ][-1]

        open_in_browser( url )


    def set_ind_active( self, widget, direction=None ):
        reset_label = self.indicator.get_menu().get_children()[3]
        reset_label.set_sensitive( False )

        self.indicator.set_status( STATUS_ACTIVE )


    def set_ind_attention( self ):
        reset_label = self.indicator.get_menu().get_children()[3]
        reset_label.set_sensitive( True )

        self.indicator.set_status( STATUS_ATTENTION )


    def setup_indicator( self ):
        indicator = Indicator( id='amazonCheck-indicator',
                               icon_name='ind_act',
                               category=CATEGORY_APPLICATION_STATUS,
                               icon_theme_path=ICON_PATH,
                               )

        indicator.set_attention_icon( 'ind_att' )
        indicator.set_status( STATUS_ACTIVE )

        item_show      = gtk.MenuItem( 'Hide window'        )
        item_add_clip  = gtk.MenuItem( 'Add from clipboard' )
        item_seperator = gtk.SeparatorMenuItem()
        item_reset     = gtk.MenuItem( 'Reset'              )
        item_exit      = gtk.MenuItem( 'Exit'               )

        item_show.connect(     'activate', self.toggle_window_visibility )
        item_add_clip.connect( 'activate', self.on_add_article           )
        item_exit.connect(     'activate', self.exit_application         )
        item_reset.connect(    'activate', self.set_ind_active           )

        menu = gtk.Menu()

        menu.append( item_show      )
        menu.append( item_add_clip  )
        menu.append( item_seperator )
        menu.append( item_reset     )
        menu.append( item_exit      )

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
            image.set_from_stock( stock_id=icon,
                                  size=gtk.ICON_SIZE_LARGE_TOOLBAR )

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

        config_box.pack_start( hbox_min_sleep,     False, False, 5 )
        config_box.pack_start( hbox_max_sleep,     False, False, 5 )
        config_box.pack_start( hbox_notifications, False, False, 5 )
        config_box.pack_start( hbox_delete_dialog, False, False, 5 )
        config_box.pack_start( hbox_alt_row_color, False, False, 5 )

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
        links_rend = gtk.CellRendererText()
        min_rend   = gtk.CellRendererText()
        avg_rend   = gtk.CellRendererText()
        max_rend   = gtk.CellRendererText()

        min_rend.set_property( 'foreground', TV_BE_AVG )
        avg_rend.set_property( 'foreground', TV_EX_AVG )
        max_rend.set_property( 'foreground', TV_AB_AVG )

        toggle_col = gtk.TreeViewColumn( '',      toggle_rend, active=0 )
        cur_col    = gtk.TreeViewColumn( 'CY',    cur_rend,    text=1   )
        price_col  = gtk.TreeViewColumn( 'Price', price_rend,  markup=2 )
        min_col    = gtk.TreeViewColumn( 'Min',   min_rend,    text=3   )
        avg_col    = gtk.TreeViewColumn( 'Avg',   avg_rend,    text=4   )
        max_col    = gtk.TreeViewColumn( 'Max',   max_rend,    text=5   )
        title_col  = gtk.TreeViewColumn( 'Title', title_rend,  text=6   )
        link_col   = gtk.TreeViewColumn( 'Links', links_rend,  text=7   )

        self.link_col = link_col

        columns = [ toggle_col,
                    cur_col,
                    price_col,
                    min_col,
                    avg_col,
                    max_col,
                    title_col,
                    link_col,
                    ]

        for index, column in enumerate( columns ):
            column.set_sort_column_id( index )

            data_view.append_column( column )

        for art in self.articles.values():
            self.data_store.append( [ False,
                                      art.currency,
                                      art.price,
                                      art.min,
                                      art.avg,
                                      art.max,
                                      art.name,
                                      art.url,
                                      ] )

        return data_view


    def start_thread( self ):
        self.refresh_thread = RefreshThread( self.articles,
                                             self.update_list_store,
                                             self.set_ind_attention,
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
        info( msg='Updating Gui' )

        for row in self.data_store:
            art = self.articles[ row[7] ] #Hidden links row

            price = mins = avgs = maxs = 'N/A'

            if art.max == art.min:
                color = '<span>'

            elif art.price == art.min:
                color = '<span foreground="' + TV_MIN + '">'

            elif art.price > art.avg:
                color = '<span foreground="' + TV_AB_AVG + '">'

            elif art.price < art.avg:
                color = '<span foreground="' + TV_BE_AVG + '">'

            else:                                         #price == avgs
                color = '<span foreground="' + TV_EX_AVG + '">'

            if art.min != -1:
                mins = '%.2f' % art.min       #1.00 not 1.0

            if art.max != -1:
                maxs = '%.2f' % art.max       #1.00 not 1.0

            if art.avg != -1:
                avgs = '%.2f' % art.avg       #1.00 not 1.0

            if art.price != 'N/A':
                price = '%.2f' % art.price    #1.00 not 1.0

            art_list = [ row[0],
                         art.currency,
                         color + str( price ) + '</span>',
                         mins,
                         avgs,
                         maxs,
                         art.name,
                         art.url
                         ]


            for index, content in enumerate( art_list ):
                row[ index ] = content

        info( msg='Updated Gui' )


def download_image( url, dest, write_mode=IMAGE_WRITE_MODE ):
    pic_data = urlopen( url ).read()

    try:
        with open( name=dest, mode=write_mode ) as f:
            f.write( pic_data )
    except IOError:
        error( msg='Couldn\'t download picture.' )



def my_sort_function( treemodel, iter1, iter2, index ):
    try:
        f1 = treemodel[iter1][index]
        f2 = treemodel[iter2][index]

        try:
            if f1.find( 'N/A' ) != -1:
                return 1
            elif f2.find( 'N/A' ) != -1:
                return -1
        except:
            return -1

        f1 = float( f1[ f1.find( '>' ) + 1 : f1.find( '<', 1 ) ] )
        f2 = float( f2[ f2.find( '>' ) + 1 : f2.find( '<', 1 ) ] )

        if f1 > f2:
            return -1
        elif f1 < f2:
            return 1
        else:
            return 0

    except ValueError:
        return 0



def read_config_file():
    try:
        with open( CONFIG_FILE, 'r' ) as config_file:
            options = loads( config_file.read() )
            info( msg=s[ 'rd-cf-fil' ] + CONFIG_FILE )

    except IOError:
        error( msg=s[ 'cnf-no-pm' ] )
        error( msg=s[ 'us-def-op' ] )
        try:
            reset_config_file()
        except:
            pass

        return [ SHOW_NOTIFICATIONS,
                 SHOW_DEL_DIALOG,
                 ALTERNATING_ROW_COLOR,
                 MIN_SLEEP_TIME,
                 MAX_SLEEP_TIME,
                 ]
    except ValueError:
        reset_config_file()
        return [ SHOW_NOTIFICATIONS,
                 SHOW_DEL_DIALOG,
                 ALTERNATING_ROW_COLOR,
                 MIN_SLEEP_TIME,
                 MAX_SLEEP_TIME,
                 ]

    return options



def reset_config_file():
    options = [ SHOW_NOTIFICATIONS,
                SHOW_DEL_DIALOG,
                ALTERNATING_ROW_COLOR,
                MIN_SLEEP_TIME,
                MAX_SLEEP_TIME,
                ]

    write_config_file( options )

    info( msg=s[ 'rd-cf-fil' ] + CONFIG_FILE )



def write_config_file( options ):                                       #Rewrite
    try:
        with open( name=CONFIG_FILE, mode='w' ) as config_file:
            config_file.write( dumps( options ) )

            info( msg=s[ 'wrt-cf-fl' ] + CONFIG_FILE )
    except IOError:
        error( msg=s[ 'cnf-no-pm' ] )
        return False



def read_data_file():
    info( msg=s[ 'dat-fl-rd' ] )

    try:
        with open( name=DATA_FILE, mode='r' ) as f:
            return_list = []

            for line in f.readlines():
                try:
                    new_art = Article()
                    new_art.__dict__ = loads( line )
                    return_list.append( new_art )
                except ValueError:
                    error( msg='Problem reading data entry.' )
                    continue
    except IOError:
        error( msg='Couldn\'t read datafile.' )
        return []

    return return_list


def write_data_file( content ):
    try:
        with open( name=DATA_FILE, mode='w' ) as data_file:
            for article in content.values():
                data_file.write( dumps( article.__dict__ ) )
                data_file.write( '\n' )

    except IOError:
        error( msg=s[ 'dat-no-pm' ] )
        return False



def get_time():
    return strftime( s[ 'date-frmt' ] )



def print_notify( title, body, picture='' ):
    print( get_time() + ' ' + title + ' ' + body )



def osd_notify( title, body, picture ):
    init("amazonCheck update")

    for color in [ RED, GREEN, NOCOLOR ]:
        title = title.replace( color, '' )
        body = body.replace( color, '' )

    Notification ( title, body, abspath( picture ) ).show()



#-----------------------------------------------------------------------
#-----------------------------------------------------------------------


if __name__ == '__main__':
    info( msg=s[ 'dashes' ] )
    info( msg=s[ 'str-prgm' ] )

    [ SHOW_NOTIFICATIONS,
    SHOW_DEL_DIALOG,
    ALTERNATING_ROW_COLOR,
    MIN_SLEEP_TIME,
    MAX_SLEEP_TIME,
    ] = read_config_file()

    info( msg=s[ 'str-mn-lp' ] )

    mywindow = MainWindow()
    mywindow.main()
