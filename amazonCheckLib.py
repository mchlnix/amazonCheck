#!/usr/bin/env python
# -*- coding: utf-8 -*-


from urllib import urlopen
from time import strftime
from sys import argv, exit
from re import search


GRAY = '\033[90m'
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
PURPLE = '\033[95m'
LIGHT_BLUE = '\033[96m'
NOCOLOR = '\033[0m'


def get_time():
    return strftime( '[%H:%M:%S]' )


def shorten_amazon_link( url ):
    offset = url.find( 'amazon.' )
    domain = url[ url.find( '.' , offset ) + 1 : url.find( '/', offset ) ]

    try:
        return_url = 'http://www.amazon.' + domain + '/gp/product/' + search( '\/[A-Z0-9]{10}\/', url ).group()[1: -1] + '/'

    except AttributeError:
        return_url = ''

    return return_url


def format_price( string ):
    format_from = [ '\n', '\t', '  ', ',' ]
    format_to = [ '', '', '', '.' ]

    for index in range( 0, len( format_from ) ):
        string = string.replace( format_from[ index ], format_to[ index ] )

    currency = search( '[^ .,0-9]*', string ).group()

    try:
        price = float( search( '[0-9]*[.][0-9]*', string ).group() )
    except AttributeError:
        price = 'N/A'

    return ( price, currency )


def format_title( string ):
    format_from = [ '&auml;', '&Auml;', '\xc3\x84', '&ouml;', '&Ouml;', '\xc3\x96', '&uuml;', '\xc3\xbc', '&Uuml;', '\xc3\x9c', '&szlig;', '\xdf', '\xc3\x9f', '&amp;', '&quot;', '&#39;' ]
    format_to = [ 'ä', 'Ä', 'Ä',  'ö', 'Ö', 'Ö', 'ü', 'ü', 'Ü', 'Ü', 'ß','ß', 'ß', '&', '\'', '\'' ]

    for i in range( 0, len( format_from ) ):
        string = string.replace( format_from[ i ], format_to[ i ] )

    return string


def print_list( old_prices = [] , is_delete_menu = False ):

    try:
        COLOR = NOCOLOR

        titles = read_titles()
        prices = read_prices()

        if not ( len( titles ) and len( prices ) ):
            print( 'Files not found ( add articles before trying to look at them ).' )
            exit( 1 )

        fmt_prices_old = []
        fmt_prices_new = []

        if len( old_prices ) > 0:
            for index in range( 0, len( old_prices ) ):
                try:
                    fmt_prices_old.append( float( search( '[-]*[0-9]+[,.]{1}[0-9]{2}',  old_prices[ index ] ).group().replace( ',', '.' ) ) )
                except AttributeError:
                    fmt_prices_old.append( 'N/A' )
                try:
                    fmt_prices_new.append( float( search( '[-]*[0-9]+[,.]{1}[0-9]{2}',  prices[ index ] ).group().replace( ',', '.' ) ) )
                except AttributeError:
                    fmt_prices_new.append( 'N/A' )

    #for index in range( 0, len( old_prices ) ):
      #print( str( fmt_prices_new[ index ] ) + '    ' + str( fmt_prices_old[ index ] ) )

        print( '                ' )

        for index in range( 0, len( titles ) ):
            if is_delete_menu:
                print( str( index + 1 ) + '    ' + prices[ index ].replace( '\n' , '' ) + '\t---\t' + titles[ index ].replace( '\n' , '' ) )
            else:

                price_change = '\r'

                if len( prices ) > 0:
                    try:
                        if fmt_prices_new[ index ] == 'N/A':
                            prices[ index ] = 'N/A'
                            COLOR = RED
                            #price_change = '    ' + RED + 'Product is unavailable'+ NOCOLOR + '\n'
                        elif fmt_prices_new[ index ] < fmt_prices_old[ index ]:
                            COLOR = GREEN
                            price_change = '    ' + RED + str( fmt_prices_old[ index ] ) + NOCOLOR + ' > ' + GREEN + str( fmt_prices_new[ index ] ) + NOCOLOR + '\t - ' + GREEN + str( fmt_prices_old[ index ] - fmt_prices_new[ index ] ) + NOCOLOR + '\n'
                        elif fmt_prices_new[ index ] > fmt_prices_old[ index ]:
                            COLOR = RED
                            price_change = '    ' + GREEN + str( fmt_prices_old[ index ] ) + NOCOLOR + ' > ' + RED + str( fmt_prices_new[ index ] ) + NOCOLOR + '\t + ' + RED + str( fmt_prices_new[ index ] - fmt_prices_old[ index ] ) + NOCOLOR + '\n'
                        else:
                            COLOR = NOCOLOR
                    except:
                        pass

                print( ' ' + COLOR + prices[ index ].replace( '\n' , '' ) + '\t---\t' + titles[ index ].replace( '\n' , '' ) ) + NOCOLOR
                print( price_change ),

        print( '' )

    except IOError:
        print( 'Files not found ( add articles before trying to look at them ).' )
        exit( 1 )


def get_info_for( url ):
    try:
        temp_file = urlopen( url ).read()

    except IOError:
        exit( 'Error connecting' )

    title = temp_file[ temp_file.find( '<title' ) + 7 : temp_file.find( '</title>' ) ]

    if title.find( ': Amazon' ) != -1:
        title = format_title( title[ 0 : title.find( ': Amazon' ) ] )

    elif title.find( 'Amazon.com: ' ) != -1:
        title = format_title( title[ title.find( 'Amazon.com: ' ) + 12 : ] )

    else:
        title = format_title( title ) + '\0'

    if temp_file.find( '<b class="priceLarge">') != -1:
        price = temp_file[ temp_file.find( '<b class="priceLarge">') + 22 : temp_file.find( '</b>', temp_file.find( '<b class="priceLarge">') + 22 ) ]

    else:
        price = 'N/A'

    ( price, currency ) = format_price( price )

    return ( title, currency, price )















