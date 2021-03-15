from BettingGameApp import db
from BettingGameApp import w3
from BettingGameApp import bcrypt
from BettingGameApp.models.models import User


def create_eth_account(password):
    _account = w3.eth.account.create()
    address = _account.address
    keystore = _account.encrypt(password)
    return address, keystore

def register_user(form):
    _hashed_pw = bcrypt.generate_password_hash(form.password.data)

    _address, _keystore = create_eth_account(form.password.data)
    user = User(
        username=form.username.data,
        email=form.email.data,
        password=_hashed_pw,
    )
    db.session.add(user)
    db.session.commit()

    return user