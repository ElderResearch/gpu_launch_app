#!/usr/bin/env python3

import grp
from datetime import datetime

from flask_login import UserMixin
from notebook.auth.security import passwd, passwd_check

from app import db, login


class ActivityLog(db.Model):
    id = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    image_type = db.Column(db.String(8))
    num_gpus = db.Column(db.Integer)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    stop_time = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return "<ActivityLog {}".format(self.id)

    def stop(self):
        self.stop_time = datetime.utcnow()

    @property
    def uptime(self):
        """Return a the uptime of the container in seconds"""
        if self.stop_time is None:
            self.stop()
        return round((self.stop_time - self.start_time).total_seconds())

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {
            "id": self.id,
            "username": self.user.username,
            "image_type": self.image_type,
            "num_gpus": self.num_gpus,
            "uptime": self.uptime,
            "start_time": self.start_time.isoformat(timespec="seconds"),
            "stop_time": self.stop_time.isoformat(timespec="seconds"),
        }


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    containers = db.relationship("ActivityLog", backref="user", lazy="dynamic")

    def __repr__(self):
        return "User <{}>".format(self.username)

    def is_admin(self):
        return self.username in grp.getgrnam("admin").gr_mem

    def set_password_hash(self, password):
        self.password_hash = passwd(password)

    def check_password(self, password):
        return passwd_check(self.password_hash, password)

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {
            "id": self.id,
            "username": self.username,
            "last_seen": self.last_seen.isoformat(),
            "containers": [c.serialize for c in self.containers],
        }


@login.user_loader
def user_loader(id):
    return User.query.get(int(id))
