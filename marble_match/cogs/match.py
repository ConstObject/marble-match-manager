import discord
import datetime
import logging

from marble_match.utils import discord_utils as du, account as acc
from discord.ext import commands
from marble_match.database.database import DbHandler
from marble_match.database import database_operation

logger = logging.getLogger('marble_match.match')


class MatchCog(commands.Cog, name='Matches'):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='match', help='Challenge a user to a marble match, for all the marbles')
    @commands.guild_only()
    async def match(self, ctx: commands.Context, member: discord.Member, marbles: int):
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

        # Check if author is member, gives a message to user and returns to exit
        if ctx.author == member:
            logger.debug(f'{ctx.author} passed themselves as member in match command')
            await du.code_message(ctx,
                                  'You\'re a terrible person who made Soph have to program this.\nNo self matches', 3)
            return

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
        match_id = database_operation.create_match(DbHandler.db_cnc,
                                                   None, marbles, 0, challenger.id, recipient.id)
        logger.debug(f'match_id: {match_id}')
        # Checks if match_id is valid, to verify match was created
        if not match_id:
            logger.debug('match_id is zero, failed to create match')
            await du.code_message(ctx, 'Failed to create match', 3)
            return

        # Subtracts marbles from challenger
        challenger.marbles -= marbles

        await du.code_message(ctx, f'{ctx.author.display_name} challenged {member.display_name} '
                                   f'to a marble match for {marbles} '
                                   f'marbles'
                                   f'\nType \'$accept\' to accept their challenge.'
                                   f'\nType \'$close\' to decline the challenge.'
                                   f'\nMatch ID: {match_id}')

    @match.error
    async def match_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await du.code_message(ctx, f'You\'re missing required argument: {error.param.name}', 3)
            await ctx.send_help('match')

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
        match_info = database_operation.get_match_info_by_id(DbHandler.db_cnc, match_id)

        # Checks if match_info is valid
        if not match_info:
            logger.debug('match_info is zero')
            await du.code_message(ctx, 'Unable to get match info')
            return

        # Check if user accepting is participant2
        if player.id == match_info[3]:
            logger.debug(f'{ctx.author} tried to accept a match they aren\'t the recipient of')
            await du.code_message(ctx, 'You\'re not the recipient of a match')
            return

        # Updates match accepted flag in database, checks if write was successful and gives message
        if not database_operation.update_match_accepted(DbHandler.db_cnc, match_id):
            logger.debug(f'Unable to update match accepted flag')
            await du.code_message(ctx, 'Was unable to accept match', 3)
            return

        # Subtracts marbles from user
        player.marbles -= match_info[1]

        await du.code_message(ctx, f'Match {match_id} accepted, now open for betting.'
                                   f'\nType \'$start\' to close the betting and start the match')

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

        # Updates match accepted flag in database, checks if write was successful and gives message
        if not database_operation.update_match_activity(DbHandler.db_cnc, match_id):
            logger.debug(f'Unable to update match accepted flag')
            await du.code_message(ctx, 'Was unable to accept match', 3)
            return
        await du.code_message(ctx, f'Match {match_id} started, betting is closed and all bets are locked in.')

    @commands.command(name='winner', help='Selects the winner of a marble match, and transfers marbles')
    @commands.guild_only()
    async def match_win(self, ctx: commands.Context, member: discord.Member = None):
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
        match_info = database_operation.get_match_info_by_id(DbHandler.db_cnc, match_id)
        logger.debug(f'match_id: {match_id}')

        # Set loser to other participant
        # Checks if participant1 is winner if true sets loser to participant2, or participant1 otherwise
        if winner.id == match_info[3]:
            loser = acc.get_account_from_db(ctx, DbHandler.db_cnc, match_info[4])
        else:
            loser = acc.get_account_from_db(ctx, DbHandler.db_cnc, match_info[3])
        logger.debug(f'loser: {loser}')

        # Add marbles to winner
        winner.marbles += match_info[1]*2
        # Adds win/lose to winner/loser
        winner.wins += 1
        loser.loses += 1
        # Creates a entry of match in match_history table
        database_operation.create_match_history(DbHandler.db_cnc, match_id, match_info[1], match_info[3],
                                                match_info[4], winner.id, datetime.datetime.utcnow())
        # Processes the bets on the match
        database_operation.process_bets(DbHandler.db_cnc, match_id, winner.id)
        # Deletes the match
        database_operation.delete_match(DbHandler.db_cnc, match_id)

        await du.code_message(ctx, f'{member.display_name} is the winner, gaining a total of {match_info[1]} marbles!')

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
        match_info = database_operation.get_match_info_by_id(DbHandler.db_cnc, match_id)
        logger.debug(f'match_info: {match_info}')

        # Get Accounts of both participants
        player_info1 = database_operation.get_player_info(DbHandler.db_cnc, match_info[3])
        player_info2 = database_operation.get_player_info(DbHandler.db_cnc, match_info[4])
        logger.debug(f'player_info1: {player_info1}, player_info2: {player_info2}')

        await du.code_message(ctx, f'Match between {player_info1[1]} and {player_info2[1]} for {match_info[1]} marbles'
                                   f'\nMatch ID: {match_id}')

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
        match_info = database_operation.get_match_info_by_id(DbHandler.db_cnc, match_id)
        logger.debug(f'match_info: {match_info}')

        player2_refund = False

        # Checks if match is accepted by participant2
        if match_info[5]:  # Match is accepted
            # Gets participant2's Account to change marbles
            player2 = acc.get_account_from_db(ctx, DbHandler.db_cnc, match_info[4])
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
        player1 = acc.get_account_from_db(ctx, DbHandler.db_cnc, int(match_info[3]))
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
        player1.marbles += match_info[1]
        if player2_refund:
            player2.marbles += match_info[1]

        database_operation.delete_bet_by_match_id(DbHandler.db_cnc, match_id)
        await du.code_message(ctx, f'Closed match {match_id}.')


def setup(bot):
    bot.add_cog(MatchCog(bot))
