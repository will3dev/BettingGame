from BettingGameApp import db, login_manager
from flask_login import UserMixin
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return UserWarning.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    register_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, niullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Integer, nullable=False, default=1)
    account_address = db.Column(db.String(60), nullable=False )
    keystore = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<USER: {self.id}, {self.username}, {self.register_date}, {'admin' if self.is_admin else 'not admin'}>"

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_type = db.Column(db.Integer, nullable=False)
    log_datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    is_success = db.Column(db.Integer, unique=False, nullable=False)
    channel = db.Column(db.String(30), nullable=False) # either api or web

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity = db.relationship('User',
                               backref=db.backref('activity_log', lazy=True))