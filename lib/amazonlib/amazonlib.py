#!/usr/bin/python2.7 -u
# -*- coding: utf-8 -*-

from pricelib import min_price, avg_price, max_price

from urllib2 import Request, urlopen
from time import time
from re import search

TIMEOUT_TIME = 5

USER_AGENT = { 'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:15.0) Gecko/20100101 Firefox/15.0.1' }

class Article():
    def __init__( self,
                  url = '',
                  ):
        self.url = shorten_amazon_link( url )
        self.name = 'No name found'
        self.price_data = []

        self.min = -1
        self.avg = -1
        self.max = -1

        self.currency = ''
        self.pic_url = ''
        self.pic_name = ''

        self.bad_conn = False
        self.bad_url = False

    def update( self ):

        self.bad_conn = self.bad_url = False
        try:
            self.name, self.currency, price, self.pic_url = get_info_for( self.url )

            if price != self.price:
                self.price_data.append( [ price, int( time() ) ] )
                self.min = min_price( self.price_data )
                self.max = max_price( self.price_data )

            self.pic_name = search( '\/[A-Z0-9]{10}\/', self.url ).group()[1: -1] + '.jpg'

        except IOError:
            self.bad_conn = True
        except ValueError:
            self.bad_url = True

        self.avg = avg_price( self.price_data )

    def __getattr__( self, name ):
        if name=='price':
            try:
                return self.price_data[-1][0]
            except IndexError:
                return 0



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



def get_encoding( web_page ):
    tmp_index = web_page.find( 'http-equiv="content-type"' ) + 25
    start = web_page.find( 'charset=', tmp_index ) + 8

    end = web_page.find( '"', start )

    encoding = web_page[ start : end ]

    return encoding



def get_title( web_page ):
    encoding = get_encoding( web_page )

    start = web_page.find( '"producttitle"' )

    if start == -1:
        raise LookupError( 'Could not find name of article.' )

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
    url = url.replace( 'product', 'offer-listing' )
    url = ''.join( [ url, '?condition=new' ] )
    source = urlopen( url=Request( url=url,
                                   data='',
                                   headers=USER_AGENT
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



def shorten_amazon_link( url ):
    offset = url.find( 'amazon.' )
    domain = url[ url.find( '.' , offset ) + 1 : url.find( '/', offset ) ]

    try:
        return_url = 'http://www.amazon.' + domain + '/gp/product/' + search( '\/[A-Z0-9]{10}', url ).group()[1: ] + '/'

    except AttributeError:
        return_url = ''

    return return_url
