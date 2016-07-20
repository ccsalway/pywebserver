# -*- coding: utf-8 -*-
from base64 import b64decode


def get_basic_auth(header):
    if not header: return False
    _, encoded = header.split(None, 1)
    decoded = b64decode(encoded)
    if ':' not in decoded: return False
    return decoded.split(':', 1)  # username, password
