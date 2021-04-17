import os
import discord
import database
import database_operation
import match
import setup
import bet_control
import stats
import economy

from discord.ext import commands
from discord_utils import code_message
from dotenv import load_dotenv

load_dotenv()
if __debug__:
    token = os.getenv('DISCORD_DEV_TOKEN')
    database.db_connection = database.create_connection('dev.db')
else:
    token = os.getenv('DISCORD_TOKEN')
    database.db_connection = database.create_connection('database.db')

database.create_tables(database.db_connection)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents, description='Manages Marble Matches')

bot.add_cog(setup.InitCog(bot))
bot.add_cog(match.MatchCog(bot))
bot.add_cog(bet_control.BetCog(bot))
bot.add_cog(stats.StatsCog(bot))
bot.add_cog(economy.EconCog(bot))

for cog in bot.cogs:
    print(cog)

bot.run(token)
