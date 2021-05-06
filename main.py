import os
import configparser
import logging
import logging.config
import sys

import discord
import database.database as database

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

if __debug__:
    logger.setLevel(logging.ERROR)
    token = config['DEVELOP']['discord_dev_token']
    database.db_connection = database.create_connection(config['DEVELOP']['dev_database'])
else:
    token = config['DEFAULT']['discord_token']
    database.db_connection = database.create_connection(config['DEFAULT']['database'])

with open('marble_bot.ini', 'w') as config_file:
    config.write(config_file)

database.create_tables(database.db_connection)

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
