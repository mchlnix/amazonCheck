#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pynotify import init, Notification
from os.path import abspath
from urllib import urlopen
from time import strftime, time
from sys import argv, exit
from re import search
from os import name

if name == 'posix':
    BOLD_WHITE = '\033[1;97m'
    GRAY = '\033[90m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    LIGHT_BLUE = '\033[96m'
    NOCOLOR = '\033[0m'

else:
    BOLD_WHITE = ''
    GRAY = ''
    RED = ''
    GREEN = ''
    YELLOW = ''
    BLUE = ''
    PURPLE = ''
    LIGHT_BLUE = ''
    NOCOLOR = ''



def format_price( string ):
    format_from = [ '\n', '\t', '  ', ',' ]
    format_to = [ '', '', '', '.' ]

    for index in range( 0, len( format_from ) ):
        string = string.replace( format_from[ index ], format_to[ index ] )

    currency = search( '[^ .,0-9]*', string ).group()

    try:
        price = float( search( '[0-9]+[.][0-9]+', string ).group() )
    except ValueError:
        price = 'N/A'
    except AttributeError:
        price = 'N/A'

    return ( price, currency )



def format_title( string ):
    format_from = [ '&auml;', '&Auml;', '\xc3\x84', '&ouml;', '&Ouml;', '\xc3\x96', '&uuml;', '\xc3\xbc', '&Uuml;', '\xc3\x9c', '&szlig;', '\xdf', '\xc3\x9f', '&amp;', '&quot;', '&#39;' ]
    format_to = [ 'ä', 'Ä', 'Ä',  'ö', 'Ö', 'Ö', 'ü', 'ü', 'Ü', 'Ü', 'ß','ß', 'ß', '&', '\'', '\'' ]

    for i in range( 0, len( format_from ) ):
        string = string.replace( format_from[ i ], format_to[ i ] )

    return string



def get_min_price( price_list ):
    min_price = 99999999999999
    changed = False

    for price in price_list:
        if price[0] == 'N/A':
            continue
        else:
            if price[0] < min_price:
                changed = True
                min_price = price[0]

    if changed:
        return min_price
    else:
        return -1



def get_avg_price( price_list ):
    avg = 0
    length = len( price_list )
    changed = False

    if length == 1:
        if price_list[0][0] == 'N/A':
            return -1
        else:
            return price_list[0][0]

    div_time = int( round( time() ) ) - price_list[0][1]

    if price_list[-1][0] == 'N/A':
        div_time -= int( round( time() ) ) - price_list[-1][1]
    else:
        changed = True
        avg += price_list[-1][0] * (int( round( time() ) ) - price_list[-1][1])


    for i in range( 2, length + 1 ):

        index = length - i

        if price_list[ index ][0] == 'N/A':
            div_time -= price_list[ index + 1 ][1] - price_list[ index ][1]
            continue

        avg += price_list[ index ][0] * ( price_list[ index + 1 ][1] - price_list[ index ][1] )
        changed = True

    try:
        if changed:
            return round( avg / div_time, 2 )
        else:
            return -1

    except ZeroDivisionError:
        return -1


def get_max_price( price_list ):
    max_price = 0
    changed = False

    for price in price_list:
        if price[0] == 'N/A':
            continue
        else:
            if price[0] > max_price:
                changed = True
                max_price = price[0]

    if changed:
        return max_price
    else:
        return -1



def get_info_for( url ):
    try:
        temp_file = urlopen( url ).read()

    except IOError:
        return ( -1, -1, -1, -1 )


    #Finding the title
    title = temp_file[ temp_file.find( '<title' ) + 7 : temp_file.find( '</title>' ) ]

    if title.find( ': Amazon' ) != -1:
        title = format_title( title[ 0 : title.find( ': Amazon' ) ] )

    elif title.find( 'Amazon.com: ' ) != -1:
        title = format_title( title[ title.find( 'Amazon.com: ' ) + 12 : ] )

    else:
        title = format_title( title ) + '\0'


    #Finding the price
    price_pos = temp_file.find( '<b class="priceLarge">') + 22

    if  price_pos != -1:
        price = temp_file[ price_pos : temp_file.find( '</b>', price_pos ) ]

    else:
        price = 'N/A'


    #Formating price and currency
    ( price, currency ) = format_price( price )


    #Finding picture
    pic_pos = temp_file.find( '<div class="main-image-inner-wrapper">' ) + 38

    if pic_pos != -1:
        picture = temp_file[ pic_pos : temp_file.find( '</div>', pic_pos ) ]

        url_pos = picture.find( 'src="' ) + 5
        picture = picture[ url_pos : picture.find( '"', url_pos ) ]
    else:
        picture = ''


    return ( title, currency, price, picture )



def get_time():
    return strftime( '[%d.%m.%y - %H:%M:%S]' )



def print_help_text():
    print( '' )
    print( 'add "amazon_link"        adds an article to the list' )
    print( 'show                     shows an overview for all articles' )
    print( 'help, -h, --help         displays this help text' )
    print( '' )
    print( '-s, --silent             runs in the backfround completely silent' )
    print( '-u, --updates_only       shows notification bubbles, otherwise silent' )
    print( '-v, --verbose            mirrors the logfile to the commandline' )
    print( '' )
    print( '--min_sleep=1234         sets the min. time between updates to 1234s' )
    print( '--max_sleep=1234         sets the max. time between updates to 1234s' )
    print( '' )



def print_notification( title, body, picture='' ):
    print( get_time() + ' ' + title + ' ' + body )



def send_notification( title, body, picture ):
    if name == 'posix':
        if not init ("icon-summary-body"):
            return false

        for color in [ RED, GREEN, NOCOLOR ]:
            title = title.replace( color, '' )
            body = body.replace( color, '' )

        # try the summary-body case
        Notification ( title, body, abspath( picture ) ).show()
    else:
        return false



if name == 'posix':
    notify = send_notification

else:
    notify = print_notification



def shorten_amazon_link( url ):
    offset = url.find( 'amazon.' )
    domain = url[ url.find( '.' , offset ) + 1 : url.find( '/', offset ) ]

    try:
        return_url = 'http://www.amazon.' + domain + '/gp/product/' + search( '\/[A-Z0-9]{10}', url ).group()[1: ] + '/'

    except AttributeError:
        return_url = ''

    return return_url
















