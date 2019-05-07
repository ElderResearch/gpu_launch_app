#!/usr/bin/python3

import os
import dash
import dash_bootstrap_components as dbc
from flask import Flask
from flask.cli import load_dotenv
from flask.helpers import get_root_path
from . import config

def create_app():
    load_dotenv()
    server = Flask(__name__)
    if os.getenv("FLASK_ENV") == 'development':
        server.config.from_object(config.DevelopmentConfig)
    elif os.getenv("FLASK_ENV") == 'production':
        server.config.from_object(config.ProductionConfig)
    else:
        raise ValueError('FLASK_ENV environment variable not set')

    register_dashapps(server)
    register_extensions(server)
    register_blueprints(server)

    return server

def register_dashapps(server):
    from .views.usage.layout import layout
    from .views.usage.callbacks import register_callbacks

    # Meta tags for viewport responsiveness
    meta_viewport = {
		"name": "viewport",
		"content": "width=device-width, initial-scale=1, shrink-to-fit=no"
	}
    external_stylesheets = [
        {
            "rel": "stylesheet",
            "href": "https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css",
            "integrity": "sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T",
            "crossorigin": "anonymous"
        },
        {
            "rel": "stylesheet",
            "href": "https://codepen.io/semperstew/pen/gJpMQN.css",
            "crossorigin": "anonymous"
        }
    ]
    usageapp = dash.Dash(__name__,
                         server=server,
                         url_base_pathname='/usage/',
                         external_stylesheets=external_stylesheets,
                         meta_tags=[meta_viewport])

    usageapp.title = 'Usage Dashboard'
    usageapp.layout = layout
    register_callbacks(usageapp)

def register_extensions(server):
    from .extensions import db
    from .extensions import migrate
    from .helpers import generate_usage_log_data
    from .models import ActivityLog
    db.init_app(server)
    with server.app_context():
        db.create_all()
        if os.getenv('FLASK_ENV') == 'development':
            rows = generate_usage_log_data(ActivityLog)
            db.session.add_all(rows)
            try:
                db.session.commit()
            except:
                db.session.rollback()
    migrate.init_app(server, db)

def register_blueprints(server):
    from .views.home import home

    server.register_blueprint(home)
