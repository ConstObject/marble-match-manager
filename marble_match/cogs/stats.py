import logging
import math
import operator
import asyncio
from typing import Union

import discord
from discord.ext import commands

from database.database_setup import DbHandler
import database.database_operation as db_op
import utils.discord_utils as du
import utils.account as acc
import utils.exception as exception

logger = logging.getLogger(f'marble_match.{__name__}')

# TODO Add bet_total_won, really complex gotta simulate the process bets again
account_stats = ['wins', 'loses', 'marbles', 'winrate', 'elo']
non_account_stats = ['match_count', 'bet_total', 'bet_winrate', 'season']
# Returns [[user.id, match_count], ...]
match_count_query = 'SELECT ' \
                    'users.id, ' \
                    'COUNT(*) ' \
                    'FROM users ' \
                    'INNER JOIN matches_history ' \
                    'ON users.id == matches_history.participant1 OR users.id == matches_history.participant2 ' \
                    'WHERE users.server_id == ?' \
                    'GROUP BY users.id'
# Returns [[user.id, bet_total_sum], ...]
bet_total_query = 'SELECT ' \
                  'users.id, ' \
                  'SUM(bets_history.amount) ' \
                  'FROM users ' \
                  'INNER JOIN bets_history ' \
                  'ON users.id == bets_history.better_id ' \
                  'WHERE users.server_id = ? ' \
                  'GROUP BY users.id'
# Returns [[user.id, count_bet_wins, count_bet_loses, bet_winrate], ...]
bet_winrate_query = 'SELECT ' \
                    'users.id, ' \
                    'SUM(bets.is_win) as "Total wins", ' \
                    'SUM(bets.is_lose) as "Total loses", ' \
                    '((SUM(bets.is_win)/(sum(bets.is_win)+sum(bets.is_lose)))*100) as "Bet winrate" ' \
                    'FROM (SELECT ' \
                    'bets_history.*, ' \
                    'CASE WHEN bets_history.participant1 == bets_history.winner_id THEN 1 ELSE 0 END as is_win, ' \
                    'CASE WHEN bets_history.participant1 == bets_history.winner_id THEN 0 ELSE 1 END as is_lose ' \
                    'FROM bets_history) as bets ' \
                    'INNER JOIN users ' \
                    'ON users.id == bets.better_id ' \
                    'WHERE users.server_id == ? ' \
                    'GROUP BY users.id'
# Returns [[seasons.player_id, total_marble_change], ...]
season_query = "SELECT " \
               "seasons.player_id, " \
               "SUM(marble_change) as change_total " \
               "FROM seasons " \
               "WHERE seasons.server_id == ? " \
               "GROUP BY seasons.player_id " \
               "ORDER BY change_total DESC"


