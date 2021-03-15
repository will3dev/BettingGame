import os
import pytest
import solcx
from solcx import compile_source
from web3 import Web3
from eth_account import Account

solcx.install_solc('0.8.0')

ganache_url = 'HTTP://127.0.0.1:7545'

accounts = [
    '0xc57e8F0B8250A88471572a76BbA37145A7242b47',
    '0xE1C4DF60f70EC1F7f651180f300E1063c278A603',
    '0xf24f095ec60A1Ba2dD31cf75976137034d923505',
    '0x26456BC15734a6acB50dec6efe7a899CBE0d463B',
    '0x9267FbD9D9F6d2328D7b26115a04BA681d7a9DcB',
    '0x1a00B7EA70dBaa84EB57aEE773CB352ca5385CE7',
    '0xa0DeB0463c91B7B2E6a6deAB2a1039Dd550EF9fc',
    '0xf82593e7E61A56e2419F520C9AE161b8E54CC6A4',
    '0xedbecf21aF76a941403bC5A23cF56965617eA150',
    '0xF6CAEBDd2CE6e147b98936Ac78537675580746FA'
]

keys = [
    '2556fa356030df115f9489e0ea2ace95a8ff0c96a0a3ba44897dcee90d0c1c8c',
    'eb267df8a4ad35e85af8235b8163c30701d2084f4cf9231a2110b042ba9a5e54',
    '818ee851b97bb84ad8a3f31e0e60054968b55f5fe92858e7089672d7e83a58ac',
    'b4efb2f9f1da40bc6d4145c7a96af5d5c7bd2ee91a32bdef69d9788f8deb35a6',
    '196460b9016d5e4cce79b67e24df1ac2fe13521edd7e492c346b11ab90ee8144',
    'b2152b65c39a85203eff5b33bac049edbad918040919751aa205ad3260bddad8',
    '7382801f1ccdbf5c9a783431be8ecab1ee14e6b576054bbbab1b256dfb0f277a',
    'cc5da47dc06d3957b4872fa94997ef76ed1784f3b1e1f1ff4e7ae0e93f6296f1',
    '998f238489c3f238986f634cab3436dbff551a595f3cf3b85af45f42fff8b8d9',
    '2835a709433f1190f4270ccc2dc0b9aa9f3dfdbb54c6c1011a55c036995ac5b5'
]

manager = Account().from_key(keys[0])

@pytest.fixture
def tester_provider():
    # return the connection to blockchain
    return Web3.HTTPProvider(ganache_url)


@pytest.fixture
def w3(tester_provider):
    return Web3(tester_provider)


@pytest.fixture
def compiled_contract():
    contract_path = os.path.join(os.getcwd(), '..', 'Contract', 'BettingGame_v2.sol')

    with open(contract_path, 'r') as c:
        source = c.read()

    return compile_source(source, solc_version='0.8.0')


@pytest.fixture
def betting_game_contract(w3, compiled_contract):
    contract = compiled_contract['<stdin>:BettingGameApp']

    # set up the contract details
    BettingGameContract = w3.eth.contract(
        abi=contract['abi'],
        bytecode=contract['bin']
    )

    # deploy the contract using the constructor function
    tx_hash = BettingGameContract.constructor(20).transact({'from': manager.address})

    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

    return BettingGameContract(tx_receipt.contractAddress)


@pytest.fixture
def BettingGame_filter_GameCreated(betting_game_contract):
    return betting_game_contract.events.GameCreated.createFilter(fromBlock='latest')


@pytest.fixture
def BettingGame_filter_BetMade(betting_game_contract):
    return betting_game_contract.events.BetMade.createFilter(fromBlock='latest')


@pytest.fixture
def BettingGame_filter_GameCancelled(betting_game_contract):
    return betting_game_contract.events.GameCancelled.createFilter(fromBlock='latest')


@pytest.fixture
def BettingGame_filter_GameClosed(betting_game_contract):
    return betting_game_contract.events.GameClosed.createFilter(fromBlock='latest')


