pragma solidity ^0.8.0;

contract BettingGame {
    // OBJECTS
    // Bet instance
    struct Bet {
        address betMaker;
        uint betAmount; // in wei
        uint betPrediction; // the anticipated winning number
        BetStatus status;
        uint amountWon;
    }

    // Game instance
    struct Game {
        address manager;
        GameStatus status;
        uint createTime;

        uint betMinimum; // in wei
        uint betFee; // in wei

        uint maxRange; // this is the top of the range the winning number could be
        uint winningNum;

        uint totalOfBetsMade; // in wei
        uint grossWinningBets; // in wei

        // data about bets
        Bet[] allBets;
        mapping(address => Bet[]) userBets;

        // lists of the winning and loosing bet indexes
        uint[] winners;
        uint[] losers;
    }

    // Game status
    enum GameStatus {pending, open, closed, cancelled}

    // Bet status
    enum BetStatus{loser, winner, pending}

    // CONTRACT METADATA
    address public manager;
    uint public betFee; // in whole percent EXAMPLE if value is 10 that means 10%
    mapping(address => uint[]) private gamesCreatedByUser; // returns a list of indexes of games a user created
    mapping(address => uint[]) private gamesBetOnByUser; // returns a list of indexes of games a user bet on
    uint private betFeeAmount; // in wei

    // Game[] private allGames;
    uint public numberOfGames;
    mapping(uint => Game) private allGames; // this must be a mapping because Game object has nested mapping
    // mapping(uint => uint) private winningNumbers;

    constructor (uint _betFee) {
        require(_betFee < 100, 'The house fee cannot be greater than 100%');
        manager = msg.sender;
        betFee = _betFee;
        betFeeAmount = 0;
        numberOfGames = 0;

    }

    // EVENTS
    event GameCreated (uint id, address gameManager, uint createTime);
    // bet made
    event BetMade (uint gameId, address betMaker, uint betAmount);
    // game cancelled
    event GameCancelled (uint gameId, address gameManager);
    // game closed no winner
    event GameClosed(uint gameId, address gameManager, uint totalPot);
    // game closer w/ winners
    event GameCompleted (uint gameId, uint numberOfWinners, uint totalPot);
    // bet fee updated
    event BetFeeUpdated (uint priorFee, uint newFee, address manager);

    // MODIFIERS
    modifier onlyOwner {
        require(manager == msg.sender, 'This is only available for the manager to request');
        _;
    }

    modifier gameIsOpen(uint _gameId) {
        Game storage game = allGames[_gameId];
        require(game.status == GameStatus.open, 'This game is not in an open status');
        _;
    }

    modifier gameIsClosed(uint gameId) {
        Game storage game = allGames[gameId];
        require(game.status == GameStatus.closed || game.status == GameStatus.cancelled, 'This game is not in a closed/cancelled status.');
        _;
    }

    // used to make sure user can request game data
    modifier is_manager(uint gameId) {
        Game storage game = allGames[gameId];
        require(msg.sender == game.manager || msg.sender == manager, 'Can only be requested by contract manager or Game manager.');
        _;
    }


    // FUNCTIONS
    /*
        address manager;
        GameStatus status;
        uint createTime;

        uint betMinimum; // in wei
        uint betFee; // in wei

        uint winningNum;

        uint totalOfBetsMade; // in wei
        uint grossWinningBets; // in wei
    */
    function createGame(uint _betMinimum, uint _maxRange) public {
        require(_maxRange > 1, 'Max number to calculate winner must be greater than 1.');
        Game storage game = allGames[numberOfGames];

        game.manager = msg.sender;
        game.status = GameStatus.open;
        game.createTime = block.timestamp;

        game.betMinimum = _betMinimum;
        game.betFee = betFee; // must use betFee set by house

        game.maxRange = _maxRange;
        game.winningNum = generateWinningNumber(_maxRange);

        game.totalOfBetsMade = 0;
        game.grossWinningBets = 0;

        gamesCreatedByUser[msg.sender].push(numberOfGames); // add the index to the list of games this user created

        numberOfGames++;

        emit GameCreated(numberOfGames - 1, game.manager, game.createTime);
    }

    function generateWinningNumber(uint _maxRange) private view returns (uint) {
        uint randomnumber = uint(keccak256(abi.encodePacked(block.timestamp, msg.sender, numberOfGames))) % _maxRange;
        return randomnumber;
    }

    function checkForBets(uint _gameId, uint _prediction, address _user) private view returns (bool) {
        Game storage game = allGames[_gameId];
        Bet[] memory userBetsMade = game.userBets[_user];

        if (userBetsMade.length == 0) return true;

        // check to see if user already made same bet
        for (uint i; i < userBetsMade.length; i++) {
            if (userBetsMade[i].betPrediction == _prediction) return false;
        }
        return true;
    }

    function placeBet(uint _gameId, uint _prediction) public payable gameIsOpen(_gameId) {

        // check to see if user has already made the same bet.
        bool result = checkForBets(_gameId, _prediction, msg.sender);
        require(result == true, 'User has already made this prediction.');

        Game storage game = allGames[_gameId];

        // make sure user met required minimum
        require(msg.value >= game.betMinimum, 'You did not meet the minimum amount to bet.');

        uint _betAmount = msg.value;

        game.totalOfBetsMade += _betAmount;

        // create the new bet object
        Bet memory newBet = Bet({
            betMaker: msg.sender,
            betAmount: _betAmount,
            betPrediction: _prediction,
            status: BetStatus.pending,
            amountWon: 0
        });


        if(_prediction == game.winningNum) {
            game.grossWinningBets += _betAmount;
            game.winners.push(game.allBets.length);
            newBet.status = BetStatus.winner;
        } else {
            game.losers.push(game.allBets.length);
            newBet.status = BetStatus.loser;
        }

        game.userBets[msg.sender].push(newBet);
        game.allBets.push(newBet);

        gamesBetOnByUser[msg.sender].push(_gameId); // append to array gameId that was bet on.

        // generate the BetMade event to emit highlevel data about the bet.
        emit BetMade(_gameId, msg.sender, _betAmount);

    }

    function completeGame(uint _gameId) public is_manager(_gameId) gameIsOpen(_gameId) {
        Game storage game = allGames[_gameId];

        require(game.allBets.length > 0, 'There have been no bets made'); // don't close out the game if no bets have been made

        uint houseFee = game.totalOfBetsMade * game.betFee / 100;
        uint profit = game.totalOfBetsMade - houseFee;

        if (game.grossWinningBets == 0) {

            payable(game.manager).transfer(profit); // payout the manager of the game for the profit after the fee is taken out
            payable(manager).transfer(houseFee); // payout the house for the fee earned off total pot

            betFeeAmount += houseFee;

            game.status = GameStatus.closed;

            emit GameClosed(_gameId, game.manager, game.totalOfBetsMade);

        } else {

            uint perDollarEarnings = (profit * 100)/game.grossWinningBets; // calculate the earnings per dollar for a winning prediction

            payable(manager).transfer(houseFee); // payout the house for the fee earned off total pot
            betFeeAmount += houseFee;

            // iterate over the bets made to calculate the winnings
            // and distribute the funds won
            for (uint b = 0; b < game.allBets.length; b++) {
                Bet storage bet = game.allBets[b];
                // check to set if this was a winning bet
                if (bet.status == BetStatus.winner) {
                    // this calculates net winnings
                    uint winnings = (bet.betAmount * perDollarEarnings) / 100;

                    // update the amountWon in the bet object
                    bet.amountWon = winnings;

                    // send the user the amount won
                    payable(bet.betMaker).transfer(winnings);

            game.status = GameStatus.closed;

            emit GameCompleted (_gameId, game.winners.length, game.totalOfBetsMade);

                }
            }
        }
    }

    function cancelGame(uint _gameId) public is_manager(_gameId) gameIsOpen(_gameId) {
        Game storage game = allGames[_gameId];

        game.status = GameStatus.cancelled;

        // when game is cancelled all users receive their funds back
        for(uint i = 0; i < game.allBets.length; i++) {
            Bet storage bet = game.allBets[i];
            payable(bet.betMaker).transfer(bet.betAmount);
        }

        emit GameCancelled(_gameId, game.manager);
    }

    function getGameCount() public view returns(uint) {
        return numberOfGames;
    }


    function convertGameStatus(GameStatus status) private pure returns (string memory statusName) {
        // check across all the game status options and return the string equivalent
        if(status == GameStatus.open) return 'open';
        if(status == GameStatus.closed) return 'closed';
        if(status == GameStatus.cancelled) return 'cancelled';
        if(status == GameStatus.pending) return 'pending';

    }

    function convertBetStatus(BetStatus status) private pure returns (string memory statusName) {
        // check across all the game status options and return the string equivalent
        if(status == BetStatus.winner) return 'winner';
        if(status == BetStatus.loser) return 'loser';
        if(status == BetStatus.pending) return 'pending';
    }

    function getGameStatus(uint _gameId) public view returns(string memory) {
        return convertGameStatus(allGames[_gameId].status); // returns status as converted string
    }

    /*
    This will return game metadata; it will be limited to non-sensitive information
    address manager;
    GameStatus status;
    uint createTime;
    uint betMinimum; // in wei
    uint betFee; // in wei
    uint totalOfBetsMade; // in wei
    uint allBets.length;
    */
    function getLimitedGameData(uint _gameId) public gameIsOpen(_gameId) view returns (address, string memory, uint, uint, uint, uint, uint, uint) {
        Game storage game = allGames[_gameId];
        return (
            game.manager,
            convertGameStatus(game.status),
            game.createTime,
            game.betMinimum,
            game.betFee,
            game.maxRange,
            game.totalOfBetsMade,
            game.allBets.length
            );
    }

    /*
    This will turn all game metadata
    address manager;
    uint createTime;
    uint betMinimum; // in wei
    uint betFee; // in wei
    uint maxRange;
    uint winningNum;
    uint totalOfBetsMade; // in wei
    uint grossWinningBets; // in wei
    uint allBets.length;
    uint winners.length;
    uint losers.length;
    */
    function getFullGameData(uint _gameId) public gameIsClosed(_gameId) view returns (address, uint, uint, uint, uint, uint, uint, uint, uint, uint) {
        Game storage game = allGames[_gameId];

        return (
            game.manager,
            game.createTime,
            game.betMinimum,
            game.betFee,
            game.maxRange,
            game.winningNum,
            game.totalOfBetsMade,
            game.grossWinningBets,
            game.winners.length,
            game.losers.length
            );
    }


    // get bet data
        // will return bet information from one game
        // would be used prior to game being closed to present bet data
    function getBetData(uint _gameId) public view returns(address[] memory, uint[] memory, uint[] memory) {
        Game storage game = allGames[_gameId];

        uint length = game.allBets.length;

        // set up the value objects that will be returned
        address[] memory betMakers = new address[](length);
        uint[] memory betAmounts = new uint[](length);
        uint[] memory betPredictions = new uint[](length);

        for (uint b = 0; b < length; b++) {
            Bet memory bet = game.allBets[b];

            betMakers[b] = bet.betMaker;
            betAmounts[b] = bet.betAmount;
            betPredictions[b] = bet.betPrediction;
        }

        return (betMakers, betAmounts, betPredictions);

    }

    // this can be accessed after the bet is closed; will return more information about each bet
    function getFullBetData(uint _gameId) public gameIsClosed(_gameId) view returns(address[] memory, uint[] memory, uint[] memory, string[] memory, uint[] memory) {
        Game storage game = allGames[_gameId];

        uint length = game.allBets.length;

        // set up the value objects that will be returned
        address[] memory betMakers = new address[](length);
        uint[] memory betAmounts = new uint[](length);
        uint[] memory betPredictions = new uint[](length);
        string[] memory betStatuses = new string[](length);
        uint[] memory winnings = new uint[](length);


        for (uint b = 0; b < length; b++) {
            Bet memory bet = game.allBets[b];

            betMakers[b] = bet.betMaker;
            betAmounts[b] = bet.betAmount;
            betPredictions[b] = bet.betPrediction;
            betStatuses[b] = convertBetStatus(bet.status);
            winnings[b] = bet.amountWon;
        }

        return (betMakers, betAmounts, betPredictions, betStatuses, winnings);

    }

    function getFeeIncome() public onlyOwner view returns(uint) {
        return betFeeAmount;
    }

    function updateBetFee(uint _newFee) public onlyOwner {
        require(_newFee < 100, 'The house fee cannot be greater than 100%');

        uint _priorFee = betFee; // set the old fee to be prior fee
        betFee = _newFee; // update the fee value metaData

        emit BetFeeUpdated (_priorFee, betFee, msg.sender); // generate event that fee has been updated
    }

    function getAllGamesCreatedByUser(address _user) public view returns (uint[] memory) {
        return gamesCreatedByUser[_user];
    }

    function getAllGamesBetOnByUser(address _user) public view returns (uint[] memory) {
        return gamesBetOnByUser[_user];
    }
}