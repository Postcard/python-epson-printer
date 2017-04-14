import math


def to_hex(arr):
    """ convert a decimal array to an hexadecimal String"""
    return ''.join(chr(b) for b in arr)


def byte_to_bits(b):

    assert b <= 255

    r = b

    bits = {}

    for i in range(0, 8):
        a = math.pow(2, 7 - i)
        bits[7 - i] = int(r // a)
        r = r % a

    return bits