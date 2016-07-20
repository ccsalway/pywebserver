# -*- coding, utf-8 -*-

"""
** Regular expression matching **

SITES = [
    ['.*\.example\.com', [
        ['/static', '__STATIC__'],  # static files
        ['/', ('index', 'Index')],
        ['/user', [
            ['/home', ('user.home', 'Render')],  # path to file (/siteroot/user/home.py) , class Name (class Render(HttpRequest))
            ['/inbox', ('user.inbox', 'Messages')],
        ]]
    ]],
    ['api\.example2\.com', [
        ['/static', '__STATIC__'],  # static files
        ['/', ('index', 'Index')],
    ]]
]
"""


SITES = [
    ['.*', [
        ['/static', '__STATIC__'],
        ['/', ('index', 'Index')],
        ['/demo', ('demo.hello', 'Hello')],
    ]],
]
