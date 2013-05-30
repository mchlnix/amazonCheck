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
from threading import Thread
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

MIN_SLEEPTIME = 180
MAX_SLEEPTIME = 300

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
        obj = SessionBus().get_object( SERVICE_NAME, '/alive' )
        to_exec = obj.get_dbus_method( 'toggle_window', SERVICE_NAME )

        to_exec()

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
        self.wind_obj.toggle_window_visible()



class RefreshThread( Thread ):
    def __init__( self, articles, upd_list_store, set_ind, upd_art ):
        self.stop_flag = False
        self.articles = articles
        self.callbacks = ( upd_list_store, set_ind, upd_art )
        Thread.__init__( self )


    def stop( self ):
        self.stop_flag = True


    def run( self ):

        info( 'Refresh Thread started' )

        while not self.stop_flag:
            start_time = time()

            no_of_articles = len( self.articles )

            if no_of_articles == 0:
                warning( s[ 'dat-empty' ] )

            #Updates the information

            info( s[ 'getng-dat' ] )

            for art in self.articles.values():
                if self.stop_flag:
                    info( s[ 'svng-data' ] )
                    write_data_file( content=self.articles )

                    info( 'Halted Refresh Thread' )

                    return

                old_price = art.price

                try:
                    art.update()
                except:
                    error( 'Couldn\'t update article %s.' % art.name )
                    continue

                if art.bad_conn:
                    warning( 'Bad connection for %s' % art.name )
                elif art.bad_url:
                    warning( 'Bad url for %s' % art.name )

                new_price = art.price

                if new_price != old_price:
                    open( name=IMAGE_PATH + art.pic_name,
                          mode=IMAGE_WRITE_MODE,
                          ).write( urlopen( url=art.pic_url ).read() )

                    if old_price == s[ 'N/A' ]:
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

            info( s[ 'svng-data' ] )

            write_data_file( content=self.articles )

            #End time

            end_time = time()

            #Calculating the length of operating

            diff_time = int( end_time - start_time )

            info( s[ 'it-took' ] + str( diff_time ) + s[ 'seconds' ] )

            #Calculating sleeptime

            sleeptime = min( max( 2*diff_time, MIN_SLEEPTIME ), MAX_SLEEPTIME )

            gobject.idle_add( self.callbacks[0] )

            #Sleeping for agreed amount

            info( s[ 'sleep-for' ] + str( int( sleeptime ) ) + s[ 'seconds' ] )

            if self.stop_flag:
                info( 'Refresh Thread was halted before sleeping' )
                return

            for i in xrange( 10*sleeptime ):
                if not self.stop_flag:
                    sleep( 1/10. )
                else:
                    info( 'Refresh Thread was halted while sleeping' )
                    return

        info( 'Refresh-Thread was stopped' )


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
                                         sort_function,
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
                              self.toggle_window_visible,
                              )
        self.window.connect( 'focus-in-event',
                              self.set_ind_active,
                              )

        self.window.set_icon_from_file( ICON_FILE )
        self.window.set_title(
          'amazonCheck - Monitor your favorite books, movies, games...',
                             )

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
            error( 'Gui crashed' )
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
                warning(
                      'Couldn\'t add article: Clipboard was empty.',
                       )

        art = Article( url )

        if art.url in self.articles:
            warning( 'Article already in the database' )
            return

        art.update()

        if art.bad_conn:
            error( s[ 'err-con-s' ] )
            return
        elif art.bad_url:
            error( 'Couldn\'t parse the url.' )
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
            error( 'Couldn\'t write to data file.' )

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
        global SHOW_NOTIFICATIONS, SHOW_DEL_DIALOG, MIN_SLEEPTIME, MAX_SLEEPTIME

        checkboxes = self.config_window.get_children()[0].get_children()[0].get_children()
        min_spin_button = self.config_window.get_children()[0].get_children()[0].get_children()[0].get_children()[2]
        max_spin_button = self.config_window.get_children()[0].get_children()[0].get_children()[1].get_children()[2]

        SHOW_NOTIFICATIONS       = checkboxes[2].get_children()[2].get_active()
        SHOW_DEL_DIALOG          = checkboxes[3].get_children()[2].get_active()
        ALTERNATING_ROW_COLOR    = checkboxes[4].get_children()[2].get_active()
        MIN_SLEEPTIME           = min_spin_button.get_value_as_int()
        MAX_SLEEPTIME           = max_spin_button.get_value_as_int()

        self.data_view.set_rules_hint( ALTERNATING_ROW_COLOR )

        write_config_file( [ SHOW_NOTIFICATIONS, SHOW_DEL_DIALOG,
                             ALTERNATING_ROW_COLOR, MIN_SLEEPTIME,
                             MAX_SLEEPTIME ] )

        self.config_window.hide()


    def on_config_cancel( self, widget, event=None ):

        self.config_window.hide()

        checkboxes = self.config_window.get_children()[0].get_children()[0].get_children()
        min_spin_button = self.config_window.get_children()[0].get_children()[0].get_children()[0].get_children()[2]
        max_spin_button = self.config_window.get_children()[0].get_children()[0].get_children()[1].get_children()[2]

        checkboxes[2].get_children()[2].set_active( SHOW_NOTIFICATIONS    )
        checkboxes[3].get_children()[2].set_active( SHOW_DEL_DIALOG       )
        checkboxes[4].get_children()[2].set_active( ALTERNATING_ROW_COLOR )

        min_spin_button.set_value( MIN_SLEEPTIME )
        max_spin_button.set_value( MAX_SLEEPTIME )

        return True


    def on_delete_articles( self, widget=None ):
        for row in self.data_store:
            if row[0]:
                break
        else:
            return

        if SHOW_DEL_DIALOG:
            dialog = gtk.Dialog( '',
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
                    error( 'Picture file was already deleted' )

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

        pic_path = IMAGE_PATH + art.pic_name

        try:
            pixbuf = gtk.gdk.pixbuf_new_from_file( pic_path )
        except GError:
            error( 'Selected article doesn\'t have an image associated with it: %s' % art.name )
            info( 'Trying to reload image.' )
            download_image( url=art.pic_url, dest=pic_path )
            pixbuf = gtk.gdk.pixbuf_new_from_file( pic_path )

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

        cur_price = get_color( art )

        last_3_prices = '  >  '.join(
        [ get_color( art, price=price ) for price, time in art.price_data[-3:] ]
                                    )

        fields = self.preview_box.get_children()[0].get_children()

        cur_price = 'Current price: %s' % ( cur_price )
        cat_title = '%s: <a href="%s">%s</a>' % ( art.category, art.url,
                                                  art.name )

        fields[1].set_markup( cat_title.replace( '&', '&amp;' ) )
        fields[2].set_markup( cur_price )
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

        item_show.connect(     'activate', self.toggle_window_visible )
        item_add_clip.connect( 'activate', self.on_add_article        )
        item_exit.connect(     'activate', self.exit_application      )
        item_reset.connect(    'activate', self.set_ind_active        )

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

        spin_min_sleep = gtk.SpinButton( adjustment=gtk.Adjustment( value=MIN_SLEEPTIME,
                                                                    lower=30,
                                                                    upper=3600,
                                                                    step_incr=1,
                                                                    page_incr=5,
                                                                    page_size=0,
                                                                    ),
                                         climb_rate=0.0,
                                         digits=0,
                                         )

        spin_max_sleep = gtk.SpinButton( adjustment=gtk.Adjustment( value=MAX_SLEEPTIME,
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

        toggle_rnd = gtk.CellRendererToggle()
        cur_rnd    = gtk.CellRendererText()
        price_rnd  = gtk.CellRendererText()
        title_rnd  = gtk.CellRendererText()
        links_rnd  = gtk.CellRendererText()
        min_rnd    = gtk.CellRendererText()
        avg_rnd    = gtk.CellRendererText()
        max_rnd    = gtk.CellRendererText()

        toggle_rnd.connect( 'toggled', self.on_cell_toggled )

        cur_rnd.set_alignment( 0.5, 0.5 )

        price_rnd.set_alignment( 0, 0.5 )

        min_rnd.set_property( 'foreground', TV_BE_AVG )
        min_rnd.set_alignment( 1, 0.5 )

        avg_rnd.set_property( 'foreground', TV_EX_AVG )
        avg_rnd.set_alignment( 1, 0.5 )

        max_rnd.set_property( 'foreground', TV_AB_AVG )
        max_rnd.set_alignment( 1, 0.5 )

        toggle_col = gtk.TreeViewColumn( '',      toggle_rnd, active=0 )
        cur_col    = gtk.TreeViewColumn( '',      cur_rnd,    text=1   )
        price_col  = gtk.TreeViewColumn( 'Price', price_rnd,  markup=2 )
        min_col    = gtk.TreeViewColumn( 'Min',   min_rnd,    text=3   )
        avg_col    = gtk.TreeViewColumn( 'Avg',   avg_rnd,    text=4   )
        max_col    = gtk.TreeViewColumn( 'Max',   max_rnd,    text=5   )
        title_col  = gtk.TreeViewColumn( 'Title', title_rnd,  text=6   )
        link_col   = gtk.TreeViewColumn( 'Links', links_rnd,  text=7   )

        self.link_col = link_col

        columns = [ toggle_col, cur_col, price_col, min_col, avg_col,
                    max_col, title_col, link_col ]

        for index, column in enumerate( columns ):
            column.set_sort_column_id( index )
            column.set_sizing( gtk.TREE_VIEW_COLUMN_AUTOSIZE )

            data_view.append_column( column )

        for art in self.articles.values():
            self.data_store.append( [ False, art.currency, art.price,
                                      art.min, art.avg, art.max,
                                      art.name, art.url ] )

        return data_view


    def start_thread( self ):
        self.refresh_thread = RefreshThread( self.articles,
                                             self.update_list_store,
                                             self.set_ind_attention,
                                             '',
                                             )
        self.refresh_thread.start()


    def toggle_window_visible( self, widget=None, event=None ):
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
        info( 'Updating Gui' )

        for row in self.data_store:
            art = self.articles[ row[7] ] #Hidden links row

            if is_japanese( art ):
                f_str = '%d'
            else:
                f_str = '%.2f' #1.00 not 1.0

            mins = avgs = maxs = 'N/A'

            if min( art.min, art.avg, art.max ) != -1:
                mins = f_str % art.min
                avgs = f_str % art.avg
                maxs = f_str % art.max

            price = get_color( art )

            art_list = [ row[0], art.currency, price, mins, avgs, maxs,
                         art.name, art.url ]

            for index, content in enumerate( art_list ):
                row[ index ] = content

        info( 'Updated Gui' )



def read_config_file():
    try:
        with open( CONFIG_FILE, 'r' ) as config_file:
            options = loads( config_file.read() )
            info( s[ 'rd-cf-fil' ] + CONFIG_FILE )

    except IOError:
        error( s[ 'cnf-no-pm' ] )
        error( s[ 'us-def-op' ] )
        try:
            reset_config_file()
        except:
            pass

        return [ SHOW_NOTIFICATIONS, SHOW_DEL_DIALOG,
                 ALTERNATING_ROW_COLOR, MIN_SLEEPTIME, MAX_SLEEPTIME ]

    except ValueError:
        reset_config_file()
        return [ SHOW_NOTIFICATIONS, SHOW_DEL_DIALOG,
                 ALTERNATING_ROW_COLOR, MIN_SLEEPTIME, MAX_SLEEPTIME ]

    return options



def reset_config_file():
    options = [ SHOW_NOTIFICATIONS, SHOW_DEL_DIALOG,
                ALTERNATING_ROW_COLOR, MIN_SLEEPTIME, MAX_SLEEPTIME ]

    write_config_file( options )

    info( s[ 'rd-cf-fil' ] + CONFIG_FILE )



def write_config_file( options ):                               #Rewrite
    try:
        with open( name=CONFIG_FILE, mode='w' ) as config_file:
            config_file.write( dumps( options ) )

            info( s[ 'wrt-cf-fl' ] + CONFIG_FILE )
    except IOError:
        error( s[ 'cnf-no-pm' ] )
        return False



def read_data_file():
    info( s[ 'dat-fl-rd' ] )

    try:
        with open( name=DATA_FILE, mode='r' ) as f:
            return_list = []

            for line in f.readlines():
                try:
                    new_art = Article()
                    new_art.__dict__ = loads( line )
                    return_list.append( new_art )
                except ValueError:
                    error( 'Problem reading data entry.' )
                    continue
    except IOError:
        error( 'Couldn\'t read datafile.' )
        return []

    return return_list



def write_data_file( content ):
    try:
        with open( name=DATA_FILE, mode='w' ) as data_file:
            for article in content.values():
                data_file.write( dumps( article.__dict__ ) )
                data_file.write( '\n' )

    except IOError:
        error( s[ 'dat-no-pm' ] )
        return False



def download_image( url, dest, write_mode=IMAGE_WRITE_MODE ):
    pic_data = urlopen( url ).read()

    try:
        with open( name=dest, mode=write_mode ) as f:
            f.write( pic_data )
    except IOError:
        error( 'Couldn\'t download picture.' )



def get_color( article, price=None ):
    if price is None:
        price = article.price

    if price == 'N/A':
        return '<span>%s</span>' % price

    if is_japanese( article ):
        str_price = '%d' % price
    else:
        str_price = '%.2f' % price

    str_price = article.cur_str % str_price

    if article.min == article.max:
        return '<span>%s</span>' % str_price

    markup = '<span foreground="%s">'

    if price == article.min:
        color = TV_MIN
    elif price < article.avg:
        color = TV_BE_AVG
    elif price > article.avg:
        color = TV_AB_AVG
    else:
        color = TV_EX_AVG

    markup = markup % color + '%s</span>' % str_price

    return markup



def get_time():
    return strftime( s[ 'date-frmt' ] )



def is_japanese( article ):
    return article.url.find( 'amazon.co.jp' ) != -1



def osd_notify( title, body, picture ):
    init( 'amazonCheck update' )

    for color in [ RED, GREEN, NOCOLOR ]:
        title = title.replace( color, '' )
        body = body.replace( color, '' )

    Notification ( title, body, abspath( picture ) ).show()



def print_notify( title, body, picture='' ):
    print( get_time() + ' ' + title + ' ' + body )



def sort_function( treemodel, iter1, iter2, index ):
    try:
        f1 = treemodel[iter1][index]
        f2 = treemodel[iter2][index]

        if f1.find( 'N/A' ) != -1:
            return 1
        elif f2.find( 'N/A' ) != -1:
            return -1

        f1 = float( search( '[0-9]+([\.][0-9]{2})', f1 ).group() )
        f2 = float( search( '[0-9]+([\.][0-9]{2})', f2 ).group() )

        if f1 > f2:
            return -1
        elif f1 < f2:
            return 1
        else:
            return 0

    except ValueError:
        return 0



#-----------------------------------------------------------------------
#-----------------------------------------------------------------------


if __name__ == '__main__':
    info( s[ 'dashes' ] )
    info( s[ 'str-prgm' ] )

    [ SHOW_NOTIFICATIONS, SHOW_DEL_DIALOG, ALTERNATING_ROW_COLOR,
      MIN_SLEEPTIME, MAX_SLEEPTIME ] = read_config_file()

    info( s[ 'str-mn-lp' ] )

    mywindow = MainWindow()
    mywindow.main()
