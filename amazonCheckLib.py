#!/usr/bin/python -u
# -*- coding: utf-8 -*-

from os.path import expanduser
from time import strftime
from os import remove
from urllib import urlopen
from re import search
from sys import argv, exit
from hashlib import md5
from json import dumps, loads
#from threading import Thread, activeCount

GRAY = '\033[90m'
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
PURPLE = '\033[95m'
LIGHT_BLUE = '\033[96m'
NOCOLOR = '\033[0m'


def remove_all_files():
    remove( expanduser( '~' ) + '/.amazonCheck.prices' )
    remove( expanduser( '~' ) + '/.amazonCheck.titles' )
    remove( expanduser( '~' ) + '/.amazonCheck.links' )


def is_valid( lines ):

    data = lines[ 0 : -1]

    hash_string = lines[ -1 ]

    if md5( ''.join( data ).replace( '\n', '' ) ).hexdigest() == hash_string:
        return True
    else:
        return False


def get_time():
    return strftime( '%H:%M:%S' )


def print_help():
    print( '' )
    print( ' amazonCheck add \'link1\' \'link2\'             Add article(s) to the list' )
    print( ' amazonCheck update                          Update the prices' )
    print( ' amazonCheck delete                          Bring up the delete menu' )
    print( ' amazonCheck clearlist                       Deletes all entries' )
    print( ' amazonCheck [show]                          Show all articles' )
    print( '' )
    print( ' amazonCheck (--help, help)                  Print this help' )
    print( '' )


def shorten_amazon_link( url ):
    offset = url.find( 'amazon.' )

    domain = url[ url.find( '.' , offset ) + 1 : url.find( '/', offset ) ]

    try:

        return_url = 'http://www.amazon.' + domain + '/gp/product/' + search( '\/[A-Z0-9]{10}\/', url ).group()[1: -1] + '/'

    except AttributeError:

        exit( 'Link couldn\'t be parsed.'  )

    return return_url


def format_price( string ):
    format_from = [ '\n', '\t', '  ' ]
    format_to = [ '', '', '' ]

    for index in range( 0, len( format_from ) ):
        string = string.replace( format_from[ index ], format_to[ index ] )

    return string


def format_title( string ):
    format_from = [ '&auml;', '&Auml;', '&ouml;', '&Ouml;', '&uuml;', '&Uuml;', '&szlig;', '&amp;', '&quot;']
    format_to = [ 'ä', 'Ä', 'ö', 'Ö', 'ü', 'Ü', 'ß', '&', '\'' ]

    for i in range( 0, len( format_from ) ):
        string = string.replace( format_from[ i ], format_to[ i ] )

    return string


def add_article( url ):

    ( title, price ) = get_info_for( url )

    urls = read_links()
    prices = read_prices()
    titles = read_titles()

    urls.append( url )
    prices.append( price )
    titles.append( title )

    write_links( urls )
    write_prices( prices )
    write_titles( titles )


def delete_article():
    print_list( is_delete_menu = True )

    titles = read_titles()
    prices = read_prices()
    links = read_links()

    print( '\n' + 'What entry do you want to delete? (0 to quit) '),

    entry = int( raw_input() ) - 1

    if not entry in range( 0, len( links ) ):
        exit()

    titles = read_titles()
    prices = read_prices()
    links = read_links()

    titles.pop( entry )
    prices.pop( entry )
    links.pop( entry )

    write_links( links )
    write_prices( prices )
    write_titles( titles )


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


def read_links():

    try:
        data = open( expanduser( '~' ) + '/.amazonCheck.links', 'r' ).readlines()

        if not len( data ) or not is_valid( data ):
            remove_all_files()
            print( 'Invalid file. Files were deleted.' )
            exit( 1 )

    except IOError:
        return []

    return data[ 0 : -1 ]


