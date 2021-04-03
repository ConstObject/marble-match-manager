import os
import discord
import database
import database_operation

from discord.ext import commands
from dotenv import load_dotenv


db_connection = database.create_connection('database.db')
database.create_tables(db_connection)

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents)


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord.')
    await bot.change_presence(activity=discord.Game(name='$help'))


@bot.event
async def on_member_join(member):
    if database_operation.get_player_id(db_connection, str(member), member.guild.id) is None:
        database_operation.create_user(db_connection, None, str(member), 10, member.guild.id)
        print(f'Added {member.name} to database')


@bot.event
async def on_command_error(ctx, error):
    await ctx.send(error)

# region Initialization of database


@bot.event
async def on_guild_join(guild):
    for members in guild.members:
        if database_operation.get_player_id(db_connection, str(members), guild.id) is None:
            database_operation.create_user(db_connection, None, str(members), 10, guild.id)
            print(f'Added {members.name} to database')


@bot.command(name='init', help='Adds all server members to the database if they do not exist already')
@commands.has_role('Admin')
async def init(ctx):
    for members in ctx.guild.members:
        if database_operation.get_player_id(db_connection, str(members), ctx.guild.id) is None:
            database_operation.create_user(db_connection, None, str(members), 10, ctx.guild.id)
            print(f'Added {members.name} to database')
    await ctx.send('Any members not added to the database have been added')

# endregion

# region Match Controls


@bot.command(name='match', help='Challenge a user to a marble match, for all the marbles')
async def match(ctx, member: discord.Member, marbles: int):
    if ctx.author == member:
        await ctx.send('You\'re a terrible person who made Soph have to program this.')
        return

    if marbles > 0:
        await ctx.send('You\'re a terrible person who made Soph have to program this.')
        return

    challenger = database_operation.get_player_id(db_connection, str(ctx.author), ctx.guild.id)
    recipient = database_operation.get_player_id(db_connection, str(member), ctx.guild.id)

    if database_operation.find_match_by_player_id(db_connection, challenger[0]) != 0:
        await ctx.send('You already have an match going')
        return

    if database_operation.find_match_by_player_id(db_connection, recipient[0]) != 0:
        await ctx.send('They already have a match going')
        return

    challenger_marbles = database_operation.get_marble_count(db_connection, challenger[0])
    if challenger_marbles < marbles:
        await ctx.send('You do not have enough marbles for this match')
        return

    recipient_marbles = database_operation.get_marble_count(db_connection, recipient[0])
    if recipient_marbles < marbles:
        await ctx.send('They do not have enough marbles for this match')
        return

    match_id = database_operation.create_match(db_connection, None, marbles, 0, challenger[0], recipient[0])

    await ctx.send(f'{ctx.author.display_name} challenged {member.display_name} to a marble match for {str(marbles)} '
                   f'marbles'
                   f'\nType \'$accept\' to accept their challenge.'
                   f'\nType \'$close\' to decline the challenge.'
                   f'\nMatch ID: {str(match_id)}')


@bot.command(name='accept', help='Accept a challenge')
async def accept(ctx):
    player_id = database_operation.get_player_id(db_connection, str(ctx.author), ctx.guild.id)[0]
    match_id = database_operation.find_match_by_player_id(db_connection, player_id)

    if match_id == 0:
        await ctx.send('You don\'t have a match to accept')
        return

    database_operation.update_match_accepted(db_connection, match_id)
    await ctx.send(f'Match {match_id} accepted, now open for betting.'
                   f'\nType \'$start\' to close the betting and start the match')


@bot.command(name='start', help='Start the match and close betting')
async def match_start(ctx):
    player_id = database_operation.get_player_id(db_connection, str(ctx.author), ctx.guild.id)[0]
    match_id = database_operation.find_match_by_player_id(db_connection, player_id)

    if match_id == 0:
        await ctx.send('You don\'t have a match to start')
        return

    database_operation.update_match_activity(db_connection, match_id)
    await ctx.send(f'Match {match_id} started, betting is closed and all bets are locked in.')


@bot.command(name='winner', help='Selects the winner of a marble match, and transfers marbles')
async def match_win(ctx, member: discord.Member):
    winner_id = database_operation.get_player_id(db_connection, str(member), ctx.guild.id)[0]
    match_id = database_operation.find_match_by_player_id(db_connection, winner_id)

    if match_id == 0:
        await ctx.send('They have no active match')
        return

    match_info = database_operation.get_match_info_by_id(db_connection, match_id)

    if winner_id == match_info[3]:
        loser_id = match_info[4]
    else:
        loser_id = match_info[3]

    database_operation.transfer_marbles(db_connection, loser_id, winner_id, match_info[1])

    database_operation.add_player_win(db_connection, winner_id, 1)
    database_operation.add_player_loses(db_connection, loser_id, 1)

    database_operation.delete_match(db_connection, match_id)

    await ctx.send(f'{member.display_name} is the winner, gaining a total of {match_info[1]} marbles!')


