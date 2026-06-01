from database.db import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id       = db.Column(db.Integer,     primary_key=True)
    username = db.Column(db.String(80),  unique=True, nullable=False)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role     = db.Column(db.String(20),  default="viewer")


class PingLog(db.Model):
    __tablename__ = "ping_logs"

    id            = db.Column(db.Integer,     primary_key=True)
    device_name   = db.Column(db.String(100), nullable=False)
    ip            = db.Column(db.String(50),  nullable=False)
    status        = db.Column(db.String(10),  nullable=False)   # ONLINE / OFFLINE
    response_time = db.Column(db.Integer,     nullable=True)    # ms, null if offline
    timestamp     = db.Column(db.String(30),  nullable=False)