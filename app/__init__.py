#!/usr/bin/python3

import dash
import dash_bootstrap_components as dbc
from flask import Flask
from flask.helpers import get_root_path
from .config import BaseConfig

def create_app():
	server = Flask(__name__)
	server.config.from_object(BaseConfig)

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

    usageapp = dash.Dash(__name__,
                         server=server,
                         url_base_pathname='/usage/',
                         external_stylesheets=[dbc.themes.BOOTSTRAP],
                         meta_tags=[meta_viewport])

    usageapp.title = 'Usage Dashboard'
    usageapp.layout = layout
    register_callbacks(usageapp)

def register_extensions(server):
	from .extensions import db
	from .extensions import migrate

	db.init_app(server)
	migrate.init_app(server, db)

def register_blueprints(server):
	from .views.home import home

	server.register_blueprint(home)