@bot.command(name='current', help='Lists info about you\'re current match')
async def current(ctx):
    player_id = database_operation.get_player_id(db_connection, str(ctx.author), ctx.guild.id)[0]
    match_id = database_operation.find_match_by_player_id(db_connection, player_id)

    if match_id == 0:
        await ctx.send('No current match')
        return

    match_info = database_operation.get_match_info_by_id(db_connection, match_id)

    player_info1 = database_operation.get_player_info(db_connection, match_info[3])
    player_info2 = database_operation.get_player_info(db_connection, match_info[4])

    print(player_info1)
    print(player_info2)

    await ctx.send(f'Match between {player_info1[1]} and {player_info2[1]} for {match_info[1]} marbles'
                   f'\nMatch ID: {match_id}')


@bot.command(name='close', help='Closes your pending match, if it has not been started')
async def close_current_match(ctx):
    player_id = database_operation.get_player_id(db_connection, str(ctx.author), ctx.guild.id)[0]
    match_id = database_operation.find_match_by_player_id(db_connection, player_id)

    database_operation.delete_match(db_connection, match_id)
    await ctx.send(f'Closed match {match_id}.')

# endregion

# region Wins/loses


@bot.command(name='wins', help='Prints a players wins')
async def wins(ctx, member: discord.Member):
    player_id = database_operation.get_player_id(db_connection, str(member), ctx.guild.id)[0]
    player_wins = database_operation.get_player_wins(db_connection, player_id)
    player_loses = database_operation.get_player_loses(db_connection, player_id)

    if player_wins == 0:
        player_winrate = 0
    else:
        player_winrate = 100 * (player_wins/(player_wins+player_loses))

    await ctx.send(f'Wins: {player_wins}.'
                   f'\nLoses: {player_loses}.'
                   f'\nWinrate: {player_winrate}%')


@bot.command(name='loses', help='Prints a players wins')
async def wins(ctx, member: discord.Member):
    player_id = database_operation.get_player_id(db_connection, str(member), ctx.guild.id)[0]
    player_wins = database_operation.get_player_wins(db_connection, player_id)
    player_loses = database_operation.get_player_loses(db_connection, player_id)

    if player_wins == 0:
        player_winrate = 0
    else:
        player_winrate = 100 * (player_wins / (player_wins + player_loses))

    await ctx.send(f'Loses: {player_loses}.'
                   f'\nWins: {player_wins}.'
                   f'\nWinrate: {player_winrate}%')

# endregion

# region Marble Management Commands


@bot.command(name='set_marbles', help='Will set the users marble count to a new number')
@commands.has_role('Admin')
async def set_marbles(ctx, member: discord.Member, marbles: int):

    if marbles < 0:
        await ctx.send('You\'re a terrible person who made Soph have to program this.')
        return

    database_operation.update_marble_count(db_connection,
                                           database_operation.get_player_id(db_connection, str(member),
                                                                            ctx.guild.id)[0],
                                           marbles)
    await ctx.send(f'Set {member.display_name}\'s marbles to {str(marbles)}')


@bot.command(name='add_marbles', help='Will add to the users marble bank')
@commands.has_role('Admin')
async def add_marbles(ctx, member: discord.Member, marbles: int):

    if marbles < 0:
        await ctx.send('You\'re a terrible person who made Soph have to program this.')
        return

    player_id = database_operation.get_player_id(db_connection, str(member), ctx.guild.id)[0]
    old_marbles = database_operation.get_marble_count(db_connection, player_id)

    database_operation.add_marbles(db_connection, player_id, marbles)

    await ctx.send(f'{ctx.author.display_name} has added {str(marbles)} to {member.display_name}\'s bank.'
                   f'\nTheir new balance is {str(old_marbles+marbles)}!')


@bot.command(name='balance', help='Prints out your marble count')
async def balance(ctx):
    player_id = database_operation.get_player_id(db_connection, str(ctx.author), ctx.guild.id)[0]
    marbles = database_operation.get_marble_count(db_connection, player_id)

    await ctx.send(f'You have {str(marbles)} marbles.')


@bot.command(name='marbles', help='Prints their marble count')
async def balance2(ctx, member: discord.Member):
    player_id = database_operation.get_player_id(db_connection, str(member), ctx.guild.id)[0]
    marbles = database_operation.get_marble_count(db_connection, player_id)

    await ctx.send(f'They have {str(marbles)} marbles.')


@bot.command(name='transfer', help='Transfers marbles from your bank to theirs')
async def transfer(ctx, member: discord.Member, marbles: int):
    if ctx.author == member:
        await ctx.send('You\'re a terrible person who made Soph have to program this.')
        return

    if marbles < 0:
        await ctx.send('You\'re a terrible person who made Soph have to program this.')
        return

    player_id1 = database_operation.get_player_id(db_connection, str(ctx.author), ctx.guild.id)[0]
    player_id2 = database_operation.get_player_id(db_connection, str(member), ctx.guild.id)[0]
    player1_marbles = database_operation.get_marble_count(db_connection, player_id1)

    if player1_marbles < marbles:
        await ctx.send('You don\'t have enough marbles for this transaction')
        return

    player2_marbles = database_operation.get_marble_count(db_connection, player_id2)

    database_operation.transfer_marbles(db_connection, player_id1, player_id2, marbles)

    await ctx.send(f'Marbles transferred! Your new balances are:'
                   f'\n{ctx.author.display_name}: {str(player1_marbles-marbles)} marbles'
                   f'\n{member.display_name}: {str(player2_marbles+marbles)} marbles')

# endregion

bot.run(token)
