import asyncio
import math

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
        """Show match history of user.

        Example:
             - `$match_history @Sophia'
             - `$match_history @Ness'

        **Arguments**

        - `<member>` The user to show the match history of. If omitted, defaults to your own history
        - `<vs>` The user to limit the match history to only games with them

        """

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
        match_list = []

        # ♕

        for matches in match_history:
            text = ''
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
            match_list.append(text)



        text = ''
        pages = math.ceil(len(match_history)/10)
        cur_page = pages-1
        active = True

        for i in range(cur_page*10, (cur_page*10) + 10):
            if i < len(match_list):
                text += str(match_list[i])

        text += f'Page {cur_page+1} of {pages}\n'

        message = await du.code_message(ctx, text)

        await message.add_reaction('\U00002B05')
        await message.add_reaction('\U000027A1')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['\U00002B05', '\U000027A1']

        while active:
            try:
                page = '```\n'
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)
                if str(reaction.emoji) == '\U00002B05' and cur_page > 0:
                    cur_page -= 1

                    for i in range(cur_page*10, cur_page*10 + 10):
                        page += match_list[i]

                    page += f'Page {cur_page+1} of {pages}\n```'
                    await message.edit(content=page)

                    await message.remove_reaction(reaction, user)
                    print('left')

                elif str(reaction.emoji) == '\U000027A1' and cur_page < pages-1:
                    cur_page += 1

                    for i in range(cur_page*10, cur_page*10 + 10):
                        if i < len(match_list):
                            page += match_list[i]

                    page += f'Page {cur_page+1} of {pages}\n```'
                    await message.edit(content=page)

                    await message.remove_reaction(reaction, user)
                    print('right')
                else:
                    await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                active = False

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


def setup(bot):
    bot.add_cog(HistoryCog(bot))