@pytest.fixture
def BettingGame_filter_GameCompleted(betting_game_contract):
    return betting_game_contract.events.GameCompleted.createFilter(fromBlock='latest')


@pytest.fixture
def BettingGame_filter_BetFeeUpdated(betting_game_contract):
    return betting_game_contract.events.BetFeeUpdated.createFilter(fromBlock='latest')


@pytest.fixture
def create_game(betting_game_contract, w3, BettingGame_filter_GameCreated):
    # get the users set
    user = Account.from_key(keys[0])

    create_game_transaction = betting_game_contract.functions.createGame(2000, 4).buildTransaction({
        'from': user.address,
        'nonce': w3.eth.get_transaction_count(user.address)
    })

    create_game_transaction_signed = user.sign_transaction(create_game_transaction)
    create_game_tx_hash = w3.eth.send_raw_transaction(create_game_transaction_signed.rawTransaction)
    w3.eth.waitForTransactionReceipt(create_game_tx_hash)

    event = BettingGame_filter_GameCreated.get_new_entries()[-1]
    if event.transactionHash == create_game_tx_hash:
        args = event.args
        game_id, game_manager, _ = [args[key] for key in list(args.keys())]

    return [game_id, game_manager]

@pytest.fixture
def place_bets(w3, betting_game_contract, create_game, BettingGame_filter_BetMade):
    game_id, game_manager = create_game
    users = []

    # should place multiple bets
    for x in range(4):
        user = Account().from_key(keys[x])
        users.append(user)
        bet_transaction = betting_game_contract.functions.placeBet(game_id, x).buildTransaction({
            'from': user.address,
            'nonce': w3.eth.get_transaction_count(user.address),
            'value': int(f'{x}000') + 2000
        })
        bet_transaction_signed = user.sign_transaction(bet_transaction)
        bet_tx_hash = w3.eth.send_raw_transaction(bet_transaction_signed.rawTransaction)
        w3.eth.waitForTransactionReceipt(bet_tx_hash)

    # should use the getBetData function to validate
    # that the bet data placed matches what is recorded
    bet_makers, bet_amounts, bet_predictions = betting_game_contract.functions.getBetData(game_id).call()

    return [bet_makers, bet_amounts, bet_predictions]


def test_create_game(w3, betting_game_contract, BettingGame_filter_GameCreated):
    # get the users set
    user = Account.from_key(keys[1])
    prior_game_count = betting_game_contract.functions.getGameCount().call()

    create_game_transaction = betting_game_contract.functions.createGame(2000, 4).buildTransaction({
        'from': user.address,
        'nonce': w3.eth.get_transaction_count(user.address)
    })

    create_game_transaction_signed = user.sign_transaction(create_game_transaction)
    create_game_tx_hash = w3.eth.send_raw_transaction(create_game_transaction_signed.rawTransaction)
    w3.eth.waitForTransactionReceipt(create_game_tx_hash)

    new_game_count = betting_game_contract.functions.getGameCount().call()

    assert prior_game_count < new_game_count

    event = BettingGame_filter_GameCreated.get_new_entries()[-1]
    if event.transactionHash == create_game_tx_hash:
        args = event.args
        game_id, game_manager, create_time_utc = [args[key] for key in list(args.keys())]

    _, _, _create_time_utc, _, _, _, _, _ = betting_game_contract.functions.getLimitedGameData(game_id).call()

    assert create_time_utc == _create_time_utc


def test_create_game_failure_maxRange(w3, betting_game_contract):
    # try to create a game, but the max number is <=1;
    # game should error out

    user = Account().from_key(keys[2])

    try:
        create_game_transaction = betting_game_contract.functions.createGame(1000, 1).buildTransaction({
            'from': user.address,
            'nonce': w3.eth.get_transaction_count(user.address)
        })

        create_game_transaction_signed = user.sign_transaction(create_game_transaction)
        create_game_tx_hash = w3.eth.send_raw_transaction(create_game_transaction_signed.rawTransaction)
        w3.eth.waitForTransactionReceipt(create_game_tx_hash)

        # if we get to this point in our code it means that
        # we did not get our expected result
        assert False

    except:
        # if the above fail it means that it passed our test
        assert True



