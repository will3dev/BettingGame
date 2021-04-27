import os

from flask import (flash, render_template, redirect, url_for, Blueprint)
from flask_login import current_user, login_required

from BettingGameApp.main.forms import BetForm
from BettingGameApp.main.utils import GameDetails, BetData, Bet
from eth_account import Account

main = Blueprint('main', __name__)


@main.route('/')
@main.route('/home')
@login_required
def home():
    gd = GameDetails()
    gd.get_all_games()
    all_games = gd.all_games
    return render_template("home.html", game_data=all_games)


@main.route('/place_bet/<int:game_id>', methods=['GET', 'POST'])
@login_required
def place_bet(game_id):
    form = BetForm(game_id=game_id)

    game_data = GameDetails().get_single_game(game_id)

    bd = BetData(game_id)
    bd.get_bet_data(limit_data=True)

    if form.validate_on_submit():
        # key = Account.decrypt(current_user.keystore, os.environ.get('TEST_PASSWORD'))
        account = Account.from_key(current_user.keystore)
        bet = Bet(game_id=form.game_id.data, prediction=form.prediction.data, bet_amount=form.bet_amount.data)
        bet.place_bet(account)

        if bet.success:
            data = bet.get_event_details()
            message = f"Bet placed: GAME_ID {data['game_id']}; BET MAKER {data['betMaker']}; BET AMOUNT {data['betAmount']}"
            flash(message, 'success')

        elif not bet.success:
            message = f"BET FAILURE: {bet.error_message}"
            flash(message, 'warning')

        else:
            message = "Something went wrong."
            flash(message, 'danger')

    return render_template("place_bet.html", form=form, bet_data=bd.bet_data, game_data=game_data)


