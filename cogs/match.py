import discord
from database import database_operation, database
import datetime
from utils import discord_utils as du
from discord.ext import commands


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

        if ctx.author == member:
            await du.code_message(ctx, 'You\'re a terrible person who made Soph have to program this.\nNo self matches')
            return

        if marbles < 1:
            await du.code_message(ctx, 'You\'re a terrible person who made Soph have to program this.'
                                       '\n No negatives or zero')
            return

        challenger = du.get_id_by_member(ctx, database.db_connection, ctx.author)
        recipient = du.get_id_by_member(ctx, database.db_connection, member)

        if database_operation.find_match_by_player_id(database.db_connection, challenger) != 0:
            await du.code_message(ctx, 'You already have an match going')
            return

        if database_operation.find_match_by_player_id(database.db_connection, recipient) != 0:
            await du.code_message(ctx, 'They already have a match going')
            return

        challenger_marbles = database_operation.get_marble_count(database.db_connection, challenger)
        if challenger_marbles < marbles:
            await du.code_message(ctx, 'You do not have enough marbles for this match')
            return

        recipient_marbles = database_operation.get_marble_count(database.db_connection, recipient)
        if recipient_marbles < marbles:
            await du.code_message(ctx, 'They do not have enough marbles for this match')
            return

        match_id = database_operation.create_match(database.db_connection, None, marbles, 0, challenger, recipient)

        await du.code_message(ctx, f'{ctx.author.display_name} challenged {member.display_name} '
                                   f'to a marble match for {str(marbles)} '
                                   f'marbles'
                                   f'\nType \'$accept\' to accept their challenge.'
                                   f'\nType \'$close\' to decline the challenge.'
                                   f'\nMatch ID: {str(match_id)}')

    @match.error
    async def match_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'member':
                await du.code_message(ctx, 'You need to enter a member to challenge')
            elif error.param.name == 'marbles':
                await du.code_message(ctx, 'You need to enter a marble amount')

    @commands.command(name='accept', help='Accept a challenge')
    @commands.guild_only()
    async def accept(self, ctx: commands.Context):
        """Accepts a match you were challenged to

        Examples:
            - `$accept`

        **Arguments**

        - `<ctx>` The context used to send confirmations.

        """

        player_id = du.get_id_by_member(ctx, database.db_connection, ctx.author)
        match_id = database_operation.find_match_by_player_id(database.db_connection, player_id)

        if match_id == 0:
            await du.code_message(ctx, 'You don\'t have a match to accept')
            return

        database_operation.update_match_accepted(database.db_connection, match_id)
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

        player_id = du.get_id_by_member(ctx, database.db_connection, ctx.author)
        match_id = database_operation.find_match_by_player_id(database.db_connection, player_id)

        if match_id == 0:
            await du.code_message(ctx, 'You don\'t have a match to start')
            return

        database_operation.update_match_activity(database.db_connection, match_id)
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

        if member is None:
            member = ctx.author

        winner_id = du.get_id_by_member(ctx, database.db_connection, member)
        match_id = database_operation.find_match_by_player_id(database.db_connection, winner_id)

        if match_id == 0:
            await du.code_message(ctx, 'They have no active match')
            return

        match_info = database_operation.get_match_info_by_id(database.db_connection, match_id)

        if winner_id == match_info[3]:
            loser_id = match_info[4]
        else:
            loser_id = match_info[3]

        database_operation.transfer_marbles(database.db_connection, loser_id, winner_id, match_info[1])

        database_operation.add_player_win(database.db_connection, winner_id, 1)
        database_operation.add_player_loses(database.db_connection, loser_id, 1)

        database_operation.create_match_history(database.db_connection, match_id, match_info[1], match_info[3],
                                                match_info[4], winner_id, datetime.datetime.utcnow())

        database_operation.process_bets(database.db_connection, match_id, winner_id)

        database_operation.delete_match(database.db_connection, match_id)

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

        player_id = du.get_id_by_member(ctx, database.db_connection, ctx.author)
        match_id = database_operation.find_match_by_player_id(database.db_connection, player_id)

        if match_id == 0:
            await du.code_message(ctx, 'No current match')
            return

        match_info = database_operation.get_match_info_by_id(database.db_connection, match_id)

        player_info1 = database_operation.get_player_info(database.db_connection, match_info[3])
        player_info2 = database_operation.get_player_info(database.db_connection, match_info[4])

        print(player_info1)
        print(player_info2)

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

        player_id = du.get_id_by_member(ctx, database.db_connection, ctx.author)
        match_id = database_operation.find_match_by_player_id(database.db_connection, player_id)

        database_operation.delete_match(database.db_connection, match_id)
        database_operation.delete_bet_by_match_id(database.db_connection, match_id)
        await du.code_message(ctx, f'Closed match {match_id}.')


def setup(bot):
    bot.add_cog(MatchCog(bot))
