import discord
import database
import database_operation
import datetime
import pytz
import discord_utils as du
from discord.ext import commands


class HistoryCog(commands.Cog, name='History'):

    def __init__(self, bot):
        self.bot = bot

    def utc_to_est(self, date):
        date2 = date.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Eastern'))
        return pytz.timezone('US/Eastern').normalize(date2)

    @commands.command(name='match_history', help='Prints out a users match history')
    @commands.guild_only()
    async def match_history(self, ctx, member: discord.Member = None, vs: discord.Member = None):

        if not member:
            member = ctx.author

        if vs:
            opponent_id = database_operation.get_player_id(database.db_connection, str(vs), ctx.guild.id)[0]

        player_id = database_operation.get_player_id(database.db_connection, str(member), ctx.guild.id)[0]
        match_history = database_operation.get_match_history_info_all(database.db_connection, player_id)

        if not match_history:
            await du.code_message(ctx, 'No match history')
            return

        text = ''

        # ♕

        for matches in match_history:
            if vs:
                if matches[2] != opponent_id and matches[3] != opponent_id:
                    continue

            text += f'{matches[1]}\t'

            if matches[2] == matches[4]:
                text += '♕'
            text += f'{du.get_member_by_player_id(ctx, database.db_connection, matches[2]).display_name}\t vs \t'

            if matches[3] == matches[4]:
                text += '♕'
            text += f'{du.get_member_by_player_id(ctx, database.db_connection, matches[3]).display_name}\t'

            text += f'{self.utc_to_est(matches[5]).strftime("%x %X")}\n'

        await du.code_message(ctx, text)

    @commands.command(name='bet_history', help='Prints out a users bet history')
    @commands.guild_only()
    async def bet_history(self, ctx, member: discord.Member = None, bet_target: discord.Member = None):

        if not member:
            member = ctx.author

        if bet_target:
            bet_target_id = database_operation.get_player_id(database.db_connection, str(bet_target), ctx.guild.id)[0]

        better_id = database_operation.get_player_id(database.db_connection, str(member), ctx.guild.id)[0]
        bet_history = database_operation.get_bet_history_info_all(database.db_connection, better_id)

        if bet_history == 0 or bet_history == []:
            await du.code_message(ctx, 'No bet history')
            return

        text = ''

        for bet in bet_history:
            if bet_target:
                if bet[4] != bet_target_id:
                    continue
            text += f'{bet[1]}\t'
            text += f'{du.get_member_by_player_id(ctx, database.db_connection, bet[4]).display_name}\t'

            if bet[4] == bet[5]:
                text += 'Won\t'
            else:
                text += 'Lost\t'

            text += f'{self.utc_to_est(bet[6]).strftime("%x %X")}\n'

        await du.code_message(ctx, text)
