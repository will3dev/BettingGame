import json

from hexbytes import HexBytes

from BettingGameApp import db
from BettingGameApp import bcrypt
from BettingGameApp.models.models import User
from flask_login import login_user, logout_user

from web3.auto.infura import w3
from eth_account import Account


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
        account_address=_address,
        keystore=json.dumps(_keystore),
    )
    db.session.add(user)
    db.session.commit()

    return user

def login_user_decrypt(user, password):
    login_user(user) # log the user in

    keystore_encrypted = json.loads(user.keystore)
    private_key = Account.decrypt(keystore_encrypted, password)

    user.keystore = private_key
    user.secret = password
    db.session.commit()


def logout_user_encrypt(user):
    keystore_encrypted = Account.encrypt(user.keystore, user.secret)

    user.keystore = json.dumps(keystore_encrypted)
    user.secret = ''
    db.session.commit()

    logout_user()


def convert_hex_string(hex_string):
    return bytes.fromhex(hex_string)
