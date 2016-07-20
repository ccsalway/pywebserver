# -*- coding: utf-8 -*-
import logging
import pylibmc
from Queue import Queue


class Cache(object):
    _conn = None

    def __init__(self, host):
        self.host = host
        self.connect()

    def connect(self):
        logging.info("Connecting to memcache %s" % self.host)
        self._conn = pylibmc.Client([self.host], binary=True, behaviors={"tcp_nodelay": True})

    def get(self, key):
        self._conn.get(key) # returns None otherwise

    def add(self, key, data, expires=0):
        # adds key if doesnt exist
        self._conn.add(key, data, expires)

    def replace(self, key, data, expires=0):
        # replaces key if exists
        self._conn.replace(key, data, expires)

    def set(self, key, data, expires=0):
        # adds or replaces key
        self._conn.set(key, data, expires)

    def extend(self, key, time):
        # extends the expiry time of a key
        self._conn.touch(key, time)

    def delete(self, key):
        self._conn.delete(key)


class CacheConnectionPool(object):
    conn_pool = Queue()
    pool_size = 5

    def get_connection(self):
        try:
            return self.conn_pool.get()
        except Exception:  # pool empty
            return Cache(self.host)

    def put_connection(self, conn):
        self.conn_pool.put(conn)

    def initialize(self):
        for i in xrange(self.pool_size):
            conn = Cache(self.host)
            self.conn_pool.put_nowait(conn)

    def __init__(self, host):
        self.host = host
        self.initialize()
