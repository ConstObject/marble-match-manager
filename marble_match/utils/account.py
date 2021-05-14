import sqlite3
import logging
from typing import Union
from dataclasses import dataclass
from datetime import datetime

import discord
from discord.ext import commands

import database.database_operation as database_operation
import database.database_setup as database_setup
import utils.discord_utils as du
import utils.exception as exception

logger = logging.getLogger('marble_match.acc')


@dataclass(order=True)
class Account:
    id: int
    member: discord.Member
    _nickname: str
    _marbles: int
    server_id: int
    _wins: int
    _loses: int

    @property
    def winrate(self) -> float:
        if self._wins:
            return 100 * (self._wins / (self._wins + self._loses))
        else:
            return 0

    @property
    def friendly_last_used(self) -> Union[datetime, int]:
        logger.debug(f'friendly_last_used_getter')

        # Try and get value from database
        try:
            time = database_operation.get_friendly_last_used(database_setup.DbHandler.db_cnc, self.id)
            if not time:
                logger.debug(f'No last_used value')
                database_operation.create_friendly(database_setup.DbHandler.db_cnc, self.id)
                return 0
            else:
                return time
        except Exception as e:
            logger.error(f'Unable to read friendly_last_used: {e}')
            raise exception.UnableToRead(class_='Account', attribute='friendly_last_used')

    @friendly_last_used.setter
    def friendly_last_used(self, time: datetime):
        logger.debug(f'friendly_last_used_setter: {time}')
        # Try and write to database
        try:
            database_operation.update_friendly(database_setup.DbHandler.db_cnc, self.id, time)
            logger.debug(f'Wrote friendly_last_used: {time}')
        except Exception as e:
            logger.error(f'Unable to write friendly_last_used: {e}')
            raise exception.UnableToWrite(class_='Account', attribute='friendly_last_used')

    @property
    def nickname(self) -> str:
        # Check if nickname equals member, if it does return member.display_name
        if self._nickname == str(self.member):
            logger.debug(f'nickname is same as member')
            return self.member.display_name
        else:
            return self._nickname

    @nickname.setter
    def nickname(self, nickname: str):
        logger.debug(f'nickname_setter: {nickname}')

        # Update nickname in database, check if write was successful then update Account info
        if database_operation.update_player_nickname(database_setup.DbHandler.db_cnc, self.id, nickname):
            self._nickname = nickname
            logger.debug('Updated nickname')
        else:
            logger.error('Unable to update nickname')
            raise exception.UnableToWrite(class_='Account', attribute='nickname', value=nickname)

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
        if database_operation.update_marble_count(database_setup.DbHandler.db_cnc, self.id, amount):
            self._marbles = amount
            logger.debug('Updated marbles')
        else:
            logger.error('Unable to update marbles')
            raise exception.UnableToWrite(class_='Account', attribute='marbles', value=amount)

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
        if database_operation.update_player_wins(database_setup.DbHandler.db_cnc, self.id, amount):
            self._wins = amount
            logger.debug('Updated wins')
        else:
            logger.error('Unable to update marbles')
            raise exception.UnableToWrite(class_='Account', attribute='wins', value=amount)

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
        if database_operation.update_player_loses(database_setup.DbHandler.db_cnc, self.id, amount):
            self._loses = amount
            logger.debug('Updated loses')
        else:
            logger.error('Unable to update loses')
            raise exception.UnableToWrite(class_='Account', attribute='loses', value=amount)


def get_account_from_db(ctx: commands.Context, connection: sqlite3.Connection, player_id: int):
    """Returns Account of player_id

    **Arguments**

    - `<ctx>` Context used to get information.
    - `<connection>` sqlite3 connection to read from database.
    - `<player_id>` id of players acc in database

    """
    logger.debug(f'get_account_from_db: {player_id}')

    # get player_info from database to use to create a Account
    player_info = database_operation.get_player_info(connection, player_id)
    logger.debug(f'player_info: {player_info}')
    # check that player_info has player information return 0 if it doesn't
    if not player_info:
        logger.error('player_info is empty')
        raise exception.UnexpectedEmpty(attribute='users')

    # create and place new Account into acc to return
    account = Account(player_info[0], du.get_member_by_uuid(ctx, player_info[1]), player_info[2], player_info[3],
                      player_info[4], player_info[5], player_info[6])
    logger.debug(f'acc: {account}')
    return account


def get_account(ctx: commands.Context, connection: sqlite3.Connection, member: Union[discord.Member, str]):
    """Returns Account of member

    **Arguments**

    - `<ctx>` Context used to get server information
    - `<connection>` sqlite3 connection to read from database
    - `<member>` member who's acc we wish to get

    """
    logger.debug(f'get_account: {member}')
    # Check if ctx.channel is dm, return 0 if it is
    if isinstance(ctx.channel, discord.DMChannel):
        logger.error('ctx channel is dm, get_account not allowed in dms')
        raise exception.DiscordDM

    # Get id from database and put into player_id
    if isinstance(member, discord.Member):
        player_id = database_operation.get_player_id(connection, member.id, ctx.guild.id)
    else:
        player_id = database_operation.get_player_id_by_username(connection, member)

    # If player_id is 0, no index in database, return 0
    if not player_id:
        logger.error('player_id was not found')
        if isinstance(member, str):
            raise exception.InvalidNickname
        raise exception.UnexpectedEmpty(attribute='user')

    # Get Account from database
    account = get_account_from_db(ctx, connection, player_id)
    # Check if acc is zero, to return 0 if Account creation failed
    if not account:
        logger.error('Unable to create acc')
        raise exception.UnexpectedEmpty(class_='Account', attribute='account')
    logger.debug(f'acc: {account}')

    return account


def get_account_server_all(ctx: commands.Context, connection: sqlite3.Connection, server_id: int) -> Union[list, int]:
    """Returns list of all Accounts on a server

    **Arguments**

    - `<ctx>` Context used to get information
    - `<connection>` Connection for database
    - `<server_id>` Server_id to get all accounts for

    """
    logger.debug(f'get_account_server_all: {server_id}')

    # Get player_list from database and validate
    player_list = database_operation.get_player_info_all_by_server(connection, server_id)
    logger.debug(f'player_list: {player_list}')
    if not player_list:
        logger.error('Unable to get player_list')
        raise exception.UnableToRead(attribute='user')

    # Create list to return, and propagate list with accounts from player_list
    account_list = []
    for player in player_list:
        logger.debug(f'player: {player}')
        account_list.append(Account(player[0], du.get_member_by_uuid(ctx, player[1]), player[2],
                                    player[3], player[4], player[5], player[6]))

    # Check if list has been propagated
    if not len(account_list):
        logger.error('account_list is empty')
        raise exception.UnexpectedEmpty(class_='Account', attribute='account')

    return account_list


def get_account_by_nick(ctx: commands.Context, nickname: str):
    """Returns an account from a nickname

    **Arguments**

    - `<ctx>` Context used to get information
    - `<nickname>` Nickname of users account to get

    """
    logger.debug(f'get_account_by_nick: {nickname}')

    # Get player_id from nickname, and validate
    player_id = database_operation.get_player_id_by_username(database_setup.DbHandler.db_cnc, nickname)
    logger.debug(f'player_id: {player_id}')
    if not player_id:
        logger.debug(f'Unable to get player_id for nickname')
        raise exception.InvalidNickname

    return get_account_from_db(ctx, database_setup.DbHandler.db_cnc, player_id)
