#!/usr/bin/python2.7 -u
# -*- coding: utf-8 -*-

from pricelib import min_price, avg_price, max_price

from urllib2 import Request, urlopen
from time import time, sleep
from re import search

class CategoryNotFound( LookupError ):
    pass
class CurrencyNotFound( LookupError ):
    pass
class NameNotFound( LookupError ):
    pass
class PriceNotFound( LookupError ):
    pass
class ShippingNotFound( LookupError ):
    pass
class TagNotFound( LookupError ):
    pass
class URLNotFound( LookupError ):
    pass

CAN = u'CDN$'
EUR = u'€'
GBP = u'£'
USD = u'$'
YEN = u'￥'

TIMEOUT_TIME = 5

USER_AGENT = { 'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:15.0) Gecko/20100101 Firefox/15.0.1' }

ENCODING_DICT = { 'www.amazon.ca'   : 'iso-8859-15',
                  'www.amazon.com'  : 'iso-8859-1',
                  'www.amazon.co.jp': 'shift-jis',
                  'www.amazon.co.uk': 'iso-8859-1',
                  'www.amazon.cn'   : 'utf-8',
                  'www.amazon.de'   : 'iso-8859-1',
                  'www.amazon.es'   : 'iso-8859-1',
                  'www.amazon.fr'   : 'iso-8859-1',
                  'www.amazon.it'   : 'iso-8859-1',
                  }


class Article():
    def __init__( self,
                  url = '',
                  ):
        self.url = shorten_amazon_link( url )
        self.name = None
        self.category = None
        self.price_data = []

        self.min = -1
        self.avg = -1
        self.max = -1

        self.currency = None
        self.cur_str  = None
        self.pic_url  = None
        self.pic_name = None

        self.bad_conn = False
        self.bad_url  = False

    def update( self ):

        self.bad_conn = self.bad_url = False

        try:
            url = self.url.replace( 'product', 'offer-listing' )
            url = ''.join( [ url, '?condition=new' ] )
            source = urlopen( url=Request( url=url,
                                           data='',
                                           headers=USER_AGENT
                                           ),
                              data=None,
                              timeout=TIMEOUT_TIME,
                              ).read()

            tmp_index = source.find( 'ue_sn=\'' )
            url = source[ tmp_index + 7 : source.find( '\'', tmp_index + 7 ) ]

            encoding = ENCODING_DICT.setdefault( url, get_encoding( source ) )
            source = unicode( source, encoding )

        except IOError:
            self.bad_conn = True
            return
        except ValueError:
            self.bad_url = True
            return

        try:
            self.name = get_name( source )
        except NameNotFound:
            pass

        try:
            self.category = get_category( source )
        except CategoryNotFound:
            pass

        try:
            self.pic_url = get_picture( source )
        except URLNotFound:
            pass

        try:
            price, currency = get_price( source )
            self.currency = currency.replace( 'EUR', EUR )
            self.cur_str = self.currency + ' %s'
        except PriceNotFound:
            price = 'N/A'
        except ( CurrencyNotFound, ShippingNotFound ):
            price = self.price

        if price != self.price:
            self.price_data.append( [ price, int( time() ) ] )
            self.min = min_price( self.price_data )
            self.max = max_price( self.price_data )

        self.pic_name = search( '\/[A-Z0-9]{10}\/', self.url ).group()[1: -1] + '.jpg'

        self.avg = avg_price( self.price_data )

    def __getattr__( self, name ):
        if name=='price':
            try:
                price = self.price_data[-1][0]

                if self.currency == YEN:
                    return int( price )
                else:
                    return price
            except IndexError:
                return None



def format_price( string, currency=None ):
    format_from = [ '\n', '\t', '  ', '+' ]
    format_to   = [  '' ,  '' ,  '' , ''  ]

    for _from, _to in zip( format_from, format_to ):
        string = string.replace( _from, _to )

    if currency is None:
        try:
            currency = search( '[^ .,0-9]*', string ).group()
        except AttributeError:
            raise CurrencyNotFound

    if currency == 'EUR':
        regexp = '[0-9]{1,3}([.]*[0-9]{3})*([,][0-9]{2})'
    elif currency in [ CAN, GBP, USD ]:
        regexp = '[0-9]{1,3}([,]*[0-9]*)([.][0-9]{2})'
    elif currency == YEN:
        regexp = '[0-9]{1,3}([,][0-9]{3})*'

    try:
        price = search( regexp, string ).group()

        if currency in [ CAN, GBP, USD, YEN ]:
            price = price.replace( ',', '' )
        else:
            price = price.replace( '.', '' ).replace( ',', '.' )

        price = float( price )

        return ( price, currency )

    except AttributeError:
        raise PriceNotFound



