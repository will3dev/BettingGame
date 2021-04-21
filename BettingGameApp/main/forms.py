from BettingGameApp.w3.BettingGameContract import BettingGameContract

from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import (StringField, SubmitField, IntegerField, FloatField)
from wtforms.validators import DataRequired, InputRequired, ValidationError
from BettingGameApp.w3.Connection import Rinkeby_Connection

w3 = Rinkeby_Connection.w3
bgc = BettingGameContract().contract()


def is_valid_gameID(form, field):
    message = 'This is not a valid Game ID'

    current_game_count = bgc.functions.numberOfGames().call()
    if int(field.data) <= int(current_game_count):
        return True

    else:
        raise ValidationError(message)


def has_available_bal(form, field):
    message = 'There are insufficient funds to support transaction.'

    account = current_user.account_address
    current_account_bal = w3.eth.get_balance(account)
    bet_amount_wei = w3.toWei(field.data, 'ether')

    if bet_amount_wei < current_account_bal:
        return True

    else:
        raise ValidationError(message)


class BetForm(FlaskForm):
    message = "Data input required"

    game_id = IntegerField('Game ID', validators=[
        InputRequired(message), is_valid_gameID
    ])

    prediction = IntegerField('Prediction', validators=[
        InputRequired(message),
    ])

    bet_amount = FloatField('Bet Amount', validators=[
        InputRequired(message), has_available_bal
    ])




