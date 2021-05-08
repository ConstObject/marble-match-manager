import discord
from discord.ext import commands

import database.database_operation as database_operation
from database.database_setup import DbHandler
import utils.account as acc
import utils.discord_utils as du


def has_database_permission():
    async def predicate(ctx: commands.Context):
        """Returns true if is me or has admin role

        **Arguments**

        - `<ctx>` Context to check.

        """

        return ctx.author.id == 126913881879740416 or commands.has_role('Admin')
    return commands.check(predicate)


class InitCog(commands.Cog, name='Initializations'):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.bot.user.name} has connected to Discord.')
        print(f'{self.bot.guilds}')
        await self.bot.change_presence(activity=discord.Game(name='$help'))

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not database_operation.get_player_id(DbHandler.db_cnc, str(member), member.guild.id):
            database_operation.create_user(DbHandler.db_cnc, None, str(member), 10, member.guild.id)
            print(f'Added {member.name} to database')

    @commands.command(name='init', help='Adds all server members to the database if they do not exist already')
    @commands.guild_only()
    @has_database_permission()
    async def init(self, ctx: commands.Context):
        """Adds server member to database if they do not exist in database

        Examples:
            - `$init`

        **Arguments**

        - `<ctx>` Context used to send confirmations.

        """

        for members in ctx.guild.members:
            if not du.get_id_by_member(ctx, DbHandler.db_cnc, members):
                database_operation.create_user(DbHandler.db_cnc, None, str(members), 10, ctx.guild.id)
                print(f'Added {members.name} to database')
        await du.code_message(ctx, 'Any members not added to the database have been added')


def setup(bot):
    bot.add_cog(InitCog(bot))
