import os

from dotenv import load_dotenv
load_dotenv()

from web3 import Web3

class Rinkeby_Connection:
    rinkeby = os.environ.get('NODE_URL')
    w3 = Web3(Web3.HTTPProvider(rinkeby))