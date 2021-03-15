pragma solidity ^0.6.0;

contract BetInstance {
    struct Bet {
        address betMaker;
        uint pick;
        uint bet;
        uint amountWon;
        bool winner;
    }

    address public manager;
    uint public placeBetFee;
    uint public betMin;
    string public payoutDate;
    bool public openForBets;
    uint private winningNumber;
    uint private feeIncome;
    Bet[] private betsMade;
    uint private grossWinner;
    uint public totalPool;


    modifier restricted() {
        require(msg.sender == manager, 'You are not authorized to perform this function.');
        _;
    }

    constructor (address mngr, uint fee, uint min, string memory closeDate, uint winningNum) public {
        manager = mngr;
        placeBetFee = fee;
        betMin = min;
        payoutDate = closeDate;
        winningNumber = winningNum;
        openForBets = true;
    }

    // this should return the primary data about the bet
    function getData() public view returns (address, uint, uint, string memory, bool, uint, uint, uint, uint) {
        return (manager, placeBetFee, betMin, payoutDate, openForBets, winningNumber,
                grossWinner, totalPool, betsMade.length);
    }


    // NEED TO SEE WHICH BETDATA OPTION IS BETTER

    // get the data on the bets made
    function getBetData(uint index) public restricted view returns (address, uint, uint, uint, bool) {
        Bet memory bet = betsMade[index]; // COULD CHECK TO SEE IF STORAGE IS MORE EFFECIENT IN THE FUTURE
        return (bet.betMaker, bet.pick, bet.bet, bet.amountWon, bet.winner);
    }

    //////// OR /////////

    function getAllBetData() public restricted view returns
    (address[] memory, uint[] memory, uint[] memory, uint[] memory, bool[] memory) {
        address[] memory betMakers = new address[](betsMade.length);
        uint[] memory betPicks = new uint[](betsMade.length);
        uint[] memory betAmounts= new uint[](betsMade.length);
        uint[] memory betWinnings = new uint[](betsMade.length);
        bool[] memory betWinners = new bool[](betsMade.length);

        for (uint b = 0; b < betsMade.length; b++) {
            Bet memory bet = betsMade[b];
            betMakers[b] = bet.betMaker;
            betPicks[b] = bet.pick;
            betAmounts[b] = bet.bet;
            betWinnings[b] = bet.amountWon;
            betWinners[b] = bet.winner;
        }

        return (betMakers, betPicks, betAmounts, betWinnings, betWinners);
    }


    // running this function will payout the winners of the app
    function payoutWinners() public restricted {
        require(betsMade.length > 0, 'There have been no bets');
        // if there were no winners, the manager gets the payout
        if (grossWinner == 0) {
            payable(manager).transfer(totalPool);

        } else {

            uint profit = totalPool - grossWinner;
            uint perDollarEarnings = profit/grossWinner;


            // iterate over the bets made to calculate the winnings
            // and distribute the funds won
            for (uint b = 0; b < betsMade.length; b++) {
                Bet storage bet = betsMade[b];
                if (bet.winner) {
                    // this calculates net winnings
                    uint winnings = bet.bet * perDollarEarnings;

                    // update the amountWon in the bet object
                    bet.amountWon = winnings;

                    // send the user the amount won plus the original investment
                    payable(bet.betMaker).transfer(winnings + bet.bet);
                }
            }
        }


        // close the betting window
        openForBets = false;
    }

    // this is used to place a bet
    function makeBet(uint pick) public payable {
        // must be open for bets
        require(openForBets == true, 'This betting window is no longer open.');
        // user must make a bet meeting minimum combined with fee requirement
        require(msg.value >= betMin + placeBetFee, 'You did not meet minimum fee and bet amount.');
        uint income = msg.value - betMin;
        uint betAmount = msg.value - placeBetFee;

        // add the betAmount to the running bet total
        totalPool += betAmount;

        // if the user's pick is a winner add this to the gross winner pick amount
        if (pick == winningNumber) grossWinner += betAmount;

        // create the bet data
        Bet memory newBet = Bet({
            betMaker: msg.sender,
            pick: pick,
            bet: betAmount,
            amountWon: 0,
            winner: false
        });

        // add the newBet to the betsMade object
        betsMade.push(newBet);

        // pay the manager the fee
        payable(manager).transfer(income);
        feeIncome += income;
    }

}
