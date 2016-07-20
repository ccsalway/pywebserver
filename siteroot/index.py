# -*- coding: utf-8 -*-
from jinja2 import Environment, FileSystemLoader
from modules.httpcore import HttpRequest, HttpException
from models.demo import say_hello
from config import *

j2_env = Environment(loader=FileSystemLoader(TEMPLATES), trim_blocks=True, autoescape=True)


class Index(HttpRequest):
    def get(self, request, response):
        # u = request.uri             - site root path  [string]
        # h = request.headers[key]    - REQUEST HEADERS  [list]
        # p = request.form[key]       - FORM DATA (POST)  [list]
        # g = request.query[key]      - QUERYSTRING DATA (GET)  [list]
        # c = request.cookies[key]    - COOKIES  [list]
        # p = request.params[index]   - URL PARAMS  [list] eg: /path_to_file/param1/param2

        # rows = self.conn.execute(sql, [vals]).fetchall()
        # self.conn.execute(sql, [vals]).commit()

        # response.headers[key] = val   - Case sensitive key name
        # response.status_code = xxx    - HttpStatus code. Default: 200

        # raise HttpException(code, message)    - Overwrites response.status_code. Message is optional.

        # return "application/json", '{"Hello, Person!"}'

        return 'text/html', j2_env.get_template('index.html').render({
            'site': {'title': SITE_TITLE},
            'message': say_hello()
        })
