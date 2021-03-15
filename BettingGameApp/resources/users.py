from flask_restful import Resource, reqparse
from flask import Blueprint


user_api = Blueprint('user_api', __name__)


class Login(Resource):
    def get(self):
        return {"message": "Success!"}, 200