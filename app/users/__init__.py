from flask import Blueprint

bp = Blueprint("users", __name__)

from app.users import routes  # noqa: E402, F401
