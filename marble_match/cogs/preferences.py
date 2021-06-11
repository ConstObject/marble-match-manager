import logging
from typing import Union
from configparser import ConfigParser

import discord
from discord.ext import commands

from database.database_setup import DbHandler
import utils.account as acc
import utils.discord_utils as du
import cogs.debug as debug

logger = logging.getLogger(f'marble_match.{__name__}')


class PrefCog(commands.Cog, name='Preferences'):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='nick', help='Change your nickname')
    @commands.guild_only()
    async def nick(self, ctx: commands.Context, nickname: str):
        logger.debug(f'nick: {nickname}')

        # Check if nickname is empty
        if not nickname.strip():
            await ctx.send('Nickname cannot be empty')
            return
        # Check if nickname contains whitespace
        if " " in nickname:
            await ctx.send('Nickname cannot contain whitespace')
            return

        account = acc.get_account(ctx, DbHandler.db_cnc, ctx.author)

        account.nickname = nickname
        await ctx.send(f'New nickname: "{account.nickname}"')

    @commands.command(name='color_role_cost', description='Sets the price of color roles')
    @commands.has_role('Admin')
    @commands.guild_only()
    async def color_role_cost(self, ctx: commands.Context, cost: int):
        logger.debug(f'color_role_cost: {int}')

        # Check if cost is not zero or negative
        if cost < 1:
            logger.debug(f'Tried to set cost to zero or negative')
            await du.code_message(ctx, 'Cost cannot be zero or negative', 3)
            return

        # Get ConfigParser to set new value
        config = ConfigParser()
        config.read('marble_bot.ini')

        # Set value to new value
        config.set(str(ctx.guild.id), 'color_role_cost', f'{cost}')

        # Write file
        with open('marble_bot.ini', 'w') as config_file:
            config.write(config_file)

        await du.code_message(ctx, f'Cost of colored roles changed to {cost}', 1)

    @commands.command(name='print_cogs', description='Prints cogs')
    @commands.check(debug.is_soph)
    @commands.guild_only()
    async def print_cogs(self, ctx: commands.Context):
        logger.debug(f'print_cogs')

        # Get ConfigParser to set new value
        config = ConfigParser()
        config.read('marble_bot.ini')

        cogs = config['DEFAULT']['cogs']
        await du.code_message(ctx, f'Cogs: {cogs}')

    @commands.command(name='write_cogs', description='Writes to cogs')
    @commands.check(debug.is_soph)
    @commands.guild_only()
    async def write_cogs(self, ctx: commands.Context, to_write: str):
        logger.debug(f'write_cogs: {to_write}')

        # Get ConfigParser to set new value
        config = ConfigParser()
        config.read('marble_bot.ini')

        # Set value to new value
        config.set('DEFAULT', 'cogs', to_write)

        # Write file
        with open('marble_bot.ini', 'w') as config_file:
            config.write(config_file)

        await du.code_message(ctx, f'Updated config file with new cogs', 1)

    @commands.command(name='print_tracked_stats', description='Prints tracked stats')
    @commands.check(debug.is_soph)
    @commands.guild_only()
    async def print_tracked_stats(self, ctx: commands.Context):
        logger.debug(f'print_tracked_stats')

        # Get ConfigParser to set new value
        config = ConfigParser()
        config.read('marble_bot.ini')

        tracked_stats = config[str(ctx.guild.id)]['tracked_stats']
        if not tracked_stats:
            await du.code_message(ctx, 'No stats tracked', 3)
            return
        else:
            await du.code_message(ctx, f'Tracked stats: {tracked_stats}')

    @commands.command(name='write_tracked_stats', description='Writes to tracked stats')
    @commands.check(debug.is_soph)
    @commands.guild_only()
    async def write_tracked_stats(self, ctx: commands.Context, to_write: str):
        logger.debug(f'write_tracked_stats: {to_write}')

        # Get ConfigParser to set new value
        config = ConfigParser()
        config.read('marble_bot.ini')

        # Set value to new value
        config.set(str(ctx.guild.id), 'tracked_stats', to_write)

        # Write file
        with open('marble_bot.ini', 'w') as config_file:
            config.write(config_file)

        await du.code_message(ctx, f'Updated config file with new tracked_stats', 1)

    @commands.command(name='update_season_number', description='Writes to season with a new value')
    @commands.check(debug.is_soph)
    @commands.guild_only()
    async def update_season_number(self, ctx: commands.Context, to_write: str):
        logger.debug(f'update_season_number: {to_write}')

        # Get ConfigParser to set new value
        config = ConfigParser()
        config.read('marble_bot.ini')

        # Set value to new value
        config.set(str(ctx.guild.id), 'season', to_write)

        # Write file
        with open('marble_bot.ini', 'w') as config_file:
            config.write(config_file)

        await du.code_message(ctx, f'Updated config file with new season number', 1)

    @commands.command(name='update_season_active', description='Writes to season_active with a new value')
    @commands.check(debug.is_soph)
    @commands.guild_only()
    async def update_season_active(self, ctx: commands.Context, to_write: bool):
        logger.debug(f'update_season_active: {to_write}')

        # Get ConfigParser to set new value
        config = ConfigParser()
        config.read('marble_bot.ini')

        # Set value to new value
        config.set(str(ctx.guild.id), 'season_active', '1' if to_write else '0')

        # Write file
        with open('marble_bot.ini', 'w') as config_file:
            config.write(config_file)

        await du.code_message(ctx, f'Updated config file with new season_active', 1)


def setup(bot):
    bot.add_cog(PrefCog(bot))
