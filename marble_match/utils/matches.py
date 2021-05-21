import logging
import datetime
from typing import Union
from dataclasses import dataclass, field

import discord
from discord.ext import commands

import database.database_operation as database_operation
from database.database_setup import DbHandler
import utils.account as acc
import utils.exception as exception

logger = logging.getLogger(f'marble_match.{__name__}')

# TODO Make this thread safe, improve management of exceptions on database calls


@dataclass(order=True)
class Match:
    id: int
    amount: int
    _active: bool
    challenger: acc.Account
    recipient: acc.Account
    _accepted: bool
    _winner: acc.Account = field(default=None)
    _match_time: datetime.datetime = field(default=None)
    _game: str = field(default='melee')
    _format: str = field(default='Bo3')
    _is_history: bool = field(default=False)

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, activity: bool):
        logger.debug(f'active_setter: {activity}')

        # Update active in database, check if write was successful then update Match info
        if database_operation.update_match_activity(DbHandler.db_cnc, self.id, int(activity)):
            self._active = activity
            logger.debug('Updated active')
        else:
            logger.error('Unable to update active')
            raise exception.UnableToWrite(class_='Match', attribute='active', value=activity)

    @property
    def accepted(self) -> bool:
        return self._accepted

    @accepted.setter
    def accepted(self, accepted: bool):
        logger.debug(f'accepted_setter: {accepted}')

        # Update accepted in database, check if write was successful then update Match info
        if database_operation.update_match_accepted(DbHandler.db_cnc, self.id, int(accepted)):
            self._accepted = accepted
            logger.debug('Updated accepted')
        else:
            logger.error('Unable to update accepted')
            raise exception.UnableToWrite(class_='Match', attribute='accepted', value=accepted)

    @property
    def winner(self) -> acc.Account:
        return self._winner

    @winner.setter
    def winner(self, winner_id: acc.Account):
        logger.debug(f'winner_setter: {winner_id}')
        # Check if winner_id, is either challenger/recipient
        if winner_id == self.challenger or winner_id == self.recipient:
            logger.debug(f'winner_id is equal to challenger or recipient: '
                         f'{winner_id}, {self.challenger}, {self.recipient}')
            self._winner = winner_id
        else:
            logger.error(f'Attempted to change winner_id to invalid id: {self}')
            raise exception.UnexpectedValue(class_='Match', attribute='winner', value=winner_id,
                                            expected_values=[self.challenger, self.recipient])

    @property
    def is_history(self) -> bool:
        return self._is_history

    @is_history.setter
    def is_history(self, history: bool):
        logger.debug(f'is_history_setter: {history}')

        # Check if match is already history
        if self._is_history:
            logger.debug(f'Attempted to set is_history flag, when flag is already true')
            return

        # Change history flag
        self._is_history = history

    @property
    def match_time(self) -> datetime.datetime:
        return self._match_time

    @match_time.setter
    def match_time(self, time: datetime.datetime):
        logger.debug(f'match_time_setter: {time}')
        self._match_time = time

    @property
    def game(self) -> str:
        return self._game

    @property
    def format_(self) -> str:
        return self._format

    @property
    def full_game(self) -> str:
        return f'{self._game}[{self._format}]'

    def create_history(self) -> bool:
        logger.debug(f'match.create_History: {self}')
        # Check if create_match_history was successful, return True if it was
        if database_operation.create_match_history(DbHandler.db_cnc, self.id, self.amount, self.challenger.id,
                                                   self.recipient.id, self._winner.id, self._match_time,
                                                   self._game, self._format):
            logger.debug('Wrote match to match_history')
            # Delete match from table, raise exception if unable to write
            if not database_operation.delete_match(DbHandler.db_cnc, self.id):
                logger.error('Unable to delete match from matches')
                raise exception.UnableToDelete(attribute='matches')

            return True
        else:
            logger.error('Unable to write to match_history')
            raise exception.UnableToWrite(attribute='match_history')


