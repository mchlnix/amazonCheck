#!/usr/bin/python2.7 -u
# -*- coding: utf-8 -*-

from amazonCheckTrans import strings as s
from colors import RED, GREEN, NOCOLOR

from pynotify import init, Notification
from os.path import abspath
from urllib2 import Request, urlopen
from time import strftime, time
from sys import argv, exit
from re import search
from os import name

TIMEOUT_TIME = 5

USER_AGENT = { 'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:15.0) Gecko/20100101 Firefox/15.0.1' }


def format_price( string ):
    format_from = [ '\n', '\t', '  ', ',', '+' ]
    format_to   = [  '' ,  '' ,  '' , '.', ''  ]

    for _from, _to in zip( format_from, format_to ):
        string = string.replace( _from, _to )

    try:
        currency = search( '[^ .,0-9]*', string ).group()
    except:
        raise LookupError( 'Couldn\'t find currency' )

    try:
        price = float( search( '[0-9]+[.][0-9]+', string ).group() )
    except:
        raise LookupError( 'Couldn\'t find price' )

    return ( price, currency )



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



def get_encoding( web_page ):
    tmp_index = web_page.find( 'http-equiv="content-type"' ) + 25
    start = web_page.find( 'charset=', tmp_index ) + 8

    end = web_page.find( '"', start )

    encoding = web_page[ start : end ]

    return encoding



def get_title( web_page ):
    encoding = get_encoding( web_page )

    start = web_page.find( '"producttitle"' )

    if start != -1:
        raise LookupError( 'Could not find name of article' )

    start = web_page.find( '>', start ) + 1

    end = web_page.find( '<', start )

    title = web_page[ start : end ]

    title = unicode( title, encoding )

    title = title.replace( '\n', '' )
    title = title.replace( '  ', '' )

    while title[0] == ' ':
        title = title[1:]

    while title[-1] == ' ':
        title = title[0:-1]

    return title



def get_price( source ):
    #Finding the price
    if source.find( '<tbody class="result">') != -1:
        price_pos = source.find( '<span class="price">' ) + 20

        if  price_pos != -1 + 20:
            price = source[ price_pos : source.find( '</span>', price_pos ) ]
        else:
            price = 'N/A'
    else:
        return s[ 'N/A' ], s[ 'N/A' ]

    #Finding shipping
    shipping_pos = source.find( '<span class="price_shipping">', price_pos ) + 29
    end_pos = source.find( '</td>', price_pos ) + 5

    if  shipping_pos != -1 + 29 and shipping_pos < end_pos:
        shipping = source[ shipping_pos : source.find( '</span>', shipping_pos ) ]
    else:
        shipping = '0.00'

    #Formating price and currency
    try:
        ( price, currency ) = format_price( price )
    except LookupError:
        return 'N/A', 'N/A'
    try:
        ( shipping, unused ) = format_price( shipping )
    except LookupError:
        return price, currency


    if shipping == 'N/A':
        print 'No shipping?'
        shipping = 0

    return round( price + shipping, 2 ), currency



def get_info_for( url ):

    source = urlopen( url=Request( url.replace( 'product',
                                                'offer-listing',
                                                 ) + '?condition=new',
                                   '',
                                   USER_AGENT
                                   ),
                      data=None,
                      timeout=TIMEOUT_TIME,
                      ).read()

    title = get_title( source )

    price, currency = get_price( source )

    #Finding picture
    pic_pos = source.find( '<div id="productheader">' ) + 24

    if pic_pos != -1 + 24:
        pic_pos = source.find( '<img src="', pic_pos ) + 10
        picture = source[ pic_pos : source.find( '"', pic_pos ) ]

    else:
        picture = ''

    return ( title, currency, price, picture )



def get_time():
    return strftime( s[ 'date-frmt' ] )



def print_notification( title, body, picture='' ):
    print( get_time() + ' ' + title + ' ' + body )



def send_notification( title, body, picture ):
    if name == 'posix':
        if not init ("icon-summary-body"):
            return false

        for color in [ RED, GREEN, NOCOLOR ]:
            title = title.replace( color, '' )
            body = body.replace( color, '' )

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
