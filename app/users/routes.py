from flask import render_template, request, flash, redirect, url_for

from app import FLASH_CLS
from app.models import User
from app.users import bp


@bp.route("/", methods=["GET"])
def all_users():
    users = User.query.order_by(User.username).all()
    return render_template("users/all_users.html", users=users)


@bp.route("/<username>", methods=["GET"])
def user_page(username=None):
    if username is None:
        flash(message="username has not been defined.", category=FLASH_CLS["error"])
        redirect(url_for("users.all_users"))

    user = User.query.filter_by(username=request.args.get("username")).first_or_404()
    pass
