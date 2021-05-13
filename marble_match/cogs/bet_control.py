import logging

import discord
from discord.ext import commands

import database.database_operation as database_operation
from database.database_setup import DbHandler
import utils.discord_utils as du
import utils.account as acc
import utils.matches as ma
import utils.bets as bets
import utils.exception as exceptions

logger = logging.getLogger(f'marble_match.{__name__}')


class BetCog(commands.Cog, name='Bets'):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='bet', help='Place a bet on a match, updates bets, if marbles is 0 it will delete your bet')
    @commands.guild_only()
    async def bet(self, ctx, winner: discord.Member, match_id: int, marbles: int):
        """Places a bet on a active and not started match

        Example:
            - `$bet @Sophia 12 5`
            - `$bet @Ness 12 0`

        **Arguments**

        - `<winner>` The player you think will win the match.
        - `<match_id>` The id of the match you'd like to bet on
        - `<marbles>` Amount of marbles you'd like to bet on the match.
        """
        if marbles < 0:
            await du.code_message(ctx, 'Marbles cannot be negative')
            return

        player_id = du.get_id_by_member(ctx, DbHandler.db_cnc, winner)
        better_id = du.get_id_by_member(ctx, DbHandler.db_cnc, ctx.author)

        if database_operation.get_marble_count(DbHandler.db_cnc, player_id) < marbles:
            await du.code_message(ctx, 'You do not have enough marbles for this bet')
            return

        match_info = database_operation.get_match_info_by_id(DbHandler.db_cnc, match_id)

        if match_info == 0:
            await du.code_message(ctx, 'Invalid match id')
            return

        if match_info[2] == 1:
            await du.code_message(ctx, 'Match has started and betting is closed')
            return

        if match_info[5] != 1:
            await du.code_message(ctx, 'You can only bet on matches that both players have accepted')
            return

        if match_info[3] == better_id or match_info[4] == better_id:
            await du.code_message(ctx, 'You cannot bet on matches you are in')

        if match_info[3] != player_id:
            if match_info[4] != player_id:
                await du.code_message(ctx, 'Player is not in this match')
                return

        bet_id = database_operation.find_bet(DbHandler.db_cnc, match_id, better_id)
        bet_info = database_operation.get_bet_info(DbHandler.db_cnc, bet_id)

        if bet_id != 0:
            if marbles == 0:
                database_operation.delete_bet(DbHandler.db_cnc, bet_id)
                database_operation.add_marbles(DbHandler.db_cnc, better_id, bet_info[1])
                await du.code_message(ctx, 'Bet deleted')

            bet_info = database_operation.get_bet_info(DbHandler.db_cnc, bet_id)
            database_operation.add_marbles(DbHandler.db_cnc, better_id, bet_info[1])
            database_operation.subtract_marbles(DbHandler.db_cnc, better_id, marbles)
            database_operation.update_bet(DbHandler.db_cnc, bet_id, player_id, marbles)
            await du.code_message(ctx, 'Bet updated')
            return

        if marbles < 1:
            await du.code_message(ctx, 'Cannot be zero')

        database_operation.create_bet(DbHandler.db_cnc, None, marbles, match_id, better_id, player_id)

        await du.code_message(ctx, 'Bet submitted')

    @bet.error
    async def bet_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'winner':
                await du.code_message(ctx, 'You need to enter who you think will win')
            elif error.param.name == 'match_id':
                await du.code_message(ctx, 'You need to enter a match id')
            elif error.param.name == 'marbles':
                await du.code_message(ctx, 'You need to enter a marble amount')


def setup(bot):
    bot.add_cog(BetCog(bot))