def create_match(ctx, match_id: int, amount: int, challenger: acc.Account, recipient: acc.Account,
                 active: bool = False, accepted: bool = False,
                 game: str = 'melee', format: str = 'Bo3') -> Union[Match, int]:
    logger.debug(f'match.create_match: {match_id}, {amount}, {challenger}, {recipient}, {active}, {accepted}')

    # Assuming match_id is None, refill match_id with results of create_match, if zero write was unsuccessful
    match_id = database_operation.create_match(DbHandler.db_cnc, match_id, amount, challenger.id, recipient.id, active,
                                               accepted, game, format)
    logger.debug(f'match_id: {match_id}')

    # Check if match_id is valid (Non zero)
    if not match_id:
        logger.error('Unable to create match')
        raise exception.UnableToWrite(attribute='matches')

    # Create Match from match_id, check if match is valid
    match = get_match(ctx, match_id)
    logger.debug(f'match: {match}')
    if not match:
        logger.error('Unable to create match')
        raise exception.UnableToRead(class_='Match', attribute='match')

    return match


def get_matches_all(ctx, user: acc.Account, user2: acc.Account = None, history: bool = False) -> Union[list, int]:
    """Returns list of all Matches with user

    **Arguments**

    - `<ctx>` Context used to get information
    - `<user>` User who's matches you wish to get
    - `<user2>` User who you wanna search for as well
    - `<history>` Used to get either match history or active matches

    """
    logger.debug(f'get_matches_all: {user}, {user2}, {history}')

    # Get all matches with user.id
    if history:
        matches = database_operation.get_match_history_info_all(DbHandler.db_cnc, user.id)
    else:
        matches = database_operation.get_match_info_all(DbHandler.db_cnc, user.id)
    logger.debug(f'matches: {matches}')

    # Check if matches is valid
    if not matches:
        logger.error('matches is zero')
        if history:
            raise exception.UnableToRead(attribute='matches')
        else:
            raise exception.UnableToRead(attribute='matches_history')

    # Create match list to return
    match_list = []

    # Loop through matches and create matches to return
    for match in matches:
        # Get challenger Account and check if valid
        if history:
            challenger_id = match[2]
        else:
            challenger_id = match[4]
        challenger = acc.get_account_from_db(ctx, DbHandler.db_cnc, challenger_id)
        logger.debug(f'challenger: {challenger}')
        if not challenger:
            logger.error('Unable to get challenger acc')
            raise exception.UnableToRead(class_='Account', attribute='account')

        # Get recipient Account and check if valid
        if history:
            recipient_id = match[3]
        else:
            recipient_id = match[4]
        recipient = acc.get_account_from_db(ctx, DbHandler.db_cnc, recipient_id)
        logger.debug(f'recipient: {recipient}')
        if not recipient:
            logger.error('Unable to get challenger acc')
            raise exception.UnableToRead(class_='Account', attribute='account')

        # Check if user2 is not none, to change search to games with user2
        if user2 is not None:
            logger.debug('user2 is not None')
            if challenger.id == user2.id or recipient.id == user2.id:
                pass
            else:
                continue

        # Create match and check if valid before appending to list
        if history:
            logger.debug('history is true')
            # Get winner Account and check if valid
            winner = acc.get_account_from_db(ctx, DbHandler.db_cnc, match[4])
            logger.debug(f'winner: {winner}')
            if not winner:
                logger.error('Unable to get winner account')
                raise exception.UnableToRead(class_='Account', attribute='account')
            append_match = Match(match[0], match[1], True, challenger, recipient, True, winner,
                                 match[5], match[6], match[7], True)

        else:
            append_match = Match(match[0], match[1], match[2], challenger, recipient, match[5],
                                 _game=match[6], _format=match[7])

        logger.debug(f'append_match: {append_match}')
        if isinstance(append_match, Match):
            match_list.append(append_match)

    # Check if list has been propagated, return 0 if not
    if not len(match_list):
        logger.debug('match_list length is zero')
        return 0

    # Return matches
    return match_list


