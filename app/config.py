#!/usr/bin/env python3

import os

basedir = os.path.abspath(os.path.dirname(__file__))

class BaseConfig:
    SECRET_KEY = \
    '\xc8d\x19E}\xa5g\xbbC\xbd\xe2\x17\x83\xfa!>\xead\x07p\xbd\x92\xce\x85'
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
