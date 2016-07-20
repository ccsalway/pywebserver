# -*- coding: utf-8 -*-
from datetime import datetime
from decimal import Decimal


def json_serialize(data):
    json = []
    if isinstance(data, (list, tuple)):
        for item in data:
            json.append(json_serialize(item))
        return '[' + ','.join(json) + ']'
    elif isinstance(data, dict):
        for item in data:
            key = item.replace('"', '\\"')
            json.append('"%s":%s' % (key, json_serialize(data[item])))
        return '{' + ','.join(json) + '}'
    else:
        if data is None:
            return 'null'
        elif isinstance(data, basestring):
            if isinstance(data, unicode):
                data = data.encode('utf-8')
            return '"' + data.replace('"', '\\"') + '"'
        elif isinstance(data, datetime):
            return '"' + data.strftime('%Y-%m-%dT%H:%M:%SZ') + '"'
        elif isinstance(data, (Decimal, long, float, int)):
            return data


def json_deserialize(data):
    for k, v in data.items():
        if not isinstance(v, basestring): continue
        try:
            data[k] = datetime.strptime(v, '%Y-%m-%dT%H:%M:%SZ')
        except:
            pass
    return data
