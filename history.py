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

    @commands.command(name='Test1', help='Help')
    @commands.guild_only()
    async def test1(self, ctx):
        example = datetime.datetime.utcnow()
        match_data = database_operation.get_match_history_info(database.db_connection, 3)
        print(example)
        # example.replace(tzinfo=datetime.tzinfo.tzname('US/Eastern'))
        example2 = example.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Eastern'))
        print(pytz.timezone('US/Eastern').normalize(example2))
        # print(match_data[5])

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
