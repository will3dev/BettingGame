from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SubmitField, FloatField)
from wtforms.validators import DataRequired, EqualTo, InputRequired
from BettingGameApp.users.validators import validate_email, validate_password, validate_username

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(), validate_email
    ])

    password = PasswordField('Password', validators=[
        DataRequired()
    ])

    login = SubmitField('Login')


class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(), validate_email
    ])
    username = StringField('Username', validators=[
        DataRequired(), validate_username
    ])
    password = PasswordField('Password', validators=[
        EqualTo('password', message='Passwords must match'),
        validate_password
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        InputRequired()
    ])
