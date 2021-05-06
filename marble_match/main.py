import configparser
import logging.config
import sys

import discord
import database.database_operation as do
import database.database as db

from discord.ext import commands


logger = logging.getLogger('marble_match')
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('log.log')
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.ERROR)
logger.addHandler(stream_handler)
formatter = logging.Formatter('%(asctime)s : %(module)s : %(levelname)s : %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

logger.error('Ran')

extensions_list = ['setup', 'match', 'bet_control', 'stats', 'economy', 'history']

config = configparser.ConfigParser()
config.read('marble_bot.ini')

token = config['DEFAULT']['discord_token']

db.create_tables(db.DbHandler.db_cnc)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents, description='Manages Marble Matches')

for extension in extensions_list:
    try:
        bot.load_extension(f'cogs.{extension}')
    except Exception as e:
        exc = '{}: {}'.format(type(e).__name__, e)
        print('Failed to load extension {}\n{}'.format(extension, exc))

for cog in bot.cogs:
    print(cog)

bot.run(token)
