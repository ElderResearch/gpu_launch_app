#!/usr/bin/python3

import os

from flask import Flask
from flask.cli import load_dotenv
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

import config

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()


def create_app():
    load_dotenv()
    server = Flask(__name__)
    if os.getenv("FLASK_ENV") == "development":
        server.config.from_object(config.DevelopmentConfig)
    elif os.getenv("FLASK_ENV") == "production":
        server.config.from_object(config.ProductionConfig)
    else:
        raise ValueError("FLASK_ENV environment variable not set")

    register_extensions(server)
    register_blueprints(server)

    return server


def register_extensions(server):
    from app.helpers import generate_usage_log_data

    db.init_app(server)
    with server.app_context():
        if os.getenv("FLASK_ENV") == "development" and "DATABASE_URL" not in os.environ:
            db.create_all()
            rows = generate_usage_log_data(n=100)
            db.session.add_all(rows)
            try:
                db.session.commit()
            except Exception as e:
                server.logger.error(str(e))
                db.session.rollback()
    migrate.init_app(
        server, db, directory=os.path.join(os.path.dirname(__file__), "migrations")
    )
    login.init_app(server)
    login.login_view = "auth.login"
    login.login_message = ""


def register_blueprints(server):
    from app.auth import bp as auth_bp
    from app.dashboard import bp as dash_bp
    from app.main import bp as main_bp

    server.register_blueprint(auth_bp, url_prefix="/auth")
    server.register_blueprint(dash_bp, url_prefix="/dashboard")
    server.register_blueprint(main_bp)
