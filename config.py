#!/usr/bin/env python3

import os

basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    SECRET_KEY = "change-this-super-secret-key"
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    if "DATABASE_URL" in os.environ:
        SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")


class ProductionConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
