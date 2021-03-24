import os
from flask import Flask, Blueprint
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_restful import Api
# from flask_jwt import JWT
from web3 import Web3

from BettingGameApp.config import Config

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'warning'

# Web3
NODE_URL = ''
w3 = ''


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)
    api = Api(app)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    @app.before_first_request
    def create_tables():
        db.create_all()

    # api blueprints
    from BettingGameApp.resources.users import user_api

    app.register_blueprint(user_api)


    from BettingGameApp.users.routes import users
    from BettingGameApp.main.routes import main
    # route blueprints
    app.register_blueprint(users)
    app.register_blueprint(main)


    from BettingGameApp.resources.users import Login

    api.add_resource(Login, '/api/login')

    return app
