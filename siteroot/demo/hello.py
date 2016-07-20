# -*- coding: utf-8 -*-
from modules.httpcore import HttpRequest, HttpException


class Hello(HttpRequest):
    """looking for REQUEST_METHOD (get, post, put, ...)"""
    def get(self, request, response):
        return "Hello, Person!"
