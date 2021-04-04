import discord
import database
import database_operation
from discord.ext import commands


class InitCog(commands.Cog, name='Initializations'):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.bot.user.name} has connected to Discord.')
        await self.bot.change_presence(activity=discord.Game(name='$help'))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if database_operation.get_player_id(database.db_connection, str(member), member.guild.id) is None:
            database_operation.create_user(database.db_connection, None, str(member), 10, member.guild.id)
            print(f'Added {member.name} to database')

    @commands.command(name='init', help='Adds all server members to the database if they do not exist already')
    @commands.guild_only()
    @commands.has_role('Admin')
    async def init(self, ctx):
        for members in ctx.guild.members:
            if database_operation.get_player_id(database.db_connection, str(members), ctx.guild.id) is None:
                database_operation.create_user(database.db_connection, None, str(members), 10, ctx.guild.id)
                print(f'Added {members.name} to database')
        await ctx.send('Any members not added to the database have been added')
