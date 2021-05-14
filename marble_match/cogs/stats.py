import logging
import operator

import discord
from discord.ext import commands

import database.database_operation as database_operation
from database.database_setup import DbHandler
import utils.discord_utils as du
import utils.account as acc
import utils.exception as exception

logger = logging.getLogger(f'marble_match.{__name__}')


class StatsCog(commands.Cog, name='Stats'):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='wins', aliases=['loses', 'winrate'], help='Prints a players wins')
    @commands.guild_only()
    async def wins(self, ctx: commands.Context, member: discord.Member = None):
        """Prints a users wins, loses, and winrate

        Examples:
            - `$wins @Sophia`
            - `$wins`

        **Arguments**

        - `<ctx>` The context used to send confirmations.
        - `<member>` The user who's data you want to print. If omitted will defaults to your own data.

        """
        logging.debug(f'wins: {member}')

        # Check if member is None, use ctx.author if None
        if member is None:
            player_id = du.get_id_by_member(ctx, DbHandler.db_cnc, ctx.author)
            name = ctx.author.display_name
        else:
            player_id = du.get_id_by_member(ctx, DbHandler.db_cnc, member)
            name = member.display_name

        # Get player Account
        account = acc.get_account_from_db(ctx, DbHandler.db_cnc, player_id)
        logger.debug(f'account: {account}')

        # Set winrate to 0 if wins is zero, otherwise calculate winrate
        if account.wins == 0:
            player_winrate = 0
        else:
            player_winrate = 100 * (account.wins / (account.wins + account.loses))

        await du.code_message(ctx, f'{account.member.display_name}\n'
                                   f'Wins: {account.wins}'
                                   f'\nLoses: {account.loses}'
                                   f'\nWinrate: {player_winrate:.2f}%')

    @wins.error
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

    @commands.command(name='list_stats', help='Lists of stats you can search by')
    @commands.guild_only()
    async def stat_list(self, ctx: commands.Context):
        stats = ['wins', 'loses', 'marbles', 'winrate']
        text = ''
        for stat in stats:
            text += f' {stat},'
        await du.code_message(ctx, f'You can use any of these stats with leaderboard command:{text}')

    @commands.command(name='leaderboard',
                      help='Will list top 10 players by winrate, or give position of member on leaderboard')
    @commands.guild_only()
    async def leaderboard(self, ctx: commands.Context, stat: str, members: discord.Member = None):
        """Lists top 10 players by winrate, or a specific users position on leaderboard

        Examples:
            - `$leaderboard winrate @Sophia`
            - `$leaderboard`
            - `$leaderboard wins`

        **Arguments**

        - `<ctx>` The context used to send confirmations.
        - `<stat>` String of stat to get
        - `<members>` The member who's position on leaderboard you'd like to receive.

        """
        logger.debug(f'leaderboard: {members}')

        # Get accounts of all users on server
        player_info = acc.get_account_server_all(ctx, DbHandler.db_cnc, ctx.guild.id)  # database_operation.get_player_info_all_by_server(DbHandler.db_cnc, ctx.guild.id)

        # Creation function to get stats based on string
        stat_get = operator.attrgetter(stat)

        players = []

        players = sorted(player_info, key=stat_get, reverse=True)

        if members is not None:
            for player in players:
                if player.member == members:
                    await du.code_message(ctx, f'{members.display_name} is rank #{players.index(player) + 1}, '
                                               f'with a win-rate of {player.winrate:.2f}%')
                    return
            return

        text = f"Leaderboard top 10 {stat}\n\n"

        for player in players[0:10]:
            if stat == 'winrate':
                text += f'#{players.index(player)} {player.member.display_name}: {stat_get(player):.2f}%\n'
            else:
                text += f'#{players.index(player)} {player.member.display_name}: {stat_get(player)}\n'

        await du.code_message(ctx, text)

    @leaderboard.error
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

def setup(bot):
    bot.add_cog(StatsCog(bot))
