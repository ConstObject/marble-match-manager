import discord
import database
import database_operation
from discord_utils import code_message
from discord.ext import commands


class BetCog(commands.Cog, name='Bets'):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='bet', help='Place a bet on a match, updates bets, if marbles is 0 it will delete your bet')
    @commands.guild_only()
    async def bet(self, ctx, winner: discord.Member, match_id: int, marbles: int):

        if marbles < 0:
            await code_message(ctx, 'Marbles cannot be negative')
            return

        player_id = database_operation.get_player_id(database.db_connection, str(winner), ctx.guild.id)[0]
        better_id = database_operation.get_player_id(database.db_connection, str(ctx.author), ctx.guild.id)[0]

        match_info = database_operation.get_match_info_by_id(database.db_connection, match_id)

        if match_info == 0:
            await code_message(ctx, 'Invalid match id')
            return

        if match_info[2] == 1:
            await code_message(ctx, 'Match has started and betting is closed')
            return

        if match_info[5] != 1:
            await code_message(ctx, 'You can only bet on matches that both players have accepted')
            return

        if match_info[3] == better_id or match_info[4] == better_id:
            await code_message(ctx, 'You cannot bet on matches you are in')

        if match_info[3] != player_id:
            if match_info[4] != player_id:
                await code_message(ctx, 'Player is not in this match')
                return

        bet_id = database_operation.find_bet(database.db_connection, match_id, better_id)

        if bet_id != 0:
            if marbles == 0:
                database_operation.delete_bet(database.db_connection, bet_id)
                await code_message(ctx, 'Bet deleted')

            bet_info = database_operation.get_bet_info(database.db_connection, bet_id)
            database_operation.add_marbles(database.db_connection, better_id, bet_info[1])
            database_operation.update_bet(database.db_connection, bet_id, player_id, marbles)
            await code_message(ctx, 'Bet updated')
            return

        if marbles < 1:
            await code_message(ctx, 'Cannot be zero')

        database_operation.create_bet(database.db_connection, None, marbles, match_id, better_id, player_id)

        await code_message(ctx, 'Bet submitted')

    @bet.error
    async def bet_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'winner':
                await code_message(ctx, 'You need to enter who you think will win')
            elif error.param.name == 'match_id':
                await code_message(ctx, 'You need to enter a match id')
            elif error.param.name == 'marbles':
                await code_message(ctx, 'You need to enter a marble amount')


def setup(bot):
    bot.add_cog(BetCog(bot))
