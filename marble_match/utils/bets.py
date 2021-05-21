import datetime
import logging
from typing import Union
from dataclasses import dataclass, field

import discord
from discord.ext import commands

import database.database_operation as database_operation
from database.database_setup import DbHandler

import utils.account as account
import utils.exception as exception
import utils.discord_utils as du
import utils.matches as matches

logger = logging.getLogger(f'marble_match.{__name__}')

# TODO Make this thread safe, improve management of exceptions on database calls


@dataclass(order=True)
class Bet:
    id: int
    _amount: int
    match: matches.Match
    bettor: account.Account
    _bet_target: account.Account
    _winner: account.Account = field(default=None)
    _bet_time: datetime.datetime = field(default=None)
    _is_history: bool = field(default=False)

    @property
    def amount(self) -> int:
        return self._amount

    @amount.setter
    def amount(self, amount):
        logger.debug(f'amount_setter" {amount}')

        # Update amount in database, check if write was successful then update Bet info
        if database_operation.update_bet(DbHandler.db_cnc, self.id, self._bet_target.id, amount):
            logger.debug(f'amount updated')
            self._amount = amount
        else:
            logger.error('Unable to update amount')
            raise exception.UnableToWrite(class_='Bet', attribute='amount', value=amount)

    @property
    def bet_target(self) -> account.Account:
        return self._bet_target

    @bet_target.setter
    def bet_target(self, bet_target: account.Account):
        logger.debug(f'bet_target: {bet_target}')

        if database_operation.update_bet(DbHandler.db_cnc, self._amount, bet_target.id, self._amount):
            logger.debug(f'Updated bet_target')
            self._bet_target = bet_target
        else:
            logger.error('Unable to write bet_target')
            raise exception.UnableToWrite(class_='Bet', attribute='bet_target')

    @property
    def winner(self) -> account.Account:
        return self._winner

    @winner.setter
    def winner(self, winner: account.Account):
        logger.debug(f'winner: {winner}')

        # Check if winner, is either match.challenger/recipient
        if winner == self.match.challenger or winner == self.match.recipient:
            logger.debug(f'winner is equal to challenger or recipient: '
                         f'{winner}, {self.match.challenger}, {self.match.recipient}')
            self._winner = winner
        else:
            logger.error(f'Attempted to change winner to invalid Account: {self}')
            raise exception.UnexpectedValue(class_='Bet', attribute='winner', value=winner,
                                            expected_values=[self.match.challenger, self.match.recipient])

    @property
    def is_history(self) -> bool:
        return self._is_history

    @is_history.setter
    def is_history(self, is_history: bool):
        logger.debug(f'is_history: {is_history}')

        # Check if bet is already history
        if self._is_history:
            logger.debug('Attempted to set is_history flag, when flag is already true')
            return

        # Change history flag
        self._is_history = is_history

    @property
    def bet_time(self) -> datetime.datetime:
        return self._bet_time

    @bet_time.setter
    def bet_time(self, time: datetime.datetime):
        logger.debug(f'bet_time: {time}')
        self._bet_time = time

    def delete_bet(self) -> bool:
        """Deletes bet
        """
        logger.debug(f'delete_bet: {self}')

        # Check if delete was successful
        if database_operation.delete_bet(DbHandler.db_cnc, self.id):
            logger.debug('Deleted bet')
            return True
        else:
            logger.error('Unable to delete bet')
            raise exception.UnableToDelete(class_='Bet', attribute='bet')

    def is_winner(self) -> bool:
        logger.debug(f'is_winner: {self}')

        # Return if bet_target == winner
        return self.bet_target == self.winner

    def create_history(self) -> bool:
        """Creates a instance of bet in bet_history in database

        """
        logger.debug(f'bet.create_history: {self}')

        # Check if needed fields are not None
        if self._winner is None or self._bet_time is None or self._is_history is None:
            logger.error('missing needed field')
            raise exception.UnableToWrite(message='Unable to write missing needed fields', class_='Bet',
                                          attribute='winner, bet_time, is_history')

        # Check if create_bet_history was successful, return true if it was
        if database_operation.create_bet_history(DbHandler.db_cnc, self.id, self._amount, self.match.id,
                                                 self.bettor.id, self._bet_target.id, self._winner.id, self._bet_time):
            logger.debug('Wrote bet to bet_history')
            # Delete bet from table, raise exception if unable to write
            if not database_operation.delete_bet(DbHandler.db_cnc, self.id):
                logger.error(f'Unable to delete bet({self.id}) from bets')
                raise exception.UnableToDelete(attribute='bets')
            return True
        else:
            logger.error(f'Unable to write bet({self.id}) to bet_history')
            raise exception.UnableToWrite(attribute='bet_history')


