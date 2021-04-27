import os

import discord
import database

from discord.ext import commands
from dotenv import load_dotenv

extensions_list = ['setup', 'match', 'bet_control', 'stats', 'economy', 'history']

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

for extension in extensions_list:
    try:
        bot.load_extension(extension)
    except Exception as e:
        exc = '{}: {}'.format(type(e).__name__, e)
        print('Failed to load extension {}\n{}'.format(extension, exc))

for cog in bot.cogs:
    print(cog)

bot.run(token)
