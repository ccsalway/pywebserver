# -*- coding: utf-8 -*-
import logging
import re
import sys
from time import time
from datetime import datetime
from hashlib import sha1
from urllib import unquote_plus
from config import *
from mappings import *
from modules.httpcore import HttpException
from modules.mysql import MySql, NoConnection

logging.basicConfig(format="%(threadName)-18s %(asctime)s %(levelname)s %(message)s", level=logging.DEBUG)


class Application(object):
    _status_codes = {
        200: 'OK',
        302: 'Found',
        304: 'Not Modified',
        400: 'Bad Request',
        401: 'Unauthorised',
        404: 'Not Found',
        405: 'Method Not Allowed',
        500: 'Server Error'
    }
    _mime_types = {
        'js': 'application/javascript',
        'css': 'text/css',
        'jpeg': 'image/jpeg',
        'jpg': 'image/jpeg',
        'gif': 'image/gif',
        'png': 'image/png',
        'ico': 'image/vnd.microsoft.icon',
        'txt': 'text/plain',
        'csv': 'text/csv',
        'json': 'application/json',
        'pdf': 'application/pdf',
    }

    class Request(): pass
    class Response(): pass

    def reset(self):
        for k in self.Request.__dict__.copy():
            del self.Request.__dict__[k]
        for k in self.Response.__dict__.copy():
            del self.Response.__dict__[k]

    def str2httpdate(self, s):
        """converts a string into an acceptable http date"""
        fmts = [
            '%a, %d %b %Y %H:%M:%S GMT',  # Sun, 06 Nov 1994 08:49:37 GMT   ; RFC 822, updated by RFC 1123
            '%A, %d-%b-%y %H:%M:%S GMT',  # Sunday, 06-Nov-94 08:49:37 GMT  ; RFC 850, obsoleted by RFC 1036
            '%a %b %d %H:%M:%S %Y',       # Sun Nov  6 08:49:37 1994        ; ANSI C's asctime() format
        ]
        for f in fmts:
            try:
                return datetime.strptime(s, f)
            except:
                pass
        raise ValueError("'badly formatted datetime' does not match any HTTP-Date format")

    def str_to_unicode(self, s):
        try:
            return unicode(s, encoding='utf-8')
        except UnicodeError:
            return s

    def parse_data(self, data, separator):
        d = {}
        if not data: return d
        for kv in data.split(separator):
            if '=' not in kv: continue  # malformed
            k, v = kv.split('=', 1)
            k = k.strip().lower()
            # do not strip v in case the value has a space such as a password might 'password$1 '
            v = unquote_plus(v)
            # remove empty values so it makes it easier to check if a value has been passed in, ie. 'raise KeyError'
            if not v.strip(): continue
            d.setdefault(k, []).append(self.str_to_unicode(v))
        return d

    def real_addr(self, env):
        if 'HTTP_X_FORWARDED_FOR' in env:
            # client, proxy1, proxy2
            return env['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()
        elif 'HTTP_FORWARDED' in env:
            # for=192.0.2.60, for="[2001:db8:cafe::17]:4711"; proto=http; by=203.0.113.43
            for a in env['HTTP_FORWARDED'].split(';'):
                if a.strip().lower().find('for') == 0:
                    d = a.split(',')[0].strip()
                    if '=' not in d: break  # health check
                    _, ip = d.split('=')
                    return ip.strip('" ')
        return env['REMOTE_ADDR']

    def get_handler(self, env):
        http_host = env.get('HTTP_HOST', '').split(':')[0]  # host:port
        if not http_host: raise HttpException(404, "Empty Site")
        path_info = env.get('PATH_INFO').rstrip('/') + '/'
        if not path_info: raise HttpException(404, "Empty Path")
        # get site paths
        paths = None
        for site in SITES:
            if not re.match(site[0] + '$', http_host, re.I): continue
            paths = site[1]
            break
        if not paths: raise HttpException(404, "Unknown Site")
        # get path handler
        parts = path_info.split('/')[1:]  # first is blank
        while len(parts) > 0:
            part = parts.pop(0)
            for path in paths:
                if not re.match(path[0] + '$', '/' + part, re.I): continue
                if isinstance(path[1], tuple) or path[1] == '__STATIC__':
                    return path[1], parts[:-1]  # last is blank
                paths = path[1]
                break
        raise HttpException(404, "Unknown Path")

    def get_headers(self, env):
        h = {'REMOTE_ADDR': self.Request.realaddr}
        for k, v in env.iteritems():
            if k.find('uwsgi') == 0 or k.find('wsgi') == 0: continue
            if k == 'REQUEST_SCHEME':
                if 'HTTP_X_FORWARDED_PROTO' in env:
                    h[k] = env['HTTP_X_FORWARDED_PROTO']
                else:
                    h[k] = v
            else:
                h[k] = v
        return h

    def get_cookies(self, env):
        return self.parse_data(env.get('HTTP_COOKIE'), ';')

    def get_querystring(self, env):
        return self.parse_data(env.get('QUERY_STRING'), '&')

    def get_request_body(self, env):
        content_type = env.get('CONTENT_TYPE', '').lower()
        content_length = env.get('CONTENT_LENGTH', '0')
        if not content_length.isdigit() or int(content_length) <= 0:
            return {}
        data = env['wsgi.input'].read(int(content_length))
        if content_type.find('application/x-www-form-urlencoded') == 0:
            return self.parse_data(data, '&')
        elif content_type.find('multipart/form-data') == 0:
            vals = {}
            m = re.search(r'boundary="?([\da-zA-Z\'()+,-_\./:=? ]{1,70})', env['CONTENT_TYPE'])
            if m is None:
                raise HttpException(400, "Missing or invalid boundary in multipart form")
            boundary = m.group(1).strip()
            for d in data.split('--' + boundary):
                if d == '' or d.find('--') == 0: continue
                d = d.strip('\r\n')
                hdrs, content = d.split('\r\n\r\n', 1)
                headers = {}
                for h in hdrs.split('\r\n'):
                    k, v = h.split(':', 1)
                    k = k.strip().lower()
                    headers[k] = v.strip()
                if 'content-disposition' not in headers:
                    continue
                if headers['content-disposition'].lower().find('form-data') != 0:
                    continue
                keys = {}
                for kv in headers['content-disposition'].split(';'):
                    if '=' not in kv: continue
                    k, v = kv.split('=')
                    k = k.strip().lower()
                    keys[k] = v.strip(' "')
                if 'name' not in keys:
                    continue
                if 'filename' in keys:
                    fn = self.str_to_unicode(keys.get('filename', ''))
                    ct = headers.get('content-type', 'application/octet-stream')
                    vals.setdefault(keys['name'], []).append({'filename': fn, 'mimetype': ct, 'content': content})
                else:
                    vals.setdefault(keys['name'], []).append(self.str_to_unicode(content))
            return vals
        else:
            return data  # such as application/json

    def get_uri(self, env):
        if 'HTTP_X_FORWARDED_PROTO' in env:
            scheme = env['HTTP_X_FORWARDED_PROTO']
        else:
            scheme = env.get('REQUEST_SCHEME', 'http')
        uri = '%s://%s' % (scheme, env['HTTP_HOST'])
        return uri

    def serve_file(self, fn):
        if not os.path.isfile(fn): raise HttpException(404)
        # set content length
        self.Response.headers['Content-Length'] = os.path.getsize(fn)
        # set last modified
        last_modified_timestamp = os.path.getmtime(fn)
        last_modified = datetime.fromtimestamp(last_modified_timestamp)
        self.Response.headers['Last-Modified'] = last_modified.strftime('%a, %d %b %Y %H:%M:%S GMT')
        # generate ETag
        hash = sha1()
        hash.update(str(last_modified_timestamp))
        self.Response.headers['Etag'] = etag = hash.hexdigest()
        # check if etag the same
        if_none_match = self.Request.headers.get('HTTP_IF_NONE_MATCH', '')
        if if_none_match == etag:
            raise HttpException(304)
        # check if client has an up-to-date cached version
        try:
            pragma = self.Request.headers.get('HTTP_PRAGMA', '').lower()
            if_modified_since = self.str2httpdate(self.Request.headers['HTTP_IF_MODIFIED_SINCE'])
            # HTTP/1.0 Pragma: no-cache - always fetches the file
            if pragma != 'no-cache' and last_modified <= if_modified_since:
                raise HttpException(304)
        except (KeyError, ValueError):  # missing header or badly formatted datetime
            pass
        # set content-type
        ext = fn.rsplit('.', 1)[1].lower()
        if ext in ('py', 'pyc'): raise HttpException(404)  # protected files
        content_type = self._mime_types.get(ext, "application/octet-stream")
        if re.match(r'^(text|application/json)', content_type):
            content_type += '; charset=utf-8'
        self.Response.headers['Content-Type'] = content_type
        # set content
        with open(fn, 'r') as f:
            self.Response.content = f.read()

    def dispatch(self, env, handler, conn):
        if handler == '__STATIC__':
            path_info = env.get('PATH_INFO', '')
            fn = "%s%s%s" % (APP_ROOT, SITE_ROOT, path_info)
            self.serve_file(fn)
        else:
            try:
                _file, _class = handler
                name = SITE_ROOT.strip('/') + '.' + _file
                # get module
                if name not in sys.modules:  # reduces overhead if already loaded
                    __import__(name)
                module = sys.modules[name]
                # get class - supports inner classes: Class1.Class1a
                for c in _class.split('.'):
                    module = getattr(module, c)
                result = module(conn)(self.Request, self.Response) or ''
                if isinstance(result, tuple):  # content-type, content
                    self.Response.headers['Content-Type'] = result[0]
                    result = result[1]
                if isinstance(result, unicode):
                    result = result.encode('utf-8')
                self.Response.content = str(result)  # content must be byte str
            except (ImportError, AttributeError), e:
                logging.error("Mapping: %s - %s" % (handler, e.message))
                raise HttpException(500)

    def set_status(self):
        return '%s %s' % (self.Response.status_code, self._status_codes[self.Response.status_code])

    def set_headers(self):
        h = [('Server', SERVER), ('Content-Length', str(len(self.Response.content)))]
        for k, v in self.Response.headers.iteritems():
            if k.lower() in ('server', 'content-length'): continue
            h.append((k, str(v)))
        return h

    def __init__(self, env):
        try:
            # opening a connection each time is slow. for
            # speed, move the conn outside of this class
            # and remove the close from the finally block below
            conn = MySql(DB_HOST, DB_USER, DB_PSWD, DB_NAME)
            try:
                self.reset()
                self.Request.time = time()  # nice to have, not necessary
                self.Request.realaddr = self.real_addr(env)
                self.Response.status_code = 200
                self.Response.headers = {'Content-Type': 'text/plain'}
                self.Response.content = ''
                try:
                    handler, params = self.get_handler(env)
                    self.Request.params = params  # url parameters - /path/file/param1/param2
                    self.Request.headers = self.get_headers(env)
                    self.Request.cookies = self.get_cookies(env)
                    self.Request.query = self.get_querystring(env)
                    self.Request.form = self.get_request_body(env)
                    self.Request.uri = self.get_uri(env)
                    self.dispatch(env, handler, conn)
                except HttpException, e:
                    self.Response.headers['Content-Type'] = 'text/plain'
                    self.Response.status_code = e.code
                    self.Response.content = e.message
                    for k in self.Response.headers.copy():
                        if k.lower() not in ('content-type', 'www-authenticate', 'location', 'set-cookie'):
                            self.Response.headers.pop(k)
                except NoConnection, e:
                    logging.error(e.message)
                    self.Response.status_code = 500
                    self.Response.headers = {'Content-Type': 'text/plain'}
                    self.Response.content = 'Server error. Please contact support.'
                except Exception, e:
                    logging.exception(e)
                    self.Response.status_code = 500
                    self.Response.headers = {'Content-Type': 'text/plain'}
                    self.Response.content = 'Server error. Please contact support.'
            finally:
                conn.close()
        except Exception, e:
            logging.exception(e)
            self.Response.status_code = 500
            self.Response.headers = {'Content-Type': 'text/plain'}
            self.Response.content = 'Server error. Please contact support.'

    def __call__(self, start):
        start(self.set_status(), self.set_headers())
        return [self.Response.content]


def application(env, start):
    return Application(env)(start)


if __name__ == '__main__':
    """ running directly. consider using uwsgi """
    from wsgiref import simple_server

    try:
        httpd = simple_server.make_server('', DEV_PORT, application)
        print "Listening on %s:%s" % httpd.server_address
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