def get_bet_all(ctx: commands.Context, user: account.Account, user2: account.Account = None,
                history: bool = False) -> Union[list, int]:
    """Returns list of all Bets with user

    **Arguments**

    - `<ctx>` Context used to get information
    - `<user>` User who's bet you wish to get
    - `<user2>` User who you wanna search for as well
    - `<history>` Used to get either match history or active matches

    """
    logger.debug(f'bets.get_bet_all: {user}, {user2}, {history}')

    # Get all bets with user.id, check if bets is valid
    if history:
        bets = database_operation.get_bet_history_info_all(DbHandler.db_cnc, user.id)
    else:
        bets = database_operation.get_bet_info_all(DbHandler.db_cnc, user.id)
    if not bets:
        logger.error('bets is zero')
        return 0

    # Create bet list to return
    bet_list = []

    for bet in bets:
        # Get bettor and check if valid
        bettor = account.get_account_from_db(ctx, DbHandler.db_cnc, bet[3])
        logger.debug(f'bettor: {bettor}')
        if not bettor:
            logger.error('Unable to get bettor account')
            raise exception.UnableToRead(class_='Account', attribute='account')
        # Get bet_target and check if valid
        bet_target = account.get_account_from_db(ctx, DbHandler.db_cnc, bet[4])
        logger.debug(f'bet_target: {bet_target}')
        if not bet_target:
            logger.error('Unable to get bet_target account')
            raise exception.UnableToRead(class_='Account', attribute='account')
        # Get match and check if valid
        match = matches.get_match(ctx, bet[2], history)
        logger.debug(f'match: {match}')
        if not match:
            logger.error('Unable to get match')
            raise exception.UnableToRead(class_='Match', attribute='match')

        # Create match depending on if history is true or not
        if history:
            logger.debug('history is true')

            # Get winner and check if valid
            winner = account.get_account_from_db(ctx, DbHandler.db_cnc, bet[5])
            logger.debug(f'winner: {winner}')
            if not winner:
                logger.error('Unable to get winner account')
                raise exception.UnableToRead(class_='Account', attribute='account')

            append_bet = Bet(bet[0], bet[1], match, bettor, bet_target, winner, bet[6], True)
        else:
            append_bet = Bet(bet[0], bet[1], match, bettor, bet_target)

        logger.debug(f'append_bet: {append_bet}')

        # Check if append_bet is filled
        if append_bet:
            bet_list.append(append_bet)

    # Check if list has been propagated, return 0 otherwise
    if not len(bet_list):
        logger.debug('bet_list length is zero')
        return 0

    # Return bets
    return bet_list


def create_bet(ctx: commands.Context, bet_id: int, amount: int, match: matches.Match,
               bettor: account.Account, bet_target: account.Account) -> Union[Bet, int]:
    """Creates a bet in database and returns the bet from database as a Bet

    """
    logger.debug(f'bet.create_bet: {bet_id}, {amount}, {match}, {bettor}, {bet_target}')

    # Assuming bet_id is None, refill bet_id with results of bet_create, if zero write was unsuccessful
    bet_id = database_operation.create_bet(DbHandler.db_cnc, bet_id, amount, match.id, bettor.id, bet_target.id)
    logger.debug(f'bet_id: {bet_id}')

    # Check if bet_id is valid (Non zero)
    if not bet_id:
        logger.error('Unable to create bet')
        raise exception.UnableToWrite(class_='Bet', attribute='bet')

    # Create bet from bet_id if bet_id is valid
    bet = get_bet(ctx, bet_id)
    logger.debug(f'bet: {bet}')
    if not bet:
        logger.error('Unable to create bet')
        raise exception.UnableToRead(class_='Bet', attribute='bet')

    return bet


def get_bet(ctx: commands.Context, bet_id: int, history: bool = False) -> Union[Bet, int]:
    """Returns a Bet for Bet with bet_id

    **Arguments**
    - `<ctx>` Context used to get members and other information
    - `<bet_id>` Id of the bet to get
    - `<history>` Used to specify if you'd like to get a bet from bet_history or bets

    """
    logger.debug(f'get_bet: {bet_id}, {history}')

    # Check if ctx.channel is dm, return zero if true
    if isinstance(ctx.channel, discord.DMChannel):
        logger.error('ctx channel is dm, get_bet not allowed in dms')
        raise exception.DiscordDM

    # Declare bet_info to be filled later with a tuple of bet data from database
    bet_info = 0

    # Checks history to decide which table to get bet_info from
    if history:
        bet_info = database_operation.get_bet_history_info(DbHandler.db_cnc, bet_id)
    else:
        bet_info = database_operation.get_bet_info(DbHandler.db_cnc, bet_id)
    logger.debug(f'bet_info: {bet_info}')

    # Check if bet_info is zero, if true return. Is non zero when filled with data
    if not bet_info:
        logger.error(f'bet_info is zero')
        return 0

    # Get match from id in bet_info and validate
    match = matches.get_match(ctx, bet_info[2])
    logger.debug(f'match: {match}')
    if not match:
        logger.error('match is zero')
        raise exception.UnableToRead(class_='Match', attribute='match')

    # Get bettor from bet_info and validate
    bettor = account.get_account_from_db(ctx, DbHandler.db_cnc, bet_info[3])
    logger.debug(f'bettor: {bettor}')
    if not bettor:
        logger.error('bettor is zero')
        raise exception.UnableToRead(class_='Account', attribute='account')

    # Get bet_target from bet_info and validate
    bet_target = account.get_account_from_db(ctx, DbHandler.db_cnc, bet_info[4])
    logger.debug(f'bet_target: {bet_target}')
    if not bet_target:
        logger.error('bet_target is zero')
        raise exception.UnableToRead(class_='Account', attribute='account')

    # Check history to get data specific to history matches
    if history:
        logger.debug('history bet')

        # Get winner from bet_info and validate
        winner = account.get_account_from_db(ctx, DbHandler.db_cnc, bet_info[5])
        logger.debug(f'winner: {winner}')
        if not winner:
            logger.error('winner is zero')
            raise exception.UnableToRead(class_='Account', attribute='account')

        # Create Bet with bet_info data
        bet = Bet(bet_info[0], bet_info[1], match, bettor, bet_target, winner, bet_info[6])
    else:
        bet = Bet(bet_info[0], bet_info[1], match, bettor, bet_target)
    logger.debug(f'bet: {bet}')

    return bet


