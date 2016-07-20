# -*- coding: utf-8 -*-
import os

SERVER = 'Xian/201607'
DEV_PORT = 3000

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
SITE_ROOT = '/siteroot'  # Nb. you cant name this folder 'site' or _mysql is not detected

DB_HOST = os.environ.get('DB_HOST')
DB_USER = os.environ.get('DB_USER')
DB_PSWD = os.environ.get('DB_PSWD')
DB_NAME = os.environ.get('DB_NAME')

MC_HOST = '127.0.0.1'
