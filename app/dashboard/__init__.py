from flask import Blueprint

bp = Blueprint("dashboard", __name__, static_folder="static")

from app.dashboard import routes  # noqa: E402, F401
