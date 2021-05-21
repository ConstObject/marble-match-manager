import logging
from typing import Union
from configparser import ConfigParser

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

    @commands.command(name='color_role_cost', description='Sets the price of color roles')
    @commands.has_role('Admin')
    @commands.guild_only()
    async def color_role_cost(self, ctx: commands.Context, cost: int):
        logger.debug(f'color_role_cost: {int}')

        # Check if cost is not zero or negative
        if cost < 1:
            logger.debug(f'Tried to set cost to zero or negative')
            await du.code_message(ctx, 'Cost cannot be zero or negative', 3)
            return

        # Get ConfigParser to set new value
        config = ConfigParser()
        config.read('marble_bot.ini')

        # Set value to new value
        config.set(str(ctx.guild.id), 'color_role_cost', f'{cost}')

        # Write file
        with open('marble_bot.ini', 'w') as config_file:
            config.write(config_file)

        await du.code_message(ctx, f'Cost of colored roles changed to {cost}', 1)


def setup(bot):
    bot.add_cog(PrefCog(bot))
