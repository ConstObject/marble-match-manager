import logging
from typing import Union

import discord
from discord.ext import commands
from cogs.debug import is_soph

import database.database_operation as database_operation
from database.database_setup import DbHandler
import utils.discord_utils as du
import utils.account as accounts
import utils.matches as matches
import utils.bets as bets

logger = logging.getLogger(f'marble_match.{__name__}')

""" Roles
0-5 - Custom can pick name and color
5-27 - Default discord colors
"""

color_role_list = ['Default',
                   'Teal', 'Dark Teal',
                   'Green', 'Dark Green',
                   'Blue', 'Dark Blue',
                   'Purple', 'Dark Purple',
                   'Magenta', 'Dark Magenta',
                   'Gold', 'Dark Gold',
                   'Orange', 'Dark Orange',
                   'Red', 'Dark Red',
                   'Dark Grey', 'Light Grey',
                   'Blurple', 'Greyple',
                   'Dark Theme']


class ServiceCog(commands.Cog, name='services'):

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @commands.command(name='create_color_roles')
    @commands.check(is_soph)
    @commands.guild_only()
    async def create_role(self, ctx: commands.Context):
        logger.debug(f'create_color_roles')
        guild: discord.guild.Guild = ctx.guild

        total_roles = await guild.fetch_roles()

        color_roles = []
        if not any(role.name == color_role_list[0] for role in total_roles):
            color_roles.append(await guild.create_role(name='Default', colour=discord.colour.Colour.default()))
        if not any(role.name == color_role_list[1] for role in total_roles):
            color_roles.append(await guild.create_role(name='Teal', colour=discord.colour.Colour.teal()))
        if not any(role.name == color_role_list[2] for role in total_roles):
            color_roles.append(await guild.create_role(name='Dark Teal', colour=discord.colour.Colour.dark_teal()))
        if not any(role.name == color_role_list[3] for role in total_roles):
            color_roles.append(await guild.create_role(name='Green', colour=discord.colour.Colour.green()))
        if not any(role.name == color_role_list[4] for role in total_roles):
            color_roles.append(await guild.create_role(name='Dark Green', colour=discord.colour.Colour.dark_green()))
        if not any(role.name == color_role_list[5] for role in total_roles):
            color_roles.append(await guild.create_role(name='Blue', colour=discord.colour.Colour.blue()))
        if not any(role.name == color_role_list[6] for role in total_roles):
            color_roles.append(await guild.create_role(name='Dark Blue', colour=discord.colour.Colour.dark_blue()))
        if not any(role.name == color_role_list[7] for role in total_roles):
            color_roles.append(await guild.create_role(name='Purple', colour=discord.colour.Colour.purple()))
        if not any(role.name == color_role_list[8] for role in total_roles):
            color_roles.append(await guild.create_role(name='Dark Purple', colour=discord.colour.Colour.dark_purple()))
        if not any(role.name == color_role_list[9] for role in total_roles):
            color_roles.append(await guild.create_role(name='Magenta', colour=discord.colour.Colour.magenta()))
        if not any(role.name == color_role_list[10] for role in total_roles):
            color_roles.append(await guild.create_role(name='Dark Magenta', colour=discord.colour.Colour.dark_magenta()))
        if not any(role.name == color_role_list[11] for role in total_roles):
            color_roles.append(await guild.create_role(name='Gold', colour=discord.colour.Colour.gold()))
        if not any(role.name == color_role_list[12] for role in total_roles):
            color_roles.append(await guild.create_role(name='Dark Gold', colour=discord.colour.Colour.dark_gold()))
        if not any(role.name == color_role_list[13] for role in total_roles):
            color_roles.append(await guild.create_role(name='Orange', colour=discord.colour.Colour.orange()))
        if not any(role.name == color_role_list[14] for role in total_roles):
            color_roles.append(await guild.create_role(name='Dark Grange', colour=discord.colour.Colour.dark_orange()))
        if not any(role.name == color_role_list[15] for role in total_roles):
            color_roles.append(await guild.create_role(name='Red',
                                                       colour=discord.colour.Colour.from_rgb(0xFF, 0x00, 0x00)))
        if not any(role.name == color_role_list[16] for role in total_roles):
            color_roles.append(await guild.create_role(name='Dark Red',
                                                       colour=discord.colour.Colour.from_rgb(0x8B, 0x00, 0x00)))
        if not any(role.name == color_role_list[17] for role in total_roles):
            color_roles.append(await guild.create_role(name='Dark Grey', colour=discord.colour.Colour.dark_grey()))
        if not any(role.name == color_role_list[18] for role in total_roles):
            color_roles.append(await guild.create_role(name='Light Grey', colour=discord.colour.Colour.light_grey()))
        if not any(role.name == color_role_list[19] for role in total_roles):
            color_roles.append(await guild.create_role(name='Blurple', colour=discord.colour.Colour.blurple()))
        if not any(role.name == color_role_list[20] for role in total_roles):
            color_roles.append(await guild.create_role(name='Greyple', colour=discord.colour.Colour.greyple()))
        if not any(role.name == color_role_list[21] for role in total_roles):
            color_roles.append(await guild.create_role(name='Dark Theme', colour=discord.colour.Colour.dark_theme()))

        color_roles.reverse()

        for role in color_roles:
            logger.debug(f'Added color roles: {role.name}')
            all_roles = await guild.fetch_roles()
            num_roles = len(all_roles)
            await role.edit(position=num_roles-2)

        await du.code_message(ctx, 'Created color roles!', 1)

    @create_role.error
    async def create_role_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            print(error)

    @commands.command(name='buy', description='Buy services and items with your marbles')
    @commands.guild_only()
    async def buy(self, ctx: commands.Context, item_group: str, specific_item: str):
        logger.debug(f'buy: {item_group}, {specific_item}')

        if item_group.lower() == 'color_role':
            logger.debug('Buying a role')
            if specific_item in color_role_list:
                logger.debug('Valid role')
                # Get ctx.author's account to check if they can purchase
                buyer_account = accounts.get_account(ctx, DbHandler.db_cnc, ctx.author)
                if buyer_account.marbles < 15:
                    logger.debug(f"User doesn't have enough marbles")
                    await du.code_message(ctx, f'You do not have enough marbles for this.\n'
                                               f'Balance: {buyer_account.marbles}\n'
                                               f'Cost: 15')
                    return
                guild: discord.Guild = ctx.guild
                bot_member: discord.Member = ctx.guild.me

                # Remove any previous color roles
                for role in ctx.author.roles:
                    if role.name in color_role_list:
                        logger.debug(f'Removed {role.name} from {ctx.author.display_name}')
                        await ctx.author.remove_roles(role, reason='Assigning new color role')

                buyer_account.marbles -= 15

                role = discord.utils.get(ctx.guild.roles, name=specific_item)
                member_roles = ctx.author.roles
                member_roles.append(role)
                await ctx.author.edit(roles=member_roles, reason='Bought a new role')

                await du.code_message(ctx, 'New Role Set')

            else:
                logger.debug(f'Invalid role: {specific_item}')
                await du.code_message(ctx, f'Invalid color_role')
                return

    @buy.error
    async def create_role_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            logger.debug(f'{error}')
            print(f'{error}')


def setup(bot: commands.Bot):
    bot.add_cog(ServiceCog(bot))