def test_place_bet(betting_game_contract, w3, create_game, BettingGame_filter_BetMade):
    game_id, game_manager = create_game
    users = []

    # should place multiple bets
    for x in range(4):
        user = Account().from_key(keys[x])
        users.append(user)
        bet_transaction = betting_game_contract.functions.placeBet(game_id, x).buildTransaction({
            'from': user.address,
            'nonce': w3.eth.get_transaction_count(user.address),
            'value': int(f'{x}000') + 2000
        })
        bet_transaction_signed = user.sign_transaction(bet_transaction)
        bet_tx_hash = w3.eth.send_raw_transaction(bet_transaction_signed.rawTransaction)
        w3.eth.waitForTransactionReceipt(bet_tx_hash)

    # check to see if the event data was emitted to correctly
    events = BettingGame_filter_BetMade.get_new_entries()
    senders = list()
    for x in range(4):
        args = events[x].args
        _, sender, _ = [args[key] for key in list(args.keys())]
        senders.append(sender)

    for x in range(4):
        if users[x].address not in senders:
            assert False

    # should use the getBetData function to validate
    # that the bet data placed matches what is recorded
    bet_makers, bet_amounts, bet_predictions = betting_game_contract.functions.getBetData(game_id).call()
    for x in range(4):
        assert bet_makers[x] == users[x].address
        assert bet_amounts[x] == (int(f'{x}000') + 2000)
        assert bet_predictions[x] == x


def test_complete_game(betting_game_contract, w3, create_game, place_bets, BettingGame_filter_GameCompleted):
    game_id, game_manager = create_game
    bet_makers, bet_amounts, _ = place_bets

    user = Account().from_key(keys[0])
    _, status, _, _, _betFee, _, _, _ = betting_game_contract.functions.getLimitedGameData(game_id).call()
    assert status == 'open'

    bet_makers, bet_amounts, bet_predictions = place_bets

    total_bets = sum(bet_amounts)
    expected_fee_income = total_bets * _betFee / 100
    net_pool = total_bets - expected_fee_income
    expected_winnings = []
    #calculate the expected winnings for each bet made
    for b in bet_amounts:
        earnings_per_dollar = net_pool/b
        expected_winnings.append(earnings_per_dollar * b)

    # should test trying to get complete game details before game is closed
    # assert that it fails
    try:
        # if this passes then it means the function was not successful
        full_game_data = betting_game_contract.functions.getFullGameData(game_id).call()
        assert False
    except:
        assert True

    # complete the game
    complete_game_transaction = betting_game_contract.functions.completeGame(game_id).buildTransaction({
        'from': user.address,
        'nonce': w3.eth.get_transaction_count(user.address)
    })
    complete_game_signed = user.sign_transaction(complete_game_transaction)
    complete_game_tx_hash = w3.eth.send_raw_transaction(complete_game_signed.rawTransaction)
    w3.eth.waitForTransactionReceipt(complete_game_tx_hash)

    # validate that the fee income calculation is correct
    actual_fee_income = betting_game_contract.functions.getFeeIncome().call({'from': user.address})
    assert actual_fee_income == expected_fee_income

    # validate the amount won is correct
    full_bet_data = betting_game_contract.functions.getFullBetData(game_id).call()
    bet_makers_after, bet_amounts_after, _, _, winnings_after = full_bet_data

    # if there is a match that means that we found an expected amount that was correct
    # when there is a match we end the test, since there should only be one winner
    # if we do not find a matching value that means
    # the calculation done in the contract was incorrect
    for x in range(4):
        if winnings_after[x] == int(expected_winnings[x]):
            assert True
            assert bet_makers[x] == bet_makers_after[x]
            return

    assert False


