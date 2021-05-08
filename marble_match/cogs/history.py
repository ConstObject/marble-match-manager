import asyncio
import math
import datetime

import pytz
import discord
from discord.ext import commands

import database.database_operation as database_operation
from database.database_setup import DbHandler
import utils.discord_utils as du


class HistoryCog(commands.Cog, name='History'):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def utc_to_est(date: datetime.datetime):
        """Returns datetime converted from utc to est

        **Arguments**
        - `<date>` utc date to be converted to est

        """
        date2 = date.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Eastern'))
        return pytz.timezone('US/Eastern').normalize(date2)

    @commands.command(name='match_history', help='Prints out a users match history')
    @commands.guild_only()
    async def match_history(self, ctx: commands.Context, member: discord.Member = None, vs: discord.Member = None):
        """Show match history of user.

        Example:
             - `$match_history @Sophia'
             - `$match_history @Ness'
             - `$match_history @Sophia @Ness'

        **Arguments**

        - `<member>` The user to show the match history of. If omitted, defaults to your own history.
        - `<vs>` The user to limit the match history to only games with them

        """

        if not member:
            member = ctx.author

        if vs:
            opponent_id = du.get_id_by_member(ctx, DbHandler.db_cnc, vs)

        player_id = du.get_id_by_member(ctx, DbHandler.db_cnc, member)
        match_history = database_operation.get_match_history_info_all(DbHandler.db_cnc, player_id)

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
            text += f'{du.get_member_by_player_id(ctx, DbHandler.db_cnc, matches[2]).display_name}\t vs \t'

            if matches[3] == matches[4]:
                text += '♕'
            text += f'{du.get_member_by_player_id(ctx, DbHandler.db_cnc, matches[3]).display_name}\t'

            text += f'{self.utc_to_est(matches[5]).strftime("%x %X")}\n'
            match_list.append(text)

        text = ''
        pages = math.ceil(len(match_list)/10)
        cur_page = pages-1
        active = True

        for i in range(cur_page*10, (cur_page*10) + 10):
            if i < len(match_list):
                text += str(match_list[i])

        if pages > 1:
            text += f'Page {cur_page+1} of {pages}\n'
        else:
            active = False

        message = await du.code_message(ctx, text)

        if pages > 1:
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
        """Prints bet history of user

        Examples:
             - `$bet_history @Sophia'
             - `$bet_history @Ness'
             - `$bet_history @Sophia @Ness'

        **Arguments**

        - `<member>` The user to who's bet history you want to print. If omitted defaults to your own history.
        - '<bet_target>' The user you want to limit bets on to.

        """

        if not member:
            member = ctx.author

        if bet_target:
            bet_target_id = du.get_id_by_member(ctx, DbHandler.db_cnc, bet_target)

        better_id = du.get_id_by_member(ctx, DbHandler.db_cnc, member)
        bet_history = database_operation.get_bet_history_info_all(DbHandler.db_cnc, better_id)

        if bet_history == 0 or bet_history == []:
            await du.code_message(ctx, 'No bet history')
            return

        text = ''
        bet_list = []

        for bet in bet_history:
            text = ''
            if bet_target:
                if bet[4] != bet_target_id:
                    continue
            text += f'{bet[1]}\t'
            text += f'{du.get_member_by_player_id(ctx, DbHandler.db_cnc, bet[4]).display_name}\t'

            if bet[4] == bet[5]:
                text += 'Won\t'
            else:
                text += 'Lost\t'

            text += f'{self.utc_to_est(bet[6]).strftime("%x %X")}\n'
            bet_list.append(text)

        text = ''
        pages = math.ceil(len(bet_list)/10)
        cur_page = pages-1
        active = True

        for i in range(cur_page*10, (cur_page*10) + 10):
            if i < len(bet_list):
                text += str(bet_list[i])

        if pages > 1:
            text += f'Page {cur_page+1} of {pages}\n'
        else:
            active = False

        message = await du.code_message(ctx, text)

        if pages > 1:
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
                        page += bet_list[i]

                    page += f'Page {cur_page+1} of {pages}\n```'
                    await message.edit(content=page)

                    await message.remove_reaction(reaction, user)
                    print('left')

                elif str(reaction.emoji) == '\U000027A1' and cur_page < pages-1:
                    cur_page += 1

                    for i in range(cur_page*10, cur_page*10 + 10):
                        if i < len(bet_list):
                            page += bet_list[i]

                    page += f'Page {cur_page+1} of {pages}\n```'
                    await message.edit(content=page)

                    await message.remove_reaction(reaction, user)
                    print('right')
                else:
                    await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                active = False


def setup(bot):
    bot.add_cog(HistoryCog(bot))
