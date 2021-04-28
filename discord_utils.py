import sqlite3
import discord
import database
import database_operation
from discord.ext import commands


async def code_message(ctx: commands.Context, text: str, color: int = 0):
    """Takes ctx and sends message back to the user

    **Arguments**

    - `<ctx>` Context used to send the message.
    - `<text>` Text to send.
    - `<color>` Currently not implemented.

    """
    return await ctx.send(f'```\n{text}```')


def get_member_by_player_id(ctx: commands.Context, connection: sqlite3.Connection, player_id: int):
    """Returns discord.Member associated with player_id in database

    **Arguments**

    - `<ctx>` Context used to get server id and member list of server.
    - `<connection>` sqlite3 connection to read from database.
    - `<player_id>` Database index of player you to get discord.Member from.

    """
    player_info = database_operation.get_player_info(connection, player_id)

    if player_info is None:
        return 0

    for member in ctx.guild.members:
        if str(member) == player_info[1]:
            return member

    return 0


def get_id_by_member(ctx: commands.Context, connection: sqlite3.Connection, member: discord.Member) -> int:
    """Returns player_id associated with discord.Member

    **Arguments**

    - `<ctx>` Context used to get server of the discord.Member.
    - `<connection>` sqlite3 connection to read from database.
    - `<member>` Member who's player id you'd like to receive.

    """
    if isinstance(ctx.channel, discord.DMChannel):
        return 0

    return database_operation.get_player_id(connection, str(member), ctx.guild.id)
