import sqlite3
import discord
import logging

from discord.ext import commands
from dataclasses import dataclass, field
from database import database, database_operation

logger = logging.getLogger('marble_match.account')


@dataclass(order=True)
class Account:
    id: int
    member: discord.Member
    _marbles: int
    server_id: int
    _wins: int
    _loses: int

    @property
    def marbles(self) -> int:
        return self._marbles

    @marbles.setter
    def marbles(self, amount: int):
        logger.debug(f'marbles_setter: {amount}')
        # Check if amount is negative, set to zero if it's negative
        if amount < 0:
            logger.debug('amount was less than zero')
            amount = 0

        # Update marble count in database, check if write was successful then update Account info
        if database_operation.update_marble_count(database.db_connection, self.id, amount):
            self._marbles = amount
            logger.debug('Updated marbles')
        else:
            logger.debug('Unable to update marbles')

    @property
    def wins(self) -> int:
        return self._wins

    @wins.setter
    def wins(self, amount: int):
        logger.debug(f'wins_setter: {amount}')
        # Check if amount is negative, set to zero if it's negative
        if amount < 0:
            logger.debug('amount was less than zero')
            amount = 0

        # Update wins in database, check if write was successful then update Account info
        if database_operation.update_player_wins(database.db_connection, self.id, amount):
            self._wins = amount
            logger.debug('Updated wins')
        else:
            logger.debug('Unable to update marbles')

    @property
    def loses(self) -> int:
        return self._loses

    @loses.setter
    def loses(self, amount: int):
        logger.debug(f'loses_setter: {amount}')
        # Check if amount is negative, set to zero if it's negative
        if amount < 0:
            logger.debug('amount was less than zero')
            amount = 0

        # Update loses in database, check if write was successful then update Account info
        if database_operation.update_player_loses(database.db_connection, self.id, amount):
            self._loses = amount
            logger.debug('Updated loses')
        else:
            logger.debug('Unable to update loses')


def get_account_from_db(ctx: commands.Context, connection: sqlite3.Connection, player_id: int):
    """Returns Account of player_id

    **Arguments**

    - `<ctx>` Context used to get information.
    - `<connection>` sqlite3 connection to read from database.
    - `<player_id>` id of players account in database

    """
    logger.debug(f'get_account_from_db: {player_id}')

    # get player_info from database to use to create a Account
    player_info = database_operation.get_player_info(connection, player_id)
    logger.debug(f'player_info: {player_info}')
    # check that player_info has player information return 0 if it doesn't
    if not player_info:
        logger.debug('player_info is empty')
        return 0

    # split username into name & discriminator
    user_string = player_info[1].split('#')
    # create and place new Account into account to return
    account = Account(player_info[0],
                      discord.utils.get(ctx.guild.members, name=user_string[0], discriminator=user_string[1]),
                      player_info[2], player_info[3], player_info[4], player_info[5])
    logger.debug(f'account: {account}')
    return account


def get_account(ctx: commands.Context, connection: sqlite3.Connection, member: discord.Member):
    """Returns Account of member

    **Arguments**

    - `<ctx>` Context used to get server information
    - `<connection>` sqlite3 connection to read from database
    - `<member>` member who's account we wish to get

    """
    logger.debug(f'get_account: {member}')
    # Check if ctx.channel is dm, return 0 if it is
    if isinstance(ctx.channel, discord.DMChannel):
        logger.debug('ctx channel is dm, get_account not allowed in dms')
        return 0

    # Get id from database and put into player_id
    player_id = database_operation.get_player_id(connection, str(member), ctx.guild.id)
    # If player_id is 0, no index in database, return 0
    if not player_id:
        logger.debug('player_id was not found')
        return 0

    # Get Account from database
    account = get_account_from_db(ctx, connection, player_id)
    # Check if account is zero, to return 0 if Account creation failed
    if not account:
        logger.debug('Unable to create account')
        return 0
    logger.debug(f'account: {account}')

    return account
