#!/usr/bin/python -u
# -*- coding: utf-8 -*-

from amazonCheckTrans import strings as s
from colors import RED, GREEN, NOCOLOR

from pynotify import init, Notification
from os.path import abspath
from urllib2 import Request, urlopen
from signal import alarm, signal, SIGALRM
from time import strftime, time
from sys import argv, exit
from re import search
from os import name

TIMEOUT_TIME = 5


def timeout( seconds ):
    alarm( seconds )


def timeout_handler( signum, frame ):
    raise TimeoutException( Exception )


signal( SIGALRM, timeout_handler )


class TimeoutException( Exception ):
    pass


USER_AGENT = { 'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:15.0) Gecko/20100101 Firefox/15.0.1' }


def format_price( string ):
    format_from = [ '\n', '\t', '  ', ',', '+' ]
    format_to = [ '', '', '', '.', '' ]

    for index in range( 0, len( format_from ) ):
        string = string.replace( format_from[ index ], format_to[ index ] )

    currency = search( '[^ .,0-9]*', string ).group()

    try:
        price = float( search( '[0-9]+[.][0-9]+', string ).group() )
    except ValueError:
        price = s[ 'N/A' ]
    except AttributeError:
        price = s[ 'N/A' ]

    return ( price, currency )



def format_title( string ):
    #format_from = [ '&auml;', '&Auml;', '\xc3\x84', '&ouml;', '&Ouml;', '\xc3\x96', '&uuml;', '\xc3\xbc', '&Uuml;', '\xc3\x9c', '&szlig;', '\u00df', '\xdf', '\xc3\x9f', '&amp;', '&quot;', '&#39;', '\0', '\u0000' ]
    #format_to = [ 'ä', 'Ä', 'Ä', 'ö', 'Ö', 'Ö', 'ü', 'ü', 'Ü', 'Ü', 'ss', 'ss', 'ss', 'ss', '&', '\'', '\'', '', '' ]
#
    #for i in range( 0, len( format_from ) ):
        #string = string.replace( format_from[ i ], format_to[ i ] )

    return string.decode( 'ascii', 'replace' )



def get_min_price( price_list ):
    min_price = 99999999999999
    changed = False

    for price in price_list:
        if price[0] == s[ 'N/A' ]:
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
        if price_list[0][0] == s[ 'N/A' ]:
            return -1
        else:
            return price_list[0][0]

    div_time = int( round( time() ) ) - price_list[0][1]

    if price_list[-1][0] == s[ 'N/A' ]:
        div_time -= int( round( time() ) ) - price_list[-1][1]
    else:
        changed = True
        avg += price_list[-1][0] * (int( round( time() ) ) - price_list[-1][1])


    for i in range( 2, length + 1 ):

        index = length - i

        if price_list[ index ][0] == s[ 'N/A' ]:
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
        if price[0] == s[ 'N/A' ]:
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
        timeout( TIMEOUT_TIME )
        temp_file = urlopen( Request( url.replace( 'product', 'offer-listing' ) + '?condition=new', '', USER_AGENT ) ).read()
        timeout( 0 )
    except IOError:
        return ( -1, -1, -1, -1 )

    except ValueError:
        return ( -2, -2, -2, -2 )

    except TimeoutException:
        return ( -3, -3, -3, -3 )


    #Finding the title
    title = temp_file[ temp_file.find( '<title' ) + 7 : temp_file.find( '</title>' ) ]


    #Shortening it
    for string in [ ': Amazon', 'Amazon.com: ', 'Amazon.de: ', 'Einkaufsangebote: ' ]:
        title = title.replace( string, '' )


    #Finding the price
    price_pos = temp_file.find( '<span class="price">' ) + 20

    if  price_pos != -1 + 20:
        price = temp_file[ price_pos : temp_file.find( '</span>', price_pos ) ]

    else:
        price = s[ 'N/A' ]

    #Finding shipping
    shipping_pos = temp_file.find( '<span class="price_shipping">', price_pos ) + 29

    if  shipping_pos != -1 + 29:
        shipping = temp_file[ shipping_pos : temp_file.find( '</span>', shipping_pos ) ]

    else:
        shipping = '0.00'


    #Formating price and currency
    ( price, currency ) = format_price( price )
    ( shipping, unused ) = format_price( shipping )

    #Finding picture
    pic_pos = temp_file.find( '<div id="productheader">' ) + 24

    if pic_pos != -1 + 24:
        pic_pos = temp_file.find( '<img src="', pic_pos ) + 10
        picture = temp_file[ pic_pos : temp_file.find( '"', pic_pos ) ]

    else:
        picture = ''


    return ( title, currency, price + shipping, picture )



def get_time():
    return strftime( s[ 'date-frmt' ] )



def print_help_text():
    print( '' )
    print( s[ 'help-add' ] )
    print( s[ 'help-del' ] )
    print( s[ 'help-show' ] )
    print( s[ 'help-help' ] )
    print( '' )
    print( s[ 'help-slnt' ] )
    print( s[ 'help-upon' ] )
    print( s[ 'help-verb' ] )
    print( '' )
    print( s[ 'help-mnsl' ] )
    print( s[ 'help-mxsl' ] )
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

        Notification ( title, format_title( body ), abspath( picture ) ).show()
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
