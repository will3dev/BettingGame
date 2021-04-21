import os
import json

from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

from eth_account import Account
from BettingGameApp import create_app, db
from BettingGameApp.models.models import User

primary_email = os.environ.get('PRIMARY_EMAIL')
rinkeby = os.environ.get('NODE_URL')
r_web3 = Web3(Web3.HTTPProvider(rinkeby))


def compiled_contract():
    contract_path = os.path.join(os.getcwd(), 'Contract', 'BettingGameContract')

    with open(contract_path, 'r') as c:
        data = c.read()
        contract = json.loads(data)

    return contract


def get_account_data():
    # create the app context then query the DB to get the user object
    app = create_app()
    app.app_context().push()

    return User.query.filter_by(email=primary_email).first()



def get_account():
    user = get_account_data()
    decrypted_keystore = json.loads(user.keystore)
    # decrypt the keystore in the user object
    pk = Account.decrypt(
        decrypted_keystore,
        os.environ.get('TEST_PASSWORD')
    ).hex()

    return Account.from_key(pk)


def deploy_contract(compiled_contract):
    account = get_account()

    print(account.privateKey)

    # create contract instance with compile abi and bytecode
    BettingGameContract = r_web3.eth.contract(
        abi=compiled_contract['abi'],
        bytecode=compiled_contract['bin']
    )

    # create contract instance and apply attributes
    transaction = BettingGameContract.constructor(20).buildTransaction({
        'chainId': 4,
        'nonce': r_web3.eth.get_transaction_count(account.address),
        'gasPrice': r_web3.eth.gas_price,
        'gas': 5000000
    })

    # sign transaction
    signed_transaction = account.sign_transaction(transaction)

    # send the transaction
    tx_hash = r_web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    tx_receipt = r_web3.eth.waitForTransactionReceipt(tx_hash)
    print('Contract Address: ', tx_receipt.contractAddress)

    # check to see that the correct manager was created
    BettingGameContractDeployed = r_web3.eth.contract(
        address=tx_receipt.contractAddress,
        abi=compiled_contract['abi']
    )

    print('Manager: ', BettingGameContractDeployed.functions.manager().call())

    return tx_receipt.contractAddress


def create_game(contract_address, compiled_contract):
    account = get_account()

    # create instance of game contract
    BettingGameContract = r_web3.eth.contract(
        address=contract_address,
        abi=compiled_contract['abi']
    )

    # create transaction making new game
    transaction = BettingGameContract.functions.createGame(
        Web3.toWei(.5, 'ether'),
        5
    ).buildTransaction({
        'from': account.address,
        'nonce': r_web3.eth.get_transaction_count(account.address)
    })

    # sign and send the transaction
    signed = account.sign_transaction(transaction)
    tx_hash = r_web3.eth.send_raw_transaction(signed.rawTransaction)
    tx_receipt = r_web3.eth.waitForTransactionReceipt(tx_hash)

    print(tx_receipt)
    return tx_receipt


contract = compiled_contract()
contract_address = deploy_contract(contract)
new_game = create_game(contract_address, contract)

