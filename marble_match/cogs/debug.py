import logging

import discord
from discord.ext import commands

import database.database_operation as database_operation
from database.database_setup import DbHandler
import utils.account as acc
import utils.matches as matches

logger = logging.getLogger(f'marble_match.{__name__}')


class DebugCog(commands.Cog, name='Debug'):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='test')
    @commands.guild_only()
    async def test(self, ctx):
        account1 = acc.get_account(ctx, DbHandler.db_cnc, ctx.author)
        account2 = acc.get_account(ctx, DbHandler.db_cnc, ctx.author)
        if account1 == account2:
            print('true')
        else:
            print('false')
        match = matches.get_match(ctx, 1, True)
        print(match)
        match_list = matches.get_matches(ctx, acc.get_account_from_db(ctx, DbHandler.db_cnc, 2))
        for ma in match_list:
            print(ma)

    @commands.command(name='create_match_debug')
    @commands.guild_only()
    async def create_match_debug(self, ctx, amount: int, active: bool,
                                 challenger: discord.Member, recipient: discord.Member, accepted: bool, count: int):
        """
        """
        logger.debug(f'create_match_debug: {amount}, {active}, {challenger}, {recipient}, {accepted}, {count}')
        x = 0
        while x < count:
            matches.create_match(ctx, None, amount, acc.get_account(ctx, DbHandler.db_cnc, challenger),
                                 acc.get_account(ctx, DbHandler.db_cnc, recipient), accepted)
            x += 1


def setup(bot: commands.Bot):
    bot.add_cog(DebugCog(bot))