def get_category( source ):
    try:
        return get_tag_content( source=source,
                                searchterm="id='nav-search-in-content'",
                                format=True,
                                )
    except TagNotFound:
        raise CategoryNotFound



def get_encoding( source ):
    start = source.find( 'charset=' ) + 8

    end = source.find( '"', start )

    encoding = source[ start : end ]

    return encoding



def get_picture( source ):
    try:
        temp = get_tag_content( source=source, searchterm='id="productheader"', format=False )
    except TagNotFound:
        raise URLNotFound

    pic_pos = temp.find( '<img src="' ) + 10
    pic_url = temp[ pic_pos : temp.find( '"', pic_pos ) ]

    return pic_url



def get_price( source ):
    price = None
    price_env = None
    shipping = None
    try:
        price_env = get_tag_content( source=source, searchterm='class="result"', format=False )
        price = get_tag_content( source=price_env, searchterm='class="price"', format=True )
    except TagNotFound as T:
        if T.args[0] == 'class="price"':
            raise PriceNotFound
        else:
            pass

    try:
        if price is None:
            price = get_tag_content( source=source, searchterm='a-size-large a-color-price', format=True )
        else:
            pass
    except TagNotFound:
        raise PriceNotFound

    try:
        ( price, currency ) = format_price( price )
    except CurrencyNotFound:
        raise CurrencyNotFound
    except PriceNotFound:
        raise PriceNotFound

    try:
        if price_env is not None:
            shipping = get_tag_content( source=price_env, searchterm='class="price_shipping"', format=True )
        else:
            shipping = get_tag_content( source=source, searchterm='a-color-secondary', format=True )

    except TagNotFound:
        shipping = 0

    if shipping != 0:
        if shipping[0] == '+':
            try:
                ( shipping, unused ) = format_price( shipping, currency=currency )
            except CurrencyNotFound:
                raise CurrencyNotFound
            except PriceNotFound:
                raise ShippingNotFound

        else:
            shipping = 0

    return round( price + shipping, 2 ), currency



def get_tag_content( source, searchterm, format=False ):
    tmp_index = source.find( searchterm )

    tag_start = source[ 0: tmp_index ].rfind( '<' ) + 1
    tag_end   = source.find( ' ', tag_start )

    tag_name = source[ tag_start : tag_end ]

    start = source.find( '>', tmp_index ) + 1

    end = source.find( '</%s>' % tag_name, start )

    if min( tmp_index, start, end ) == -1:
        raise TagNotFound( searchterm )

    content = source[ start : end ]

    if format:
        content = content.replace( '\n', ' ' )
        content = ' '.join( content.split() )

    return content



def get_name( source ):
    for searchterm in [ '"producttitle"', 'a-spacing-none' ]:
        try:
            name = get_tag_content( source, searchterm, format=True )
            return name
        except TagNotFound:
            continue
    else:
        raise NameNotFound



def shorten_amazon_link( url ):
    offset = url.find( 'amazon.' )
    domain = url[ url.find( '.' , offset ) + 1 : url.find( '/', offset ) ]

    try:
        return_url = 'http://www.amazon.' + domain + '/gp/product/' + search( '\/[A-Z0-9]{10}', url ).group()[1: ] + '/'

    except AttributeError:
        return_url = ''

    return return_url



if __name__ == '__main__':
    urls = [ 'http://www.amazon.cn/gp/offer-listing/B00AZR7NSA/',#China
    'http://www.amazon.fr//dp/B005OS4NHE/',                      #France
    'http://www.amazon.com/gp/product/0735619670/',              #USA
    'http://www.amazon.ca/gp/product/B00ADSBS3M/',               #Canada
    'http://www.amazon.co.jp/gp/product/B0042D73LA/',            #Japan
    'http://www.amazon.es/gp/product/B00BP5DKM4/',               #Spain
    'http://www.amazon.co.uk/gp/product/B008U5H7Q2/',            #GB
    'http://www.amazon.it/gp/product/B009KR4UNM/',               #Italy
    'http://www.amazon.de/gp/product/B009WJC77O/',               #Germany
    ]

    for url in urls:
        art = Article( url )
        art.update()

        print 'Name    : ', art.name
        print 'Price   : ', art.price
        print 'Currency: ', art.currency
        print 'URL     : ', art.url
        print '----------------------------------'