def test_complete_game_failure_manager_closed(betting_game_contract, w3, create_game):
    # non-manager tries to complete game, but fails
    game_id, game_manager = create_game

    user = Account().from_key(keys[8])

    try:
        complete_game_transaction = betting_game_contract.functions.completeGame(game_id).buildTransaction({
            'from': user.address,
            'nonce': w3.eth.get_transaction_count(user.address)
        })
        # if it gets the last call this test failed
        assert False

    except:
        # cancel the game with a transaction coming from teh game manager
        cancel_game_transaction = betting_game_contract.functions.cancelGame(game_id).buildTransaction({
            'from': manager.address,
            'nonce': w3.eth.get_transaction_count(manager.address)
        })
        cancel_game_signed = manager.sign_transaction(cancel_game_transaction)
        cancel_game_tx_hash = w3.eth.send_raw_transaction(cancel_game_signed.rawTransaction)
        w3.eth.waitForTransactionReceipt(cancel_game_tx_hash)

    # try to complete the same game that was just cancelled
    try:
        complete_game_transaction = betting_game_contract.functions.completeGame(game_id).buildTransaction({
            'from': manager.address,
            'nonce': w3.eth.get_transaction_count(user.address)
        })
        # if the above function is success it means that the rule failed
        # assert that teh test failed
        assert False

    except:
        assert True
        return


def test_close_game(betting_game_contract, w3, create_game,
                    BettingGame_filter_GameCompleted, BettingGame_filter_GameClosed):
    game_id, game_manager = create_game
    # place bets with predictions above maxrange val
    for x in range(7,10):
        user = Account().from_key(keys[x])
        place_bet_transaction = betting_game_contract.functions.placeBet(game_id, 8).buildTransaction({
            'from': user.address,
            'nonce': w3.eth.get_transaction_count(user.address),
            'value': 2000
        })
        place_bet_signed = user.sign_transaction(place_bet_transaction)
        place_bet_tx_hash = w3.eth.send_raw_transaction(place_bet_signed.rawTransaction)
        w3.eth.waitForTransactionReceipt(place_bet_tx_hash)

    # then close out the game
    complete_game_transaction = betting_game_contract.functions.completeGame(game_id).buildTransaction({
        'from': manager.address,
        'nonce': w3.eth.get_transaction_count(manager.address)
    })
    complete_game_signed = manager.sign_transaction(complete_game_transaction)
    complete_game_tx_hash = w3.eth.send_raw_transaction(complete_game_signed.rawTransaction)
    w3.eth.waitForTransactionReceipt(complete_game_tx_hash)

    # this should emit a different event
    # check and make sure there was not an GameCompleted event
    complete_event = BettingGame_filter_GameCompleted.get_new_entries()
    assert len(complete_event) == 0

    closed_event = BettingGame_filter_GameClosed.get_new_entries()[-1]
    if closed_event.transactionHash == complete_game_tx_hash:
        args = closed_event.args
        _game_id, _game_manager, _total_bets = [args[key] for key in list(args.keys())]

    # make sure that the game_id in the GameClosed event
    # matches that the original game_id
    assert _game_id == game_id



def test_cancel_game(betting_game_contract, w3, create_game, place_bets, BettingGame_filter_GameCancelled):
    # happy path to cancel game
    bet_makers, bet_amounts, bet_predictions = place_bets
    prior_balance = [w3.eth.get_balance(maker) for maker in bet_makers]

    game_id, game_manager = create_game

    cancel_game_transaction = betting_game_contract.functions.cancelGame(game_id).buildTransaction({
        'from': game_manager,
        'nonce': w3.eth.get_transaction_count(game_manager)
    })
    cancel_game_signed = Account().from_key(keys[0]).sign_transaction(cancel_game_transaction)
    cancel_game_tx_hash = w3.eth.send_raw_transaction(cancel_game_signed.rawTransaction)
    w3.eth.waitForTransactionReceipt(cancel_game_tx_hash)

    new_balance = [w3.eth.get_balance(maker) for maker in bet_makers]

    # when the cancel function is run the betted funds are returned to owners
    # so each betters new balance should be greater than their balance
    # after they made their bet
    # with the exception of the first better because that user was also the manager of the wallet
    # and to cancel the game cost some gas and that user might not be positive
    for x in range(1,4):
        assert prior_balance[x] < new_balance[x]

    event = BettingGame_filter_GameCancelled.get_new_entries()[-1]
    if event.transactionHash == cancel_game_tx_hash:
        args = event.args
        _game_id, _ = [args[key] for key in list(args.keys())]

    assert _game_id == game_id


