#!/usr/bin/python2.7 -u
# -*- coding: utf-8 -*-

from time import time

def min_price( price_list ):
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
            return round( avg / div_time, 2 )
        else:
            return -1

    except ZeroDivisionError:
        return -1


def max_price( price_list ):
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
