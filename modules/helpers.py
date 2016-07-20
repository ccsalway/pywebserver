# -*- coding: utf-8 -*-
import binascii, os
from datetime import datetime


def generate_uid(size=32):
    """ Generates a random alphanumeric string of [size] """
    return binascii.hexlify(os.urandom(size/2))


def get_first(obj, default=None):
    """ returns first element in a list or default """
    return obj[0] if obj else default


class DateTime(object):
    @classmethod
    def rfc1123(cls, dt=None):
        """Sun, 27 Mar 2016 20:54:59 GMT"""
        if not dt: dt = datetime.utcnow()
        return dt.strftime('%a, %d %b %Y %H:%M:%S GMT')

    @classmethod
    def iso8601(cls, dt=None):
        """2016-03-27T20:54:59.087738Z"""
        if not dt: dt = datetime.utcnow()
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    @classmethod
    def sql(cls, dt=None):
        """2016-03-27 20:54:59"""
        if not dt: dt = datetime.utcnow()
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    @classmethod
    def date(cls, dt=None):
        """2016-03-27"""
        if not dt: dt = datetime.utcnow()
        return dt.strftime('%Y-%m-%d')

    @classmethod
    def unixtime(cls, dt=None):
        """1469016094"""
        if not dt: dt = datetime.utcnow()
        return dt.strftime("%s")


def str_to_unicode(s):
    try:
        return unicode(s, encoding='utf-8')
    except:
        return s


def unicode_to_str(s):
    try:
        return s.encode('utf-8')
    except:
        return s
