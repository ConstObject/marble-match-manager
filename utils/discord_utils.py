import sqlite3
import discord
import logging
from database import database_operation
from discord.ext import commands

logger = logging.getLogger('marble_match.discord_utils')


async def code_message(ctx: commands.Context, text: str, color: int = 0):
    """Takes ctx and sends message back to the user

    **Arguments**

    - `<ctx>` Context used to send the message.
    - `<text>` Text to send.
    - `<color>` 0, None. 1, Green. 2, Yellow. 3, Red.

    """
    color_prefix = [('', ''), ('diff', '+ '), ('fix', ''), ('diff', '- ')]
    return await ctx.send(f'```{color_prefix[color][0]}\n{color_prefix[color][1]}{text}\n```')


def get_member_by_player_id(ctx: commands.Context, connection: sqlite3.Connection, player_id: int):
    """Returns discord.Member associated with player_id in database

    **Arguments**

    - `<ctx>` Context used to get server id and member list of server.
    - `<connection>` sqlite3 connection to read from database.
    - `<player_id>` Database index of player you to get discord.Member from.

    """
    logger.debug(f'get_member_by_player_id: {ctx}, {connection}, {player_id}')

    player_info = database_operation.get_player_info(connection, player_id)
    logger.debug(f'player_info: {player_info}')

    if player_info is None:
        logger.debug('player_info is empty')
        return 0

    for member in ctx.guild.members:
        if str(member) == player_info[1]:
            logger.debug(f'Found member matching player_info: {member}')
            return member

    return 0


def get_id_by_member(ctx: commands.Context, connection: sqlite3.Connection, member: discord.Member) -> int:
    """Returns player_id associated with discord.Member

    **Arguments**

    - `<ctx>` Context used to get server of the discord.Member.
    - `<connection>` sqlite3 connection to read from database.
    - `<member>` Member who's player id you'd like to receive.

    """
    logger.debug(f'get_id_by_member: {ctx}, {connection}, {member}')
    if isinstance(ctx.channel, discord.DMChannel):
        logger.debug('Ctx channel is dm, get_id_by_member not allowed in dms')
        return 0

    player_id = database_operation.get_player_id(connection, str(member), ctx.guild.id)
    logger.debug(f'player_id: {player_id}')
    return player_id
