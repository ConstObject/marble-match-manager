import configparser
import logging.config
import sys
import traceback

import discord
from discord.ext import commands

import database.database_setup as db
import utils.scheduled as schedules
import utils.exception as exception
import utils.discord_utils as du


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

config = configparser.ConfigParser()
config.read('marble_bot.ini')

extensions_list = config['DEFAULT']['cogs'].split(',')

token = config['DEFAULT']['discord_token']

db.create_tables(db.DbHandler.db_cnc)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents, description='Manages Marble Matches')

for extension in extensions_list:
    try:
        bot.load_extension(f'cogs.{extension}')
        print(f'Loaded {extension}')
    except Exception as e:
        exc = '{}: {}'.format(type(e).__name__, e)
        print('Failed to load extension {}\n{}'.format(extension, exc))

# schedules.start_scheduler()


def update_ini(server_id: str):
    if not config.has_section(server_id):
        config.add_section(server_id)
        config.set(server_id, 'default_marbles', '10')
        config.set(server_id, 'tracked_stats', '')
        config.set(server_id, 'color_role_cost', '20')

    with open('marble_bot.ini', 'w') as config_file:
        config.write(config_file)


@bot.event
async def on_command_error(ctx, error):
    """The event triggered when an error is raised while invoking a command.

    Parameters
    ------------
    ctx: commands.Context
        The context used for command invocation.
    error: commands.CommandError
        The Exception raised.
    """

    # This prevents any commands with local handlers being handled here in on_command_error.
    if hasattr(ctx.command, 'on_error'):
        return

    # This prevents any cogs with an overwritten cog_command_error being handled here.
    cog = ctx.cog
    if cog:
        if cog._get_overridden_method(cog.cog_command_error) is not None:
            return

    ignored = (commands.CommandNotFound, )

    # Allows us to check for original exceptions raised and sent to CommandInvokeError.
    # If nothing is found. We keep the exception passed to on_command_error.
    error = getattr(error, 'original', error)

    # Anything in ignored will return and prevent anything happening.
    if isinstance(error, ignored):
        return

    if isinstance(error, commands.DisabledCommand):
        await du.code_message(ctx, f'{ctx.command} has been disabled.')

    elif isinstance(error, commands.NoPrivateMessage):
        try:
            await du.code_message(ctx, f'{ctx.command} can not be used in Private Messages.')
        except discord.HTTPException:
            pass

    elif isinstance(error, commands.MissingPermissions):
        await du.code_message(ctx, f"You're don't have permission for this. Missing perms [{error.missing_perms}]")

    elif isinstance(error, commands.BotMissingPermissions):
        await du.code_message(ctx, f"Bot doesn't have permissions for this. Missing perms [{error.missing_perms}]")

    elif isinstance(error, commands.MissingRequiredArgument):
        await du.code_message(ctx, f"You're missing a required argument: {error.param}")
        await ctx.send_help(ctx.command.name)

    # Check if it's a custom exception
    elif isinstance(error, exception.UnableToRead):
        await du.code_message(ctx, f'Error reading {error.attribute}', 3)
    elif isinstance(error, exception.UnableToWrite):
        await du.code_message(ctx, f"Error writing {error.attribute}", 3)
    elif isinstance(error, exception.UnableToDelete):
        await du.code_message(ctx, f"Error deleting {error.attribute}", 3)
    elif isinstance(error, exception.UnexpectedEmpty):
        await du.code_message(ctx, f"Error unexpected empty {error.attribute}", 3)
    elif isinstance(error, exception.UnexpectedValue):
        await du.code_message(ctx, f"Unexpected value, {error.attribute}", 3)
    elif isinstance(error, exception.InvalidNickname):
        await du.code_message(ctx, error.message, 3)

    else:
        # All other Errors not returned come here. And we can just print the default TraceBack.
        logger.error('Ignoring exception in command {}:'.format(ctx.command))
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


@bot.event
async def on_ready():
    print(f'Bot connected.')

    for server in bot.guilds:
        update_ini(str(server.id))

bot.run(token)