def test_cancel_game_failure_manager(betting_game_contract, w3, create_game, place_bets):
    # non-manager tries to cancel game, should fail
    game_id, game_manager = create_game

    user = Account().from_key(keys[6])

    # try to cancel the game using a user that is not the game manager
    # if the function makes it through the try block
    # it means that the function was unsuccessful and should fail

    try:
        cancel_game_transaction = betting_game_contract.functions.cancelGame(game_id).buildTransaction({
            'from': user.address,
            'nonce': w3.eth.get_transaction_count(user.address)
        })
        cancel_game_signed = user.sign_transaction(cancel_game_transaction)
        cancel_game_tx_hash = w3.eth.send_raw_transaction(cancel_game_signed.rawTransaction)
        w3.eth.waitForTransactionReceipt(cancel_game_tx_hash)

        assert False

    except:
        assert True


def test_cancel_game_failure_closed(betting_game_contract, w3, create_game, place_bets):
    # game is not in an open status; should fail
    game_id, game_manager = create_game
    bet_makers, bet_amounts, bet_predictions = place_bets

    user = Account().from_key(keys[0])

    # complete the game first
    complete_game_transaction = betting_game_contract.functions.completeGame(game_id).buildTransaction({
        'from': user.address,
        'nonce': w3.eth.get_transaction_count(user.address)
    })
    complete_game_signed = user.sign_transaction(complete_game_transaction)
    complete_game_tx_hash = w3.eth.send_raw_transaction(complete_game_signed.rawTransaction)
    w3.eth.waitForTransactionReceipt(complete_game_tx_hash)

    # try to cancel the game that has already been completed
    # if the function makes it through the try block
    # it means that the function was unsuccessful and should fail
    try:
        cancel_game_transaction = betting_game_contract.functions.cancelGame(game_id).buildTransaction({
            'from': user.address,
            'nonce': w3.eth.get_transaction_count(user.address)
        })
        cancel_game_signed = user.sign_transaction(cancel_game_transaction)
        cancel_game_tx_hash = w3.eth.send_raw_transaction(cancel_game_signed.rawTransaction)
        w3.eth.waitForTransactionReceipt(cancel_game_tx_hash)

        assert False

    except:
        assert True


def test_fee_income(betting_game_contract, w3, place_bets, create_game):
    # create game, place bet, then complete game
    # will need to keep track of bet amount
    game_id, game_manager = create_game
    user = Account().from_key(keys[0])
    _, status, _, _, _betFee, _, total_of_bets, _ = betting_game_contract.functions.getLimitedGameData(game_id).call()
    assert status == 'open'

    bet_makers, bet_amounts, bet_predictions = place_bets

    total_bets = sum(bet_amounts)
    expected_fee_income = total_bets * _betFee / 100
    net_pool = total_bets - expected_fee_income
    expected_winnings = []
    #calculate the expected winnings for each bet made
    for b in bet_amounts:
        earnings_per_dollar = net_pool/b
        expected_winnings.append(earnings_per_dollar * b)

    # get the prior fee and ensure that current value is 0
    prior_fee_income = betting_game_contract.functions.getFeeIncome().call({'from': manager.address})
    assert prior_fee_income == 0

    # complete the game to payout the fee and the winnings
    complete_game_transaction = betting_game_contract.functions.completeGame(game_id).buildTransaction({
        'from': user.address,
        'nonce': w3.eth.get_transaction_count(user.address)
    })
    complete_game_signed = user.sign_transaction(complete_game_transaction)
    complete_game_tx_hash = w3.eth.send_raw_transaction(complete_game_signed.rawTransaction)
    w3.eth.waitForTransactionReceipt(complete_game_tx_hash)

    # validate that the expected income matches actual income
    current_fee_income = betting_game_contract.functions.getFeeIncome().call({'from': manager.address})
    assert current_fee_income == expected_fee_income

    bet_makers_full, bet_amounts_after, _, _, bet_winnings_after = betting_game_contract.functions.getFullBetData(game_id).call()

    # check to see if any of the values for the actual winnings
    # match the expected winnings. there should only be one winner,
    # if you find a match assert that the test passed, then end the test with a return
    # if we do not find a match assert false because if means that we never
    # found the expected amount
    for x in range(4):
        if bet_winnings_after[x] == int(expected_winnings[x]):
            assert True
            return

    assert False




