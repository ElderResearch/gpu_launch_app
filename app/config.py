#!/usr/bin/env python3

import os

basedir = os.path.abspath(os.path.dirname(__file__))

class BaseConfig:
    SECRET_KEY = "change-this-super-secret-key"
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    CACHE_DIR = os.getenv('CACHE_DIR', os.path.join(basedir, "cache"))
    CACHE_DEFAULT_TIMEOUT=60
    CACHE_THRESHOLD=100

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    if 'DATABASE_URL' in os.environ:
        SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')


class ProductionConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
    CACHE_TYPE = 'filesystem'