def process_bets(ctx, match: matches.Match) -> bool:
    """Processes all the bets for a given match
    """
    logger.debug(f'process_bets: {match}')

    # Check if match is a history match
    if not match.is_history:
        logger.error(f"Passed a match that isn't history to process_bets")
        return False

    # Get all bets for match, validate that it's not empty
    bet_data = database_operation.get_bet_info_match_all(DbHandler.db_cnc, match.id)
    if not len(bet_data):
        logger.debug(f"No bets placed on this match")
        return False

    # Create list of bets to be filled and processed
    bets = []
    for bet in bet_data:
        # Check if bet and match.id are equal
        if bet[2] == match.id:
            logger.debug(f'Valid bet({bet[0]})')

        # Get bettor account and bet target account, validate
        bettor = account.get_account_from_db(ctx, DbHandler.db_cnc, bet[3])
        bet_target = account.get_account_from_db(ctx, DbHandler.db_cnc, bet[4])
        if not bettor or not bet_target:
            logger.error(f'Unable to get accounts from bet')
            raise exception.UnableToRead(class_='Account', attribute='account')

        # Create bet to append onto bets
        bet_temp = Bet(bet[0], bet[1], match, bettor, bet_target, match.winner)
        logger.debug(f'bet_temp: {bet_temp}')
        if not bet_temp:
            logger.error(f'Unable to create bet')
            raise exception.UnableToWrite(class_='Bet', attribute='bet')
        bets.append(bet_temp)

    # Check if bets has been propagated
    if not len(bets):
        logger.error(f'bets was not propagated')
        return False

    # Total marble count
    marble_pot = 0

    # Total of loser marbles and losers
    loser_count = 0
    loser_pot = 0

    # Total of winner marbles and winners
    winner_count = 0
    winner_pot = 0

    # Calculations that need all bets
    for process_bet in bets:
        # Check if bet is winner
        if process_bet.is_winner():
            # Increment winner count and add bet amount to winner pool
            winner_count += 1
            winner_pot += process_bet.amount
        else:
            # Increment loser count and add bet amount to loser pool
            loser_count += 1
            loser_pot += process_bet.amount
        # Increment total marbles
        marble_pot += process_bet.amount

    logger.debug(f'marble_pot: {marble_pot}, '
                 f'loser: sum({loser_pot}),count({loser_count}), '
                 f'winner: sum({winner_pot}),count({winner_count})')

    # Calculate winner_pot_ratio and winnings per bet
    for calculate_bets in bets:
        if calculate_bets.is_winner():
            # Ratio of your bet in winner_pot
            winner_pot_ratio = calculate_bets.amount/winner_pot
            logger.debug(f'pot_ratio: {winner_pot_ratio}')

            # If loser pot* winner_pot_ratio < 1: return bet amount + one marble
            if (loser_pot*winner_pot_ratio) < 1:
                bet_returns = calculate_bets.amount + 1
            else:
                bet_returns = calculate_bets.amount + (loser_pot*winner_pot_ratio)

            # If no losers, house matches bet and returns double amount
            if loser_count == 0:
                bet_returns = calculate_bets.amount * 2

            logger.debug(f'user: {calculate_bets.bettor.nickname}'
                         f'winner_pot_ratio: {winner_pot_ratio}'
                         f'bet_returns: {bet_returns}')

            # Add bet_returns to bettors marbles
            calculate_bets.bettor.marbles += bet_returns

        # Update calculate_bet to prep for making into history
        calculate_bets.bet_time = datetime.datetime.utcnow()
        calculate_bets.is_history = True
        # Delete bet
        calculate_bets.delete_bet()
        # Make bet history
        calculate_bets.create_history()

    return True
