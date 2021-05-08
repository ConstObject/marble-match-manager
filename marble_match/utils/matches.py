import sqlite3
import logging
import datetime
from typing import Union
from dataclasses import dataclass, field

import discord
from discord.ext import commands

import database.database_operation as database_operation
from database.database_setup import DbHandler
import utils.account as account

logger = logging.getLogger(f'marble_match.{__name__}')


@dataclass(order=True)
class Match:
    id: int
    amount: int
    _active: bool
    challenger: account.Account
    recipient: account.Account
    _accepted: bool
    _winner: account.Account = field(default=None)
    _match_time: datetime.datetime = field(default=None)
    _is_history: bool = field(default=False)

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, activity: bool):
        logger.debug(f'active_setter: {activity}')
        # TODO Write activity to database, check if write was successful then write to db
        self._active = activity

    @property
    def accepted(self) -> bool:
        return self._accepted

    @accepted.setter
    def accepted(self, accepted: bool):
        logger.debug(f'accepted_setter: {accepted}')
        # TODO Write accepted to database, check if write was successful then write to db
        self._accepted = accepted

    @property
    def winner(self) -> account.Account:
        return self._winner

    @winner.setter
    def winner(self, winner_id: account.Account):
        logger.debug(f'winner_setter: {winner_id}')
        # Check if winner_id, is either challenger/recipient
        if winner_id == self.challenger or winner_id == self.recipient:
            logger.debug(f'winner_id is equal to challenger or recipient: '
                         f'{winner_id}, {self.challenger}, {self.recipient}')
            # TODO Write winner_id to database, check if write was successful then write to db
            self._winner = winner_id
        logger.debug(f'Attempted to change winner_id to invalid id: {self}')

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

        # Set _match_time to current time
        self._match_time = datetime.datetime.utcnow()

        # TODO Write history & _match_time to database, check if write was successful then write to db
        # Change history flag
        self._is_history = history

    @property
    def match_time(self) -> datetime.datetime:
        return self._match_time

    @match_time.setter
    def match_time(self, time: datetime.datetime):
        logger.debug(f'match_time_setter: {time}')
        self._match_time = time


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
        return 0

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

    # Get Accounts from match_info player_id
    challenger = account.get_account_from_db(ctx, DbHandler.db_cnc, match_info[2])
    logger.debug(f'challenger: {challenger}')

    # Checks if challenger is int, if true return 0
    if isinstance(challenger, int):
        logger.error('challenger is type int')
        return 0

    recipient = account.get_account_from_db(ctx, DbHandler.db_cnc, match_info[3])
    logger.debug(f'recipient: {recipient}')

    # Check if recipient is int, if true return 0
    if isinstance(recipient, int):
        logger.error('recipient is type int')
        return 0

    # Check history to get data specific to history matches
    if history:
        # Get Account for winner
        winner = account.get_account_from_db(ctx, DbHandler.db_cnc, match_info[4])
        logger.debug(f'winner: {winner}')

        # Checks if winner is int, if true return 0
        if isinstance(winner, int):
            logger.error('winner is type int')
            return 0

        # Create Match with match_info data
        match = Match(match_info[0], match_info[1], True, challenger, recipient, True, winner, match_info[5], True)
        logger.debug(f'match: {match}')
        # Checks if match is type int, if true return 0
        if isinstance(match, int):
            logger.error('match is type int')
            return 0

        # Return match
        return match
    else:
        # Create match with match_info data
        match = Match(match_info[0], match_info[1], match_info[2], challenger, recipient, match_info[5])

        # Checks if match is type int, if true return 0
        if isinstance(match, int):
            logger.error('match is type int')
            return 0

        # Return match
        return match