class StatsCog(commands.Cog, name='Stats'):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='match_count')
    @commands.guild_only()
    async def match_count(self, ctx: commands.Context):
        results = db_op.raw_query(DbHandler.db_cnc, match_count_query, [126914954384244736])
        print(results)

    @commands.command(name='wins', aliases=['loses', 'winrate'], help='Prints a players wins/stats')
    @commands.guild_only()
    async def wins(self, ctx: commands.Context, member: Union[discord.Member, str] = None):
        """Prints a users wins, loses, and winrate

        Examples:
            - `$wins @Sophia`
            - `$wins`

        **Arguments**

        - `<ctx>` The context used to send confirmations.
        - `<member>` The user who's data you want to print. If omitted will defaults to your own data.

        """
        logging.debug(f'wins: {member}')

        # Check if member is None, use ctx.author if None
        if member is None:
            account = acc.get_account(ctx, DbHandler.db_cnc, ctx.author)
        else:
            account = acc.get_account(ctx, DbHandler.db_cnc, member)
        logger.debug(f'account: {account}')

        # Set winrate to 0 if wins is zero, otherwise calculate winrate
        if account.wins == 0:
            player_winrate = 0
        else:
            player_winrate = 100 * (account.wins / (account.wins + account.loses))

        await du.code_message(ctx, f'{account.nickname}\n'
                                   f'Wins: {account.wins}'
                                   f'\nLoses: {account.loses}'
                                   f'\nWinrate: {player_winrate:.2f}%')

    @commands.command(name='leaderboard',
                      help=f'Will list top 10 players by '
                           f'stat[{", ".join(stats for stats in (account_stats + non_account_stats))}], '
                           f'or give position of member on leaderboard')
    @commands.guild_only()
    async def leaderboard(self, ctx: commands.Context, stat: str, members: Union[discord.Member, str] = None):
        """Lists top 10 players by winrate, or a specific users position on leaderboard

        Examples:
            - `$leaderboard winrate @Sophia`
            - `$leaderboard`
            - `$leaderboard wins`

        **Arguments**

        - `<ctx>` The context used to send confirmations.
        - `<stat>` String of stat to get
        - `<members>` The member who's position on leaderboard you'd like to receive.

        """
        logger.debug(f'leaderboard: {members}')
        member_account = None

        # Check if stat is valid
        if not stat in (account_stats + non_account_stats):
            logger.debug(f'Invalid stat passed {stat}')
            await du.code_message(ctx, f'Unsupported stat, use list_stat for a list of valid stats', 3)
            await ctx.send_help('leaderboard')
            await ctx.send_help('list_stats')
            return

        # List containing information to display on page
        page_text_list = []

        # Active used to start while_loop
        active = True

        # Get member account, set active to false. Don't loop when members is passed
        if members:
            member_account = acc.get_account(ctx, DbHandler.db_cnc, members)
            active = False
            logger.debug(f'member_account: {member_account}')

        # if stat not easily able to be gotten from account, switch to doing manual queries for information
        if stat not in account_stats:
            if stat == 'match_count' or stat == 'bet_total':
                # Preform query
                if stat == 'bet_total':
                    query_results = db_op.raw_query(DbHandler.db_cnc, bet_total_query, [ctx.guild.id])
                else:
                    query_results = db_op.raw_query(DbHandler.db_cnc, match_count_query, [ctx.guild.id])
                # Sort query, and set index to 0
                sorted_list = sorted(query_results, key=lambda x: x[1], reverse=True)
                index = 0
                # Loop through sorted_list, and append lines to page_text_list for each index
                for results in sorted_list:
                    con_string = ''
                    index += 1
                    # If member is supplied only append index if member is in it
                    if member_account:
                        if results[0] != member_account.id:
                            continue
                        else:
                            # Build string for command when ran by member
                            con_string += f"{member_account.nickname}'s rank " \
                                          f"#{index} in {stat} with {results[1]}"
                            page_text_list.append(con_string)
                            continue

                    # Get account of user to use nickname
                    player_account = acc.get_account_from_db(ctx, DbHandler.db_cnc, results[0])
                    con_string += f"#{index} {player_account.nickname}: {results[1]}\n"
                    page_text_list.append(con_string)
                logger.debug(f'Exited match_count/bet_total for loop')
            elif stat == 'bet_winrate':
                # Preform query
                query_results = db_op.raw_query(DbHandler.db_cnc, bet_winrate_query, [ctx.guild.id])
                # Sort query, and set index to 0
                sorted_list = sorted(query_results, key=lambda x: x[3], reverse=True)
                index = 0
                # Loop through sorted_list, and append lines to page_text_list for each index
                for results in sorted_list:
                    con_string = ''
                    index += 1
                    # Get winrate to double check value
                    if not results[3]:
                        winrate = 0
                    else:
                        winrate = results[3]
                    # If member is supplied only append index if member is in it
                    if member_account:
                        if results[0] != member_account.id:
                            continue
                        else:
                            # Build string for command when ran by member
                            con_string += f"{member_account.nickname}'s rank " \
                                          f"#{index} in {stat} with {winrate}"
                            page_text_list.append(con_string)
                            continue

                    # Get account of user to use nickname
                    player_account = acc.get_account_from_db(ctx, DbHandler.db_cnc, results[0])
                    con_string += f"#{index} {player_account.nickname}: {winrate}\n"
                    page_text_list.append(con_string)
                logger.debug(f'Exited bet_winrate for loop')
            elif stat == 'season':
                # Preform query
                query_results = db_op.raw_query(DbHandler.db_cnc, season_query, [ctx.guild.id])
                index = 0
                # Loop through sorted_list, and append lines to page_text_list for each index
                for results in query_results:
                    con_string = ''
                    index += 1
                    # If member is supplied only append index if member is in it
                    if member_account:
                        if results[0] != member_account.id:
                            continue
                        else:
                            # Build string for command when ran by member
                            con_string += f"{member_account.nickname}'s rank " \
                                          f"#{index} in {stat} with {results[1]}"
                            page_text_list.append(con_string)
                            continue

                    # Get account of user to use nickname
                    player_account = acc.get_account_from_db(ctx, DbHandler.db_cnc, results[0])
                    con_string += f"#{index} {player_account.nickname}: {results[1]}\n"
                    page_text_list.append(con_string)
                logger.debug(f'Exited season for loop')

        else:
            # Get accounts of all users on server
            player_info = acc.get_account_server_all(ctx, DbHandler.db_cnc, ctx.guild.id)

            # Creation function to get stats based on string
            stat_get = operator.attrgetter(stat)

            # Create players list and fill with sorted player_info
            players = []
            players = sorted(player_info, key=stat_get, reverse=True)

            # If member_account filled, concate strings for member
            if member_account:
                for player in players:
                    if player.id == member_account.id:
                        if stat == 'winrate':
                            con_string = f"{member_account.nickname}'s rank #{players.index(player) + 1}, " \
                                         f"with a {stat} of {stat_get(player):.2f}%"
                        else:
                            con_string = f"{member_account.nickname}'s rank " \
                                         f"#{players.index(player) + 1}, with {stat_get(player)}"
                        page_text_list.append(con_string)
                        return
                return

            index = 0

            for player in players:
                con_string = ''
                if stat == 'winrate':
                    con_string += f'#{players.index(player) + 1} {player.nickname}: {stat_get(player):.2f}%\n'
                else:
                    con_string += f'#{players.index(player) + 1} {player.nickname}: {int(stat_get(player))}\n'

                page_text_list.append(con_string)

                index += 1

        # Check that page_text_list has been propagated, exit if not with error
        if not len(page_text_list):
            logger.debug(f'No {stat} stats to display to user')
            await ctx.send(f'No {stat} to display')
            return

        # Only add leaderboard header when member is not
        message_test = ''
        if not member_account:
            message_test = f'Leaderboard: {stat}\n\n'
        message_test += ''.join(line for line in page_text_list[0:10])

        message = await du.code_message(ctx, message_test)

        # pages = page_text_list / 10 # 10 indexes per page
        pages = math.ceil(len(page_text_list)/10)
        # current page is pages - 1 # Last page
        cur_page = pages - 1

        # if more than one page, add navigation reactions
        if pages > 1:
            await message.add_reaction('\U00002B05')
            await message.add_reaction('\U000027A1')
        else:
            active = False

        # Function to check if reaction = ctx.author
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['\U00002B05', '\U000027A1']

        # loop for reaction controls
        while active:
            try:
                # Set page to start of codeblock
                page = f'```Leaderboard: {stat}\n\n'
                # wait till we get a reaction, fill reaction, user with output of 'reaction_add'
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)
                # Check if reaction is left, and cur_page greater than zero
                if str(reaction.emoji) == '\U00002B05' and cur_page > 0:  # ⬅️
                    # Set cur_page to current value minus one
                    cur_page -= 1

                    # Generate current page with cur_page
                    for i in range(cur_page * 10, cur_page * 10 + 10):
                        page += page_text_list[i]

                    # Append page counter and edit message with page
                    page += f'Page {cur_page + 1} of {pages}\n```'
                    await message.edit(content=page)
                    # Remove user reaction
                    await message.remove_reaction(reaction, user)
                # Check if reaction is right, and cur_page less than pages-1
                elif str(reaction.emoji) == '\U000027A1' and cur_page < pages - 1:  # ➡️
                    # Set cur_page to current value plus one
                    cur_page += 1

                    # Generate current page with cur_page
                    for i in range(cur_page * 10, cur_page * 10 + 10):
                        if i < len(page_text_list):
                            page += page_text_list[i]

                    # Append page counter and edit message with page
                    page += f'Page {cur_page + 1} of {pages}\n```'
                    await message.edit(content=page)
                    # Remove user reaction
                    await message.remove_reaction(reaction, user)
                else:
                    await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                # When 'reaction_add' gets a timeout, set active to false to end loop
                active = False
                # Get cached message to remove all reactions
                cached_msg = discord.utils.get(self.bot.cached_messages, id=message.id)
                for reactions in cached_msg.reactions:
                    await reactions.remove(self.bot.user)


def setup(bot):
    bot.add_cog(StatsCog(bot))
