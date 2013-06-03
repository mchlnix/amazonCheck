#!/usr/bin/python2.7 -u
# -*- coding: utf-8 -*-

from time import time

def min_price( price_list ):
    """Return the minimum price in the list of tupels or -1.
    
    Arguments:
    price_list -- list of tupels ( price or 'N/A', seconds in unix time )
    
    """
    tmp_list = sorted( price for price, time in price_list )

    for price in tmp_list:
        if price != 'N/A':
            return price
    else:
        return -1


def avg_price( price_list ):
    """Calculate the average price considering time, neglecting 'N/A'.
    
    Arguments:
    price_list -- list of tupels ( price or 'N/A', seconds in unix time )
    
    """
    changed = False
    avg = 0

    start_time = tmp_time = int( time() )

    for _price, _time in reversed( price_list ):
        if _price == 'N/A':
            start_time -= ( tmp_time - _time )
        else:
            changed = True
            avg += ( tmp_time - _time ) * _price

        tmp_time = _time

    if changed:
        try:
            return round( avg / float( start_time - price_list[0][1] ), 2 )
        except ZeroDivisionError:
            return price_list[0][0]
    else:
        return -1


def max_price( price_list ):
    """Return the maximum price in the list of tupels or -1.
    
    Arguments:
    price_list -- list of tupels ( price or 'N/A', seconds in unix time )
    
    """
    tmp_list = reversed( sorted( price for price, time in price_list ) )

    for price in tmp_list:
        if price != 'N/A':
            return price
    else:
        return -1


if __name__ == '__main__':
    mylists = [ [ (10, int( time() - 5000 )), (20, int( time() - 3000 )), ('N/A', int( time() - 2000 )), (15, int( time() - 1000 )) ],
                [ (10, int( time() - 5000 )) ],
                [ ('N/A', int( time() - 2000 )) ],
                [ (10 , int( time() - 6000 )), (20 , int( time() - 5000 )), (30 , int( time() - 4000 )), (40 , int( time() - 3000 )), ( 50 , int( time() - 2000 )), ('N/A' , int( time() - 1000 )) ],
                [],
                [ (20, int( time() - 4000)), ('N/A', int( time() - 2000)) ],
                [ (0, int( time() )) ],
                [ (20, int( time() - 7000 )), (15, int( time() - 4000 )), (13, int( time() - 2000 )), (27, int( time() - 500 )) ]
                ]

    results = [ [10, 13.75, 20], [10, 10, 10], [-1, -1, -1], [10, 30, 50], [-1, -1, -1], [20, 20, 20], [0, 0, 0], [13, 17.57, 27] ]

    for mylist, result in zip( mylists, results ):
        print 'Tested list:',mylist
        print '[min] Should be:', result[0], 'is', min_price( mylist )
        print '[avg] Should be:', result[1], 'is', avg_price( mylist )
        print '[max] Should be:', result[2], 'is', max_price( mylist )
        print '-------------------------------------------------'
