import os
import json
from BettingGameApp.w3.Connection import Rinkeby_Connection

w3 = Rinkeby_Connection.w3

class BettingGameContract:
    def __init__(self):
        self.contract_address = '0x6d7580066166B9dB7E5971BC7774246fD9854BA9'
        self.contract_path = os.path.join(os.getcwd(), 'Contract', 'BettingGameContract')

    def load_contract_json(self):
        with open(self.contract_path, 'r') as c:
            data = c.read()
        return json.loads(data)

    def contract(self):
        contract_json = self.load_contract_json()
        return w3.eth.contract(
            address=self.contract_address,
            abi=contract_json['abi']
        )