def test_get_all_data(betting_game_contract, w3, BettingGame_filter_GameCreated):
    # create multiple games
    # use different account to place bets on each game
    # use getAllGamesCreateByUser and getAllGamesBetOnByUser
    # to validate that the games created and bets made match the expected activity

    users = []
    game_ids = {}

    # create the games
    for x in range(4, 8):
        user = Account().from_key(keys[x])
        users.append(user)

        create_game_transaction = betting_game_contract.functions.createGame(1000, 4).buildTransaction({
            'from': user.address,
            'nonce': w3.eth.get_transaction_count(user.address)
        })
        create_game_signed = user.sign_transaction(create_game_transaction)
        create_game_tx_hash = w3.eth.send_raw_transaction(create_game_signed.rawTransaction)
        w3.eth.waitForTransactionReceipt(create_game_tx_hash)

    # get the game id's
    events = BettingGame_filter_GameCreated.get_new_entries()
    for event in events:
        args = event.args
        _id, _game_manager, _ = [args[key] for key in list(args.keys())]
        game_ids[_game_manager] = _id

    # each user will place a bet on each of the games
    # the prediction of each user will be the same for each user
    new_game_ids = list(game_ids.values())
    for x in range(4):
        # iterate over each game placing a bet
        for y in range(4):
            place_bet = betting_game_contract.functions.placeBet(new_game_ids[y], x).buildTransaction({
                'from': users[x].address,
                'nonce': w3.eth.get_transaction_count(users[x].address),
                'value': 1000
            })
            place_bet_signed = users[x].sign_transaction(place_bet)
            place_bet_tx_hash = w3.eth.send_raw_transaction(place_bet_signed.rawTransaction)
            w3.eth.waitForTransactionReceipt(place_bet_tx_hash)

    # check to see if the data matches
    for x in range(4):
        games_list = betting_game_contract.functions.getAllGamesCreatedByUser(users[x].address).call()
        bets_list = betting_game_contract.functions.getAllGamesBetOnByUser(users[x].address).call()

        # each user should only have created one game and the id should be in the same order of the users
        assert games_list[-1] == game_ids[users[x].address]
        # each user bet on each game so the list is the same for all users
        assert sorted(bets_list) == sorted(list(game_ids.values()))


def test_update_bet_fee(betting_game_contract, BettingGame_filter_BetFeeUpdated, w3):
    newFee = 15
    priorFee = betting_game_contract.functions.betFee().call()

    assert priorFee == 20

    transaction = betting_game_contract.functions.updateBetFee(newFee).buildTransaction({
        'from': manager.address,
        'nonce': w3.eth.get_transaction_count(manager.address)
    })
    signed_transaction = manager.sign_transaction(transaction)
    tx_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    w3.eth.waitForTransactionReceipt(tx_hash)

    event = BettingGame_filter_BetFeeUpdated.get_new_entries()[-1]
    if event.transactionHash == tx_hash:
        args = event.args
        _priorFee, _newFee, _ = [args[key] for key in list(args.keys())]

    assert priorFee == _priorFee
    assert newFee == _newFee
    assert newFee == betting_game_contract.functions.betFee().call()






