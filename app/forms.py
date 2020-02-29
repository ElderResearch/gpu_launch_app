#!/usr/bin/env python3

from wtforms import BooleanField, Form, PasswordField, StringField
from wtforms.validators import DataRequired


class LoginForm(Form):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
