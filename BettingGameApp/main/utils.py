
from web3 import Web3, exceptions
from BettingGameApp.w3.BettingGameContract import BettingGameContract
from BettingGameApp.w3.Connection import Rinkeby_Connection

bgc = BettingGameContract().contract()
w3 = Rinkeby_Connection().w3


class GameDetails:
    def get_limited_data(self, game_id):
        try:
            data = bgc.functions.getLimitedGameData(game_id).call()

        except:
            return []

        manager, status, create_time, bet_min, bet_fee, val_range, total_pool, bets_count = data

        game_data = {
            'id': id,
            'manager': manager,
            'status': status.upper(),
            'create_time': create_time,
            'bet_min': Web3.fromWei(bet_min, 'ether'),
            'bet_fee': bet_fee,
            'val_range': val_range,
            'total_pool': Web3.fromWei(total_pool, 'ether'),
            'bets_count': bets_count
        }

        return game_data

    def get_single_game(self, game_id):
        data = self.get_limited_data(game_id)
        self.all_games = data
        self.game_count = 1
        return data

    def get_all_games(self):
        number_of_games = bgc.functions.getGameCount().call()

        game_data = []
        for id in range(0, number_of_games):
            data = self.get_limited_data(id)
            if data:
                game_data.append(data)

        self.all_games= sorted(game_data, key=lambda x: x['id'], reverse=True)
        self.game_count = number_of_games

        return game_data

    @property
    def get_closed_games(self):
        return filter(lambda x: x['status'] == 'closed', self.all_games)

    @property
    def get_open_games(self):
        return filter(lambda x: x['status'] == 'open', self.all_games)

    @property
    def get_cancelled_games(self):
        return filter(lambda x: x['status'] == 'cancelled', self.all_games)

    def get_extended_game_data(self):
        not_open_games = filter(
            lambda x: x['status'] == 'cancelled' or x['status'] == 'closed',
            self.all_games
        )
        not_open_ids = [g['id'] for g in not_open_games]

        game_data = []
        for id in not_open_ids:
            data = bgc.functions.getFullGamedata(id)
            (manager, create_time, bet_min, bet_fee, max_range, winning_num,
            total_pool, winning_pool, winner_count, loser_count) = data

            game_data.append(
                {
                    'manager': manager,
                    'create_time': create_time,
                    'bet_min': Web3.fromWei(bet_min, 'ether'),
                    'bet_fee': bet_fee,
                    'max_range': max_range,
                    'winning_num': winning_num,
                    'total_pool': Web3.fromWei(total_pool, 'ether'),
                    'winning_pool': Web3.fromWei(winning_pool, 'ether'),
                    'winner_count': winner_count,
                    'loser_count': loser_count
                }
            )

        return game_data


class Bet:
    def __init__(self, game_id, prediction, bet_amount):
        self.game_id = game_id
        self.prediction = prediction
        self.bet_amount = Web3.toWei(bet_amount, 'ether')

    def place_bet(self, account):
        try:
            transaction = bgc.functions.placeBet(self.game_id, self.prediction).buildTransaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'value': self.bet_amount
            })
            signed = account.sign_transaction(transaction)
            tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
            self.tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
            self.success = True
            return self


        except exceptions.SolidityError as err:
            self.error_message = str(err)
            self.success = False
            return self

    def get_event_details(self):
        event = bgc.events.BetMade().processReceipt(self.tx_receipt)
        event_data = event['args']
        event_data['betAmount'] = Web3.fromWei(event_data.get('betAmount'), 'ether')
        self.event_data = event_data
        self.event_full = event
        return self.event_data


class BetData:
    def __init__(self, game_id):
        self.game_id = game_id

    def get_full_data(self):
        bet_makers, bet_amounts, predictions, statuses, winnings = bgc.functions.getBetData(self.game_id).call()

        data = dict()
        for pos, obj in enumerate(zip(bet_makers, bet_amounts, predictions, statuses, winnings)):
            maker, amount, prediction, status, amount_won = obj
            data[pos] = {
                'bet_maker': maker,
                'bet_amount': Web3.fromWei(amount, 'ether'),
                'prediction': prediction,
                'bet_status': status.capitalize(),
                'winnings': Web3.fromWei(amount_won, 'ether')
            }

        return data

    def get_limited_data(self):
        bet_makers, bet_amounts, predictions = bgc.functions.getBetData(self.game_id).call()

        data = dict()
        for pos, obj in enumerate(zip(bet_makers, bet_amounts, predictions)):
            maker, amount, prediction = obj
            data[pos] = {
                'bet_maker': maker,
                'bet_amount': Web3.fromWei(amount, 'ether'),
                'prediction': prediction
            }

        return data

    def get_bet_data(self, limit_data=False):
        try:
            return self.bet_data

        except:
            status = bgc.functions.getGameStatus(self.game_id).call()
            if status == 'open' or limit_data:
                bet_data = self.get_limited_data()

            else:
                bet_data = self.get_full_data()

            self.bet_data = bet_data
            self.status = status
            self.limit_data = limit_data

            return self


class CreateGame:
    # this is used to create a game
    # will also contain event handler to
    # capture game details emit
    pass


class CompleteGame:
    # this is used to complete a game
    # will also contain event handler to
    # capture completed game details emit
    pass


class CancelGame:
    # this is used to cancel a game
    # will also contain event handler to
    # capture canceled game details emit
    pass





