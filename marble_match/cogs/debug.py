import logging
from typing import Union

import discord
from discord.ext import commands

import database.database_operation as database_operation
from database.database_setup import DbHandler
import utils.discord_utils as du
import utils.account as accounts
import utils.matches as matches
import utils.bets as bets

logger = logging.getLogger(f'marble_match.{__name__}')


class DebugCog(commands.Cog, name='Debug'):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='test')
    @commands.guild_only()
    async def test(self, ctx: commands.Context):
        # Get match
        match = matches.get_match(ctx, 1, True)
        # Process bets
        bets.process_bets(ctx, match)
        pass

    @commands.command(name='create_bet_debug')
    @commands.guild_only()
    async def create_bet_debug(self, ctx: commands.Context, amount: int, bettor: discord.Member,
                               bet_target: discord.Member, is_history: bool = False, winner: discord.Member = None,
                               id_range_start: int = 0, id_range_end: int = 0):
        bettor_id = du.get_id_by_member(ctx, DbHandler.db_cnc, bettor)
        bet_target_id = du.get_id_by_member(ctx, DbHandler.db_cnc, bet_target)
        if winner:
            winner_id = du.get_id_by_member(ctx, DbHandler.db_cnc, winner)

        if id_range_start:
            for i in range(id_range_start, id_range_end):
                if is_history:
                    database_operation.create_bet_history(DbHandler.db_cnc, i, amount, i, bettor_id, bet_target_id,
                                                          winner_id)
                else:
                    database_operation.create_bet(DbHandler.db_cnc, i, amount, i, bettor_id, bet_target_id)
        else:
            database_operation.create_bet(DbHandler.db_cnc, None, amount, None, bettor_id, bet_target_id)

    @commands.command(name='create_match_debug')
    @commands.guild_only()
    async def create_match_debug(self, ctx, amount: int, active: bool,
                                 challenger: discord.Member, recipient: discord.Member, accepted: bool, count: int):
        """
        """
        logger.debug(f'create_match_debug: {amount}, {active}, {challenger}, {recipient}, {accepted}, {count}')
        x = 0
        while x < count:
            matches.create_match(ctx, None, amount, accounts.get_account(ctx, DbHandler.db_cnc, challenger),
                                 accounts.get_account(ctx, DbHandler.db_cnc, recipient), active, accepted)
            x += 1


def setup(bot: commands.Bot):
    bot.add_cog(DebugCog(bot))