def read_titles():
    try:
        data = open( expanduser( '~' ) + '/.amazonCheck.titles', 'r' ).readlines()

        if not len( data ) or not is_valid( data ):
            remove_all_files()
            print( 'Invalid file. Files were deleted.' )
            exit( 1 )

    except IOError:
        return []


    return data[ 0 : -1 ]


def read_prices():
    try:
        data = open( expanduser( '~' ) + '/.amazonCheck.prices', 'r' ).readlines()

        if not len( data ) or not is_valid( data ):
            remove_all_files()
            print( 'Invalid file. Files were deleted.' )
            exit( 1 )

    except IOError:
        return []

    return data[ 0 : -1 ]


def updated_info():
    prices = []
    titles = []

    urls = read_links()

    length = len( urls )

    for index in range( 0, length ):
        print( '\r[' + get_time() + '] Reading: ' + str( index + 1 ) + '/' + str( length ) ),

        temp_info = get_info_for( urls[ index ] )

        titles.append( temp_info[0] )
        prices.append( temp_info[1] )


    print( '\r                           ' ),
    return ( titles, prices )


def write_links( links ):
    if len( links ):
        links_file = open( expanduser( '~' ) + '/.amazonCheck.links' , 'w')

        length = len( links )

        for index in range( 0, length ):
            links[ index ] = links[ index ].replace( '\n', '' ) + '\n'

        links_file.write( ''.join( links ) )

        hash_string = md5( ''.join( links ).replace( '\n', '' ) ).hexdigest()

        links_file.write( hash_string )
    else:
        remove_all_files()

def write_titles( titles ):
    if len( titles ):
        titles_file = open( expanduser( '~' ) + '/.amazonCheck.titles' , 'w')

        length = len( titles )

        for index in range( 0, length ):
            titles[ index ] = titles[ index ].replace( '\n', '' ) + '\n'

        titles_file.write( ''.join( titles ) )

        hash_string = md5( ''.join( titles ).replace( '\n', '' ) ).hexdigest()

        titles_file.write( hash_string )
    else:
        remove_all_files()


def write_prices( prices ):
    if len( prices ):
        prices_file = open( expanduser( '~' ) + '/.amazonCheck.prices' , 'w')

        length = len( prices )

        for index in range( 0, length ):
            prices[ index ] = prices[ index ].replace( '\n', '' ) + '\n'

        prices_file.write( ''.join( prices ) )

        hash_string = md5( ''.join( prices ).replace( '\n', '' ) ).hexdigest()

        prices_file.write( hash_string )
    else:
        remove_all_files()


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
        title = format_title( title )


    if temp_file.find( '<b class="priceLarge">') != -1:
        price = temp_file[ temp_file.find( '<b class="priceLarge">') + 22 : temp_file.find( '</b>', temp_file.find( '<b class="priceLarge">') + 22 ) ]
    else:
        price = 'N/A'

    price = format_price( price )

    return ( title, price )


#-----------------------------------------------------------------------


if __name__ == '__main__':

    if len( argv ) < 2:
        print_list()

    elif len( argv ) < 3 and argv[1] == 'show':
        print_list()

    elif len( argv ) < 3 and argv[1] == 'update':
        try:
            old_prices = read_prices()

            ( updated_titles, updated_prices ) = updated_info()

            write_prices( updated_prices )
            write_titles( updated_titles )

            print_list( old_prices, False )
        except OSError:
            print( '\rFiles not found ( add articles before trying to look at them ).' )
            exit( 1 )

    elif len( argv ) < 3 and argv[1] == '--help' or argv[1] == 'help':
        print_help()

    elif len( argv ) < 3 and argv[1] == 'delete':
        delete_article()

    elif len( argv ) < 3 and argv[1] == 'clearlist':
        try:
            remove_all_files()
        except OSError:
            pass

    elif len( argv ) > 2 and argv[1] == 'add':

        for index in range( 2, len( argv ) ):
            url = shorten_amazon_link( argv[ index ] )
            add_article( url )

    else:
        print_help()














