import datetime
import logging
from datetime import datetime
from typing import Union
from configparser import ConfigParser

import discord
from discord.ext import commands

from database.database_setup import DbHandler
import database.database_operation as do
import utils.discord_utils as du
import cogs.debug as debug
import utils.ranked as ranked


logger = logging.getLogger(f'marble_match.{__name__}')


class RankedCog(commands.Cog, name='Ranked'):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='current_season', help='Prints current season information')
    @commands.guild_only()
    async def current_season_func(self, ctx: commands.Context):
        logger.debug(f'current_season_func')

        query = "SELECT * FROM season_list " \
                "WHERE server_id == ? AND season_number == ?"
        query_param = [ctx.guild.id, ranked.current_season(ctx.guild.id)]

        # Check if there is a currently active season and it's valid
        # Check if a season is already active
        if not ranked.is_season_active(ctx.guild.id):
            await du.code_message(ctx, 'There is no active season', 3)
            return
        season_number = ranked.current_season(ctx.guild.id)
        if not season_number:
            await du.code_message(ctx, 'Cannot display season 0, please start a season to display information', 3)
            return

        results = do.raw_query(DbHandler.db_cnc, query, query_param)[0]

        if not results:
            await du.code_message(ctx, 'Unable to get current season information', 3)
            return

        await du.code_message(ctx, f"Season {results[2]}\n"
                                   f"Season start: {results[3].strftime('%Y/%m/%d')}\n"
                                   f"Season end: {results[4].strftime('%Y/%m/%d')}\n")

    @commands.command(name='list_seasons', help='Prints seasons list with information')
    @commands.guild_only()
    async def list_season_func(self, ctx: commands.Context):
        logger.debug(f'list_season_func')

        query = "SELECT * FROM season_list " \
                "WHERE server_id == ? " \
                "ORDER BY season_number"
        query_param = [ctx.guild.id]

        results = do.raw_query(DbHandler.db_cnc, query, query_param)

        if not results:
            await du.code_message(ctx, 'No seasons to display')
            return

        display_text = ['Seasons\n']

        for index in results:
            display_text.append(f"Season {index[2]}: "
                                f"{index[3].strftime('%Y/%m/%d')} - {index[4].strftime('%Y/%m/%d')}\n")

        await du.code_message(ctx, "".join(item for item in display_text))

    @commands.command(name='start_season', help='Starts a ranked season YYYY-MM-DD')
    @commands.check(debug.is_soph)
    @commands.guild_only()
    async def start_season(self, ctx: commands.Context, end_time: str):
        logger.debug(f'start_season: {end_time}')

        # Get time from string and shift it to work with GMT-0 to EST
        datetime_from_str = datetime.strptime(end_time, "%Y-%m-%d")
        datetime_end_time = datetime_from_str.replace(hour=5)

        print(datetime_end_time)
        # Check if a season is already active
        if ranked.is_season_active(ctx.guild.id):
            await du.code_message(ctx, 'There is already an active season, please end that season to start a new one')
            return
        # Get current season to then start next season as that +1
        cur_season_num = ranked.current_season(ctx.guild.id)
        cur_season_num += 1
        # Create season_list entry for the current season
        ranked.create_season_list_entry(DbHandler.db_cnc, ctx.guild.id, cur_season_num, datetime.utcnow(),
                                        datetime_end_time)
        # Write season_active and season
        # Get ConfigParser to set new value
        config = ConfigParser()
        config.read('marble_bot.ini')

        # Set value to new value
        config.set(str(ctx.guild.id), 'season', str(cur_season_num))
        config.set(str(ctx.guild.id), 'season_active', '1')

        # Write file
        with open('marble_bot.ini', 'w') as config_file:
            config.write(config_file)

        # Return message
        await du.code_message(ctx, f'New season started, now season {cur_season_num}', 1)

    @commands.command(name='end_season', help='Ends a ranked season')
    @commands.check(debug.is_soph)
    @commands.guild_only()
    async def end_season(self, ctx: commands.Context):
        logger.debug(f'end_season')

        # Check if season is not active
        if not ranked.is_season_active(ctx.guild.id):
            await du.code_message(ctx, 'No active season to end', 3)
            return
        # Check if season number is not zero
        season_number = ranked.current_season(ctx.guild.id)
        if not season_number:
            await du.code_message(ctx, 'Cannot end season 0, must have started a season to end', 3)
            return

        ranked.update_season_list_end_time(DbHandler.db_cnc, ctx.guild.id, season_number, datetime.utcnow())

        # Write season_active
        # Get ConfigParser to set new value
        config = ConfigParser()
        config.read('marble_bot.ini')

        # Set value to new value
        config.set(str(ctx.guild.id), 'season_active', '0')

        # Write file
        with open('marble_bot.ini', 'w') as config_file:
            config.write(config_file)

        await du.code_message(ctx, f"Ended season {season_number}, you're now free to start a new season.", 1)


def setup(bot):
    bot.add_cog((RankedCog(bot)))
