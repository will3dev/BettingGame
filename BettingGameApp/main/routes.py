
from flask import (flash, render_template, redirect, url_for, Blueprint)
from flask_login import current_user, login_required

main = Blueprint('main', __name__)


@main.route('/')
@main.route('/home')
@login_required
def home():
    return render_template("home.html")