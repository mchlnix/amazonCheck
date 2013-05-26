#!/usr/bin/python2.7 -u
# -*- coding: utf-8 -*-

from pricelib import min_price, avg_price, max_price

from urllib2 import Request, urlopen
from time import time, sleep
from re import search

JAPAN_HACK = False

EUR = u'€'
GBP = u'£'
USD = u'$'
YEN = u'￥'

TIMEOUT_TIME = 5

USER_AGENT = { 'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:15.0) Gecko/20100101 Firefox/15.0.1' }

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

            self.name = get_name( source )

            price, currency = get_price( source )

            self.currency = currency.replace( 'EUR', u'€' )

            self.cur_str = currency + ' %s'

            self.category = get_category( source )

            self.pic_url = get_picture( source )

            if price != self.price:
                self.price_data.append( [ price, int( time() ) ] )
                self.min = min_price( self.price_data )
                self.max = max_price( self.price_data )

            self.pic_name = search( '\/[A-Z0-9]{10}\/', self.url ).group()[1: -1] + '.jpg'

        except IOError:
            self.bad_conn = True
            return
        except ValueError:
            self.bad_url = True
            return

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
                return -1



def format_price( string, currency=None ):
    format_from = [ '\n', '\t', '  ', '+' ]
    format_to   = [  '' ,  '' ,  '' , ''  ]

    for _from, _to in zip( format_from, format_to ):
        string = string.replace( _from, _to )

    if currency is None:
        try:
            currency = search( '[^ .,0-9]*', string ).group()
        except:
            raise LookupError( 'Couldn\'t find currency' )

    if currency == 'EUR':
        regexp = '[0-9]{1,3}([.]*[0-9]{3})*([,][0-9]{2})'
    elif currency == GBP:
        regexp = '[0-9]{1,3}([,]*[0-9]*)([.][0-9]{2})'
    elif currency == YEN:
        regexp = '[0-9]{1,3}([,][0-9]{3})*'

    try:
        price = search( regexp, string ).group()

        if currency == YEN or currency == GBP:
            price = price.replace( ',', '' )
        else:
            price = price.replace( '.', '' ).replace( ',', '.' )

        price = float( price )

        return ( price, currency )

    except:
        raise LookupError( 'Couldn\'t find price' )



def get_category( source ):
    return get_tag_content( source=source, searchterm="id='nav-search-in-content'", format=True, encoded=False )



def get_encoding( source ):
    if JAPAN_HACK:
        tmp_index = source.find( 'ue_sn=\'' )
        url = source[ tmp_index + 7 : source.find( '\'', tmp_index + 7 ) ]
        if url == 'www.amazon.co.jp':
            return 'SHIFT_JIS'

    tmp_index = source.find( 'http-equiv="content-type"' ) + 25
    start = source.find( 'charset=', tmp_index ) + 8

    end = source.find( '"', start )

    encoding = source[ start : end ]

    return encoding



def get_picture( source ):
    try:
        temp = get_tag_content( source=source, searchterm='id="productheader"', format=False, encoded=False )
    except LookupError:
        return ''

    pic_pos = temp.find( '<img src="' ) + 10
    pic_url = temp[ pic_pos : temp.find( '"', pic_pos ) ]

    return pic_url



def get_price( source ):
    #Finding the price
    try:
        price_env = get_tag_content( source=source, searchterm='class="result"', format=False, encoded=False )
        price = get_tag_content( source=price_env, searchterm='class="price"', format=True, encoded=True )
    except LookupError:
        return 'N/A', 'N/A'

    ( price, currency ) = format_price( price )

    try:
        shipping = get_tag_content( source=price_env, searchterm='class="price_shipping"', format=False, encoded=True )
        ( shipping, unused ) = format_price( shipping, currency=currency )
    except LookupError:
        shipping = 0

    return round( price + shipping, 2 ), currency



def get_tag_content( source, searchterm, format=False, encoded=False ):
    if not encoded:
        encoding = get_encoding( source )
        source = unicode( source, encoding )

    tmp_index = source.find( searchterm )

    tag_start = source[ 0: tmp_index ].rfind( '<' ) + 1
    tag_end   = source.find( ' ', tag_start )

    tag_name = source[ tag_start : tag_end ]

    start = source.find( '>', tmp_index ) + 1

    end = source.find( '</%s>' % tag_name, start )

    if min( tmp_index, start, end ) == -1:
        raise LookupError( 'Couldn\'t find tag with search term \'%s\'.' % searchterm )

    content = source[ start : end ]

    if format:
        content = content.replace( '\n', ' ' )
        content = ' '.join( content.split() )

    return content



def get_name( source ):
    try:
        name = get_tag_content( source=source,
                                searchterm='"producttitle"',
                                format=True,
                                encoded=False,
                                )
    except LookupError:
        with open( '/tmp/derp.html', 'w') as f:
            f.write( source )

        raise LookupError( 'Could not find name of article.' )

    return name



def shorten_amazon_link( url ):
    offset = url.find( 'amazon.' )
    domain = url[ url.find( '.' , offset ) + 1 : url.find( '/', offset ) ]

    try:
        return_url = 'http://www.amazon.' + domain + '/gp/product/' + search( '\/[A-Z0-9]{10}', url ).group()[1: ] + '/'

    except AttributeError:
        return_url = ''

    return return_url



def set_japan_hack( activated ):
    global JAPAN_HACK

    JAPAN_HACK = activated


if __name__ == '__main__':
    set_japan_hack( True )

    art = Article( 'http://www.amazon.co.jp/HUNTER%C3%97HUNTER-32-%E3%82%B8%E3%83%A3%E3%83%B3%E3%83%97%E3%82%B3%E3%83%9F%E3%83%83%E3%82%AF%E3%82%B9-%E5%86%A8%E6%A8%AB-%E7%BE%A9%E5%8D%9A/dp/4088706986/ref=tmm_comic_meta_binding_title_0?ie=UTF8&qid=1369566753&sr=8-3' )

    art.update()

    print art.price

    for k, v in art.__dict__.items():
        print k, v

    print '-------------------------------------------'

    art = Article( 'http://www.amazon.de/gp/product/B006I3OH6Q/' )

    art.update()

    print art.price

    for k, v in art.__dict__.items():
        print k, v

    print '-------------------------------------------'

    art = Article( 'http://www.amazon.co.jp/%E3%83%9A%E3%83%B3%E3%82%BF%E3%83%83%E3%82%AF%E3%82%B9-50-mm-DA-%E3%83%9A%E3%83%B3%E3%82%BF%E3%83%83%E3%82%AF%E3%82%B9%E3%83%AA%E3%82%B3%E3%83%BC%E3%82%A4%E3%83%A1%E3%83%BC%E3%82%B8%E3%83%B3%E3%82%B0/dp/B0087MQ1B0/ref=sr_1_1?ie=UTF8&qid=1369570227&sr=8-1&keywords=da' )

    art.update()

    print art.price

    for k, v in art.__dict__.items():
        print k, v

    print '-------------------------------------------'

    art = Article( 'http://www.amazon.co.uk/AKG-True-Hybrid-In-Ear-Headphones/dp/B00A9H8XTY/ref=sr_1_1?m=A3P5ROKL5A1OLE&s=electronics-accessories&ie=UTF8&qid=1369574490&sr=1-1' )

    art.update()

    print art.price

    for k, v in art.__dict__.items():
        print k, v
