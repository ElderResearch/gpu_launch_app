#!/usr/bin/python3

from flask import Flask
from .config import BaseConfig

def create_app():
	server = Flask(__name__)
	server.config.from_object(BaseConfig)

	register_extensions(server)
	register_blueprints(server)

	return server

def register_extensions(server):
	from .extensions import db
	from .extensions import migrate

	db.init_app(server)
	migrate.init_app(server, db)

def register_blueprints(server):
	from .views.home import home

	server.register_blueprint(home)


if __name__ == "__main__":
	app.run()
