from flask import render_template, request, flash, redirect, url_for

from app import FLASH_CLS
from app.models import User
from app.users import bp


@bp.route("/", methods=["GET"])
def all_users():
    users = User.query.order_by(User.username).all()
    return render_template("users/all_users.html", users=users)


