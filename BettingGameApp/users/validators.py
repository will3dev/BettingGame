import re
from wtforms.validators import ValidationError

from BettingGameApp.models.models import User


def validate_email(form, email_inpt):
    message = "Must be a valid email format"

    email_re = re.compile(r'\w+@\w+\.[a-zA-Z]{2,3}')
    check = email_re.match(email_inpt.data)
    if check:
        return True

    raise ValidationError(message)


def validate_password(form, password_inpt):
    # password requirements:
    # at least 10 characters
    # at least 1 lower, 1 upper, and 1 number
    # must contain special character: @#!%&
    message = "Your password did not meet minimum requirements."

    _length = len(password_inpt.data) >= 10
    _lower = re.search(r'[a-z]+', password_inpt.data)
    _upper = re.search(r'[A-Z]+', password_inpt.data)
    _number = re.search(r'[0-9]', password_inpt.data)
    _special = re.search(r'[@#!&%]', password_inpt.data)
    if _length and _lower and _upper and _number and _special:
        return True

    raise ValidationError(message)


def validate_username(form, username):
    message = "Username already exists. Pick another."

    user = User.query.filter_by(username=username.data).first()

    if user:
        raise ValidationError(message)





