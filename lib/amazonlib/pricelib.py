#!/usr/bin/python2.7 -u
# -*- coding: utf-8 -*-

from time import time

def min_price( price_list ):
    tmp_list = sorted( price for price, time in price_list )

    for price in tmp_list:
        if price != 'N/A':
            return price
    else:
        return -1



def avg_price( price_list ):
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
            return round( avg / float( div_time ), 2 )
        else:
            return -1

    except ZeroDivisionError:
        return -1


def max_price( price_list ):
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
                ]

    results = [ [10, 13.75, 20], [10, 10, 10], [-1, -1, -1] ]

    for mylist, result in zip( mylists, results ):
        print 'Tested list:',mylist
        print '[min] Should be:', result[0], 'is', min_price( mylist )
        print '[avg] Should be:', result[1], 'is', avg_price( mylist )
        print '[max] Should be:', result[2], 'is', max_price( mylist )
        print '-------------------------------------------------'
