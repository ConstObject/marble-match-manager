import logging
from typing import Union

import discord
from discord.ext import commands

import database.database_operation as database_operation
from database.database_setup import DbHandler
import utils.account as acc
import utils.discord_utils as du
import utils.exception as exception

logger = logging.getLogger(f'marble_match.{__name__}')


class PrefCog(commands.Cog, name='Preferences'):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='nick', help='Change your nickname')
    @commands.guild_only()
    async def nick(self, ctx: commands.Context, nickname: str):
        logger.debug(f'nick: {nickname}')

        # Check if nickname is empty
        if not nickname.strip():
            await ctx.send('Nickname cannot be empty')
            return
        # Check if nickname contains whitespace
        if " " in nickname:
            await ctx.send('Nickname cannot contain whitespace')
            return

        account = acc.get_account(ctx, DbHandler.db_cnc, ctx.author)

        account.nickname = nickname
        await ctx.send(f'New nickname: "{account.nickname}"')

    @nick.error
    async def generic_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await du.code_message(ctx, f"You're missing required argument: {error.param.name}", 3)
            await ctx.send_help('nick')
        elif isinstance(error, commands.CheckFailure):
            await du.code_message(ctx, f"You're unable to use this command in a dm.", 3)
        elif isinstance(error, exception.UnableToRead):
            await du.code_message(ctx, f'Error reading {error.attribute}', 3)
        elif isinstance(error, exception.UnableToWrite):
            await du.code_message(ctx, f"Error writing {error.attribute}", 3)
        elif isinstance(error, exception.UnableToDelete):
            await du.code_message(ctx, f"Error deleting {error.attribute}", 3)
        elif isinstance(error, exception.UnexpectedEmpty):
            await du.code_message(ctx, f"Error unexpected empty {error.attribute}", 3)
        elif isinstance(error, exception.UnexpectedValue):
            await du.code_message(ctx, f"Unexpected value, {error.attribute}", 3)
        elif isinstance(error, exception.InvalidNickname):
            await du.code_message(ctx, error.message, 3)


def setup(bot):
    bot.add_cog(PrefCog(bot))
