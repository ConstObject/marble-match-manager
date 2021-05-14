import asyncio
import datetime
import logging
from typing import Union
from datetime import datetime, timedelta

import discord
from discord.ext import commands

import database.database_operation as database_operation
from database.database_setup import DbHandler
import utils.discord_utils as du
import utils.account as acc
import utils.matches as ma
import utils.exception as exception
import utils.config.json_config as json_cfg

logger = logging.getLogger('marble_match.match')


class MatchCog(commands.Cog, name='Matches'):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def function1(self):
        raise exception.UnableToRead(attribute='test')

    @commands.command(name='match', help='Challenge a user to a marble match, for all the marbles')
    @commands.guild_only()
    async def match(self, ctx: commands.Context, member: Union[discord.Member, str], marbles: int,
                    game: str = 'melee', form: str = 'Bo3'):
        """Challenge a user to a marble match

        Examples:
            - `$match @Sophia 10`
            - `$match @Ness 1`

        **Arguments**

        - `<ctx>` The context used to send confirmations.
        - `<member>` The user you want to challenge to a marble match
        - `<marbles>` The amount of marbles for the match

        """
        logging.debug(f'match: {member}, {marbles}')

        # Check if marbles is less than one, gives a message to user and returns to exit
        if marbles < 1:
            logger.debug(f'{ctx.author} attempted to create a match with < 1 marbles')
            await du.code_message(ctx, 'You\'re a terrible person who made Soph have to program this.'
                                       '\n No negatives or zero', 3)
            return

        # Get and check if Account exists, gives a message to user and returns if no Account
        challenger = acc.get_account(ctx, DbHandler.db_cnc, ctx.author)
        if not challenger:
            logger.debug(f'Unable to get Account for {ctx.author}')
            await du.code_message(ctx, f'Unable to get {ctx.author.display_name}\'s account info', 3)
            return
        recipient = acc.get_account(ctx, DbHandler.db_cnc, member)
        if not recipient:
            logger.debug(f'Unable to get Account for {member}')
            await du.code_message(ctx, f'Unable to get {member.display_name}\'s account info', 3)
            return

        # Check if challenger and recipient are the same, gives a message to user and returns to exit
        if challenger.id == recipient.id:
            logger.debug(f'{ctx.author} passed themselves as member in match command')
            await du.code_message(ctx, 'You cannot challenge yourself to a match', 3)
            return

        # Checks if challenger has a match already going
        if database_operation.find_match_by_player_id(DbHandler.db_cnc, challenger.id):
            logger.debug(f'{ctx.author} attempted to start a match with one already made')
            await du.code_message(ctx, 'You already have an match going', 3)
            return
        # Checks if recipient has a match already going
        if database_operation.find_match_by_player_id(DbHandler.db_cnc, recipient.id):
            logger.debug(f'{ctx.author}attempted to start a match while {recipient} has a match already')
            await du.code_message(ctx, 'They already have a match going')
            return

        # Checks if challenger/recipient has enough marbles to create a match
        if challenger.marbles < marbles:
            logger.debug(f'{ctx.author} does not have enough marbles for this match')
            await du.code_message(ctx, f'You do not have enough marbles for this match,'
                                       f' you have {challenger.marbles}', 3)
            return
        if recipient.marbles < marbles:
            logger.debug(f'{member} does not have enough marbles for this match')
            await du.code_message(ctx, f'They do not have enough marbles for this match,'
                                       f' they have {recipient.marbles}', 3)
            return

        # Creates the match with the players
        match = ma.create_match(ctx, None, marbles, challenger, recipient, game=game, format=form)
        logger.debug(f'match: {match}')
        # Checks if match_id is valid, to verify match was created
        if not match:
            logger.debug('match is zero, failed to create match')
            await du.code_message(ctx, 'Failed to create match', 3)
            return

        # Subtracts marbles from challenger
        challenger.marbles -= marbles

        await du.code_message(ctx, f'{challenger.nickname} challenged {recipient.nickname} '
                                   f'to a marble match for {marbles} '
                                   f'marbles'
                                   f'\nType \'$accept\' to accept their challenge.'
                                   f'\nType \'$close\' to decline the challenge.'
                                   f'\nMatch ID: {match.id}')

    @match.error
    async def generic_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await du.code_message(ctx, f"You're missing required argument: {error.param.name}", 3)
            await ctx.send_help('match')
        elif isinstance(error, commands.CheckFailure):
            await du.code_message(ctx, f"You're unable to use this command in a dm.", 3)
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

    @commands.command(name='accept', help='Accept a challenge')
    @commands.guild_only()
    async def accept(self, ctx: commands.Context):
        """Accepts a match you were challenged to

        Examples:
            - `$accept`

        **Arguments**

        - `<ctx>` The context used to send confirmations.

        """
        logger.debug(f'accept: {ctx}, {ctx.author}')
        # Get player from database for user, then get a match_id
        player = acc.get_account(ctx, DbHandler.db_cnc, ctx.author)
        match_id = database_operation.find_match_by_player_id(DbHandler.db_cnc, player.id)
        logger.debug(f'player: {player}, match_id: {match_id}')

        # Checks if match id is 0/None, gives user message and returns to exit
        if not match_id:
            logger.debug(f'match_id is zero')
            await du.code_message(ctx, 'You don\'t have a match to accept')
            return

        # Get match_info to get marble amount
        match = ma.get_match(ctx, match_id)  # database_operation.get_match_info_by_id(DbHandler.db_cnc, match_id)

        # Checks if match_info is valid
        if not match:
            logger.debug('match_info is zero')
            await du.code_message(ctx, 'Unable to get match info')
            return

        # Check if user accepting is participant2
        if player.id != match.recipient.id:
            logger.debug(f'{ctx.author} tried to accept a match they aren\'t the recipient of')
            await du.code_message(ctx, 'You\'re not the recipient of a match')
            return

        # Updates match accepted flag in database, checks if write was successful and gives message
        try:
            match.accepted = True  # database_operation.update_match_accepted(DbHandler.db_cnc, match_id):
        except commands.CommandError as e:
            logger.debug(f'Unable to update match accepted flag')
            await du.code_message(ctx, 'Was unable to accept match', 3)
            return

        # Subtracts marbles from user
        player.marbles -= match.amount

        await du.code_message(ctx, f'Match {match.id} accepted, now open for betting.'
                                   f'\nType \'$start\' to close the betting and start the match')

    @accept.error
    async def generic_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await du.code_message(ctx, f"You're missing required argument: {error.param.name}", 3)
            await ctx.send_help('match')
        elif isinstance(error, commands.CheckFailure):
            await du.code_message(ctx, f"You're unable to use this command in a dm.", 3)
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

    @commands.command(name='start', help='Start the match and close betting')
    @commands.guild_only()
    async def match_start(self, ctx: commands.Context):
        """Starts a marble match

        Examples:
            - `$start`

        **Arguments**

        - `<ctx>` The context used to send confirmations.

        """
        logger.debug(f'match_start: {ctx}, {ctx.author}')
        # Get player_id from database for user, then get a match_id
        player_id = du.get_id_by_member(ctx, DbHandler.db_cnc, ctx.author)
        match_id = database_operation.find_match_by_player_id(DbHandler.db_cnc, player_id)
        logger.debug(f'player_id: {player_id}, match_id: {match_id}')

        # Checks if match id is 0/None, gives user message and returns to exit
        if not match_id:
            logger.debug(f'match_id is zero')
            await du.code_message(ctx, 'You don\'t have a match to start')
            return

        try:
            # Get match from match_id
            match = ma.get_match(ctx, match_id)
            logger.debug(f'match: {match}')
        except commands.CommandError as e:
            logger.error(f'Unable to get match from match_id')
            await du.code_message(ctx, 'Was unable to get match please try again later', 3)
            return

        # Check if match is accepted
        if not match.accepted:
            logger.debug(f'match.accepted is false')
            await du.code_message(ctx, 'You can only start matches the other player has accepted', 3)
            return

        # Updates match accepted flag in database, checks if write was successful and gives message
        try:  # if not database_operation.update_match_activity(DbHandler.db_cnc, match_id):
            match.active = True
        except commands.CommandError as e:
            logger.debug(f'Unable to update match accepted flag')
            await du.code_message(ctx, 'Was unable to accept match', 3)
            return
        await du.code_message(ctx, f'Match {match_id} started, betting is closed and all bets are locked in.')

    @match_start.error
    async def generic_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await du.code_message(ctx, f"You're missing required argument: {error.param.name}", 3)
            await ctx.send_help('match')
        elif isinstance(error, commands.CheckFailure):
            await du.code_message(ctx, f"You're unable to use this command in a dm.", 3)
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

    @commands.command(name='winner', help='Selects the winner of a marble match, and transfers marbles')
    @commands.guild_only()
    async def match_win(self, ctx: commands.Context, member: Union[discord.Member, str] = None):
        """Sets the winner of a marble match

        Examples:
            - `$winner @Sophia`
            - `$winner @Ness`

        **Arguments**

        - `<ctx>` The context used to send confirmations.
        - `<member>' Member to select as the winner.

        """
        logger.debug(f'match_win: {member}')
        # Checks if member is None, then sets member to ctx.author if true
        if member is None:
            member = ctx.author
        # Gets winner/match_id to process match and do integrity checks
        winner = acc.get_account(ctx, DbHandler.db_cnc, member)
        match_id = database_operation.find_match_by_player_id(DbHandler.db_cnc, winner.id)
        logger.debug(f'winner: {winner}, match_id: {match_id}')

        # Checks if they have an active match
        if not match_id:
            logger.debug('match_id is zero')
            await du.code_message(ctx, 'They have no active match', 3)
            return
        # Get match info from match_id
        try:
            match = ma.get_match(ctx, match_id)
            logger.debug(f'match: {match}')
        except commands.CommandError as e:
            logger.error(f'Unable to get match: {e}')
            await du.code_message(ctx, 'Unable to process match', 3)
            return

        # Set loser to other participant
        # Checks if participant1 is winner if true sets loser to participant2, or participant1 otherwise
        if winner == match.challenger:
            loser = match.recipient
        else:
            loser = match.challenger
        logger.debug(f'loser: {loser}')

        try:
            # Set match winner
            match.winner = winner
            # Add marbles to winner
            winner.marbles += match.amount * 2
            # Adds win/lose to winner/loser
            winner.wins += 1
            loser.loses += 1
        except commands.CommandError as e:
            logger.error(f'Unable to update player stats: {e}')
            await du.code_message(ctx, 'Was unable to update player stats please try again', 3)
            return

        # Processes the bets on the match
        database_operation.process_bets(DbHandler.db_cnc, match_id, winner.id)
        logger.debug('Processed bets')
        # Creates a entry of match in match_history table, deletes from matches
        try:
            match.is_history = True
            match.match_time = datetime.utcnow()
            logger.debug('Updated match info')
            match.create_history()
            logger.debug('Created match_history for match')
        except commands.CommandError as e:
            logger.error(f'Unable to create matches_history entry')
            await du.code_message(ctx, f'Failed to add match to history or to delete from matches: {match.id}', 3)
            return

        await du.code_message(ctx, f'{winner.nickname} is the winner, gaining a total of {match.amount} marbles!')

    @accept.error
    async def generic_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await du.code_message(ctx, f"You're missing required argument: {error.param.name}", 3)
            await ctx.send_help('match')
        elif isinstance(error, commands.CheckFailure):
            await du.code_message(ctx, f"You're unable to use this command in a dm.", 3)
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

    @commands.command(name='current', help='Lists info about you\'re current match')
    @commands.guild_only()
    async def current(self, ctx: commands.Context):
        """Lists your current marble match

        Examples:
            - `$current`

        **Arguments**

        - `<ctx>` The context used to send confirmations.

        """
        logger.debug(f'current: {ctx}, {ctx.author}')

        # Gets player_id from ctx.author and gets match_id for player
        player_id = du.get_id_by_member(ctx, DbHandler.db_cnc, ctx.author)
        match_id = database_operation.find_match_by_player_id(DbHandler.db_cnc, player_id)
        logger.debug(f'player_id: {player_id}, match_id: {match_id}')

        # Checks if match_id is an actual id
        if not match_id:
            logger.debug('match_id is zero')
            await du.code_message(ctx, 'No current match')
            return
        # Gets match_info to display back to the user
        match_info = ma.get_match(ctx, match_id)  # database_operation.get_match_info_by_id(DbHandler.db_cnc, match_id)
        logger.debug(f'match_info: {match_info}')

        # Get Accounts of both participants
        player_info1 = acc.get_account_from_db(ctx, DbHandler.db_cnc, match_info.challenger.id)  # database_operation.get_player_info(DbHandler.db_cnc, match_info[3])
        player_info2 = acc.get_account_from_db(ctx, DbHandler.db_cnc, match_info.recipient.id)  # database_operation.get_player_info(DbHandler.db_cnc, match_info[4])
        logger.debug(f'player_info1: {player_info1}, player_info2: {player_info2}')

        await du.code_message(ctx, f'Match between {player_info1.nickname} and '
                                   f'{player_info2.nickname} for {match_info.amount} marbles'
                                   f'\nMatch ID: {match_info.id}')

    @current.error
    async def generic_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await du.code_message(ctx, f"You're missing required argument: {error.param.name}", 3)
            await ctx.send_help('match')
        elif isinstance(error, commands.CheckFailure):
            await du.code_message(ctx, f"You're unable to use this command in a dm.", 3)
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

    @commands.command(name='close', help='Closes your pending match, if it has not been started')
    @commands.guild_only()
    async def close_current_match(self, ctx: commands.Context):
        """Closes your active marble match

        Examples:
            - `$close`

        **Arguments**

        - `<ctx>` The context used to send confirmations

        """
        logger.debug(f'close: {ctx}, {ctx.author}')

        # Gets player_id and match_id, to close the current match
        player_id = du.get_id_by_member(ctx, DbHandler.db_cnc, ctx.author)
        match_id = database_operation.find_match_by_player_id(DbHandler.db_cnc, player_id)
        logger.debug(f'player_id: {player_id}, match_id: {match_id}')

        # Gets match_info to return marbles back to participants
        match_info = ma.get_match(ctx, match_id)  # database_operation.get_match_info_by_id(DbHandler.db_cnc, match_id)
        logger.debug(f'match_info: {match_info}')

        player2_refund = False

        # Checks if match is accepted by participant2
        if match_info.accepted:  # Match is accepted
            # Gets participant2's Account to change marbles
            player2 = acc.get_account_from_db(ctx, DbHandler.db_cnc, match_info.recipient.id)
            logger.debug(f'player2: {player2}')
            # Checks if player2 is 0, then returns if 0
            if not player2:
                logger.debug(f'Unable to get participant2 Account')
                await du.code_message(ctx, 'Unable to get participant2\'s account')
                return
            # Sets flag for player2 to be refunded amount to true
            player2_refund = True
            logger.debug(f'player2_refund: {player2_refund}')

        # Get participant1's Account to refund player for match amount
        player1 = acc.get_account_from_db(ctx, DbHandler.db_cnc, match_info.challenger.id)
        # Check if player1 is 0, then returns if 0
        if not player1:
            logger.debug('Unable to get participant1 Account')
            await du.code_message(ctx, 'Unable to get participant1\'s account')
            return

        # Deletes the match and all the bets on the match by id, checks if write was successful and returns message
        if not database_operation.delete_match(DbHandler.db_cnc, match_id):
            logger.debug('Unable to delete match')
            await du.code_message(ctx, 'Unable to delete match', 3)
            return

        # Refunds players marbles, checks if player2 flag is true to refund player2
        player1.marbles += match_info.amount
        if player2_refund:
            player2.marbles += match_info.amount

        database_operation.delete_bet_by_match_id(DbHandler.db_cnc, match_id)
        await du.code_message(ctx, f'Closed match {match_id}.')

    @close_current_match.error
    async def generic_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await du.code_message(ctx, f"You're missing required argument: {error.param.name}", 3)
            await ctx.send_help('match')
        elif isinstance(error, commands.CheckFailure):
            await du.code_message(ctx, f"You're unable to use this command in a dm.", 3)
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

    # Function to send error message to user
    @staticmethod
    async def send_error(ctx, hardcoded_time, account):
        difference = hardcoded_time - datetime.utcnow()
        seconds = difference.seconds
        hours = seconds // 3600
        if not hours:
            minutes = seconds // 60
            await du.code_message(ctx, f"{account.nickname} already used this command today, "
                                       f"must wait {minutes} minutes until server refresh")
        else:
            await du.code_message(ctx, f"{account.nickname} already used this command today, "
                                       f"must wait {hours} hours until server refresh")

    @commands.command(name='friendly', help="Use when you're playing a friendly to earn a marble")
    @commands.guild_only()
    async def friendlies(self, ctx: commands.Context, member: Union[discord.Member, str]):
        logger.debug(f'friendlies: {member}')

        # Get players Accounts
        player1 = acc.get_account(ctx, DbHandler.db_cnc, ctx.author)
        if not player1:
            logger.error('No player1_id found')
            await du.code_message(ctx, 'Unable to get player info', 3)
        player2 = acc.get_account(ctx, DbHandler.db_cnc, member)
        if not player2:
            logger.error('No player1_id found')
            await du.code_message(ctx, 'Unable to get player info', 3)

        # Check if player1 is player2
        if player1.id == player2.id:
            await du.code_message(ctx, 'No self friendlies', 3)
            return

        # Function to check if reaction and user
        def check_member(reaction, user):
            return user == player2.member and str(reaction.emoji) == '\U00002705'   # ✅️

        # Set needed variables
        active = True
        now = datetime.utcnow()
        hardcoded_time = datetime(now.year, now.month, now.day, 4, 0, 0, 0)

        # Get players last used time
        player1_last_used = player1.friendly_last_used
        player2_last_used = player2.friendly_last_used

        # Check if both players have access to the command
        if not player1_last_used or player1_last_used < hardcoded_time:
            if not player2_last_used or player2_last_used < hardcoded_time:
                pass
            else:
                await self.send_error(ctx, hardcoded_time, player2)
                return
        else:
            await self.send_error(ctx, hardcoded_time, player1)
            return

        # Send message to have users react to
        message = await du.code_message(ctx, f'Please react to this message with ✅ to accept the friendly')
        # Add reaction to message
        await message.add_reaction('\U00002705')

        while active:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check_member)
                if str(reaction) == '\U00002705':
                    player1.marbles += 1
                    player1.friendly_last_used = datetime.utcnow()
                    player2.marbles += 1
                    player2.friendly_last_used = datetime.utcnow()
                    await du.code_message(ctx, f"We've added a marble to your accounts for playing friendlies today.\n"
                                               f"{player1.nickname}: {player1.marbles}\n"
                                               f"{player2.nickname}: {player2.marbles}")
            except asyncio.TimeoutError:
                # When 'reaction_add' gets a timeout, set active to false to end loop
                active = False
                # Get cached message to remove all reactions
                cached_msg = discord.utils.get(self.bot.cached_messages, id=message.id)
                for reactions in cached_msg.reactions:
                    await reactions.remove(self.bot.user)

    @close_current_match.error
    async def generic_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await du.code_message(ctx, f"You're missing required argument: {error.param.name}", 3)
            await ctx.send_help('match')
        elif isinstance(error, commands.CheckFailure):
            await du.code_message(ctx, f"You're unable to use this command in a dm.", 3)
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


def setup(bot):
    bot.add_cog(MatchCog(bot))
