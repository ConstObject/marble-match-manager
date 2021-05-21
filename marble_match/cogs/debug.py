import logging

import discord
from discord.ext import commands

import database.database_operation as database_operation
from database.database_setup import DbHandler
import utils.discord_utils as du
import utils.account as accounts
import utils.matches as matches
import utils.bets as bets
import utils.images as image

logger = logging.getLogger(f'marble_match.{__name__}')


async def is_soph(ctx: commands.Context):
    return ctx.author.id == 126913881879740416


class DebugCog(commands.Cog, name='Debug', description="Don't mind me unless you're Soph"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='write_file', description="No longer drive her nuts")
    @commands.check(is_soph)
    async def write_file_dm(self, ctx: commands.Context):
        safe_files = ['change_log.txt', 'database.db', 'marble_bot.ini']
        message: discord.Message = ctx.message
        if message.attachments:
            for attach in message.attachments:
                if attach.filename in safe_files:
                    await message.attachments[0].save(fp=message.attachments[0].filename)

    @commands.command(name='ness_sanity', description="No longer drive her nuts")
    @commands.check(is_soph)
    async def ness_sanity(self, ctx: commands.Context):
        dm_channel = await ctx.author.create_dm()
        await dm_channel.send('database', file=discord.File(r"database.db"))

    @commands.command(name='ness_sanity_log', description="No longer drive her nuts")
    @commands.check(is_soph)
    async def ness_sanity_log(self, ctx: commands.Context):
        dm_channel = await ctx.author.create_dm()
        await dm_channel.send('log', file=discord.File(r"log.log"))

    @commands.command(name='ness_sanity_ini', description="No longer drive her nuts")
    @commands.check(is_soph)
    async def ness_sanity_ini(self, ctx: commands.Context):
        dm_channel = await ctx.author.create_dm()
        await dm_channel.send('ini', file=discord.File(r"marbles_bot.ini"))

    @commands.command(name='test')
    @commands.check(is_soph)
    @commands.guild_only()
    async def test(self, ctx: commands.Context):
        roles = await ctx.guild.fetch_roles()
        print(f'length {len(roles)}\n\n')
        for role in roles:
            print(f'{role}: {role.position}\n\n')

    @commands.command(name='create_bet_debug')
    @commands.check(is_soph)
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
    @commands.check(is_soph)
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