def get_match(ctx: commands.Context, match_id: int, history: bool = False) -> Union[Match, int]:
    """Returns Match for Match with match_id

    **Arguments**

    - `<ctx>` Context used to get members and other information
    - `<match_id>` Id of the match to get
    - `<history>` Used to specify if you'd like to get a match from match_history or matches

    """
    logger.debug(f'get_match: {match_id}, {history}')

    # Check if ctx.channel is dm, return zero if true
    if isinstance(ctx.channel, discord.DMChannel):
        logger.error('ctx channel is dm, get_match not allowed in dms')
        raise exception.DiscordDM

    # Declare match_info to be filled later with tuple of match data from database
    match_info = 0

    # Checks history to decide which table to get match_info from
    if history:
        match_info = database_operation.get_match_history_info(DbHandler.db_cnc, match_id)
    else:
        match_info = database_operation.get_match_info_by_id(DbHandler.db_cnc, match_id)
    logger.debug(f'match_info: {match_info}')

    # Checks if match_info is int, if true return. Is tuple when filled with data
    if isinstance(match_info, int):
        logger.error(f'match_info was type int')
        return 0

    # Check history to get data specific to history matches
    if history:
        # Get Account of challenger
        challenger = acc.get_account_from_db(ctx, DbHandler.db_cnc, match_info[2])
        logger.debug(f'challenger: {challenger}')
        # Checks if challenger is int, if true return 0
        if isinstance(challenger, int):
            logger.error('challenger is type int')
            raise exception.UnableToRead(class_='Account', attribute='account')

        # Get Account of recipient
        recipient = acc.get_account_from_db(ctx, DbHandler.db_cnc, match_info[3])
        logger.debug(f'recipient: {recipient}')
        # Check if recipient is int, if true return 0
        if isinstance(recipient, int):
            logger.error('recipient is type int')
            raise exception.UnableToRead(class_='Account', attribute='account')

        # Get Account for winner
        winner = acc.get_account_from_db(ctx, DbHandler.db_cnc, match_info[4])
        logger.debug(f'winner: {winner}')
        # Checks if winner is int, if true return 0
        if isinstance(winner, int):
            logger.error('winner is type int')
            raise exception.UnableToRead(class_='Account', attribute='account')

        # Create Match with match_info data
        match = Match(match_info[0], match_info[1], True, challenger, recipient, True, winner, match_info[5],
                      match_info[6], match_info[7], True)
        logger.debug(f'match: {match}')
        # Checks if match is type int, if true return 0
        if isinstance(match, int):
            logger.error('match is type int')
            raise exception.UnableToWrite(class_='Match', attribute='match')

        # Return match
        return match
    else:
        # Get Account of challenger
        challenger = acc.get_account_from_db(ctx, DbHandler.db_cnc, match_info[3])
        logger.debug(f'challenger: {challenger}')
        # Checks if challenger is int, if true return 0
        if isinstance(challenger, int):
            logger.error('challenger is type int')
            raise exception.UnableToRead(class_='Account', attribute='account')

        # Get Account of recipient
        recipient = acc.get_account_from_db(ctx, DbHandler.db_cnc, match_info[4])
        logger.debug(f'recipient: {recipient}')
        # Check if recipient is int, if true return 0
        if isinstance(recipient, int):
            logger.error('recipient is type int')
            raise exception.UnableToRead(class_='Account', attribute='account')
        # Create match with match_info data
        match = Match(match_info[0], match_info[1], match_info[2], challenger, recipient, match_info[5],
                      _game=match_info[6], _format=match_info[7])

        # Checks if match is type int, if true return 0
        if isinstance(match, int):
            logger.error('match is type int')
            raise exception.UnableToWrite(class_='Match', attribute='match')

        # Return match
        return match


def get_matches(ctx, user: acc.Account) -> Union[list, int]:
    logger.debug(f'get_match: {user}')

    # Get matches for Account, check if valid
    match_list = get_matches_all(ctx, user)
    logger.debug(f'match_list: {match_list}')
    if isinstance(match_list, int):
        logger.error('match_list is zero')
        return 0

    # Return match_list
    return match_list
