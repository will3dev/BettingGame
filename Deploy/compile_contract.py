import json
import os

from solcx import compile_source

contract_path = os.path.join(os.getcwd(),'Contract', 'BettingGame_v2.sol')

with open(contract_path, 'r') as c:
    read_contract = c.read()

compiled_contract = compile_source(read_contract)

new_contract_path = os.path.join(os.getcwd(), 'Contract', 'BettingGameContract')

with open(new_contract_path, 'w') as nc:
    json.dump(compiled_contract['<stdin>:BettingGame'], nc)