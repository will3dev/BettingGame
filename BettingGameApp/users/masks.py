import requests

from BettingGameApp.resources.users import Login

def login_user():
    resp = requests.get('http://127.0.0.1:5000/api/login')

    if resp.status_code != 200:
        return "There was an error"

    data = resp.json()
    return data['message']