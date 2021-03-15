from flask import (Blueprint, render_template, redirect,
                   url_for, flash)
from flask_login import current_user, login_user, logout_user
from BettingGameApp import bcrypt
from BettingGameApp.users.forms import LoginForm, RegisterForm
from BettingGameApp.users.utils import register_user
from BettingGameApp.models.models import User


users = Blueprint('users', __name__)


@users.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = LoginForm
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            # ACTIVITY LOG
            login_user(user)
            flash(f'Welcome back, {user.username}', 'success')
            return redirect(url_for('main.home'))

        else:
            flash(f'Unsuccessful login attempt.', 'warning')
    return render_template("login.html")


@users.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = register_user(form)

        if user:
            # ACTIVITY LOG
            flash("You have been successfully registered", "success")
            return redirect(url_for(users.login))

        else:
            flash("Something went wrong, please try again.", "warning")

    return render_template('register.html')



