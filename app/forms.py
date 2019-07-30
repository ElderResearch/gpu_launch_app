#!/usr/bin/env python3

from wtforms import (Form, StringField, PasswordField, BooleanField)
from wtforms.validators import DataRequired

class LoginForm(Form):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
