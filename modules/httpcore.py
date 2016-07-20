# -*- coding: utf-8 -*-


class HttpRequest(object):
    def __init__(self, conn=None):
        self.conn = conn

    def __call__(self, request, response):
        mname = request.headers.get('REQUEST_METHOD', '').lower()
        if not mname or not hasattr(self, mname):
            raise HttpException(405)  # Method Not Allowed
        method = getattr(self, mname)
        return method(request, response)


class HttpException(Exception):
    """captures all 4xx, 5xx HTTP exceptions"""
    def __init__(self, code, message=''):
        super(HttpException, self).__init__(message)
        self.code = code
