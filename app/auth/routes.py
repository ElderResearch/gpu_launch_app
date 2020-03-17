import pam
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from werkzeug.urls import url_parse

from app import db, FLASH_CLS
from app.auth import bp
from app.auth.forms import LoginForm
from app.models import User


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginForm(request.form)
    if request.method == "POST":
        if form.validate():
            user = User.query.filter_by(username=form.username.data).first()
            if user is None:
                if pam.authenticate(form.username.data, form.password.data):
                    try:
                        user = User(username=form.username.data)
                        user.set_password_hash(form.password.data)
                        db.session.add(user)
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
                        flash(
                            message=(
                                "Error adding user to database. "
                                "Contact an admin for assistance."
                            ),
                            category=FLASH_CLS["error"],
                        )
                        return redirect(url_for("auth.login"))
                else:
                    flash(
                        message="Invalid username or password",
                        category=FLASH_CLS["error"],
                    )
                    return redirect(url_for("auth.login"))
            if not user.check_password(form.password.data):
                flash(
                    message="Invalid username or password", category=FLASH_CLS["error"]
                )
                return redirect(url_for("auth.login"))
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get("next")
            if not next_page or url_parse(next_page).netloc != "":
                next_page = url_for("main.index")
            return redirect(next_page)
        else:
            flash(message="All fields required.", category=FLASH_CLS["error"])
    return render_template("auth/login.html", form=form)


@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
