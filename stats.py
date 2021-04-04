import discord
import database
import database_operation
from discord_utils import code_message
from discord.ext import commands


class StatsCog(commands.Cog, name='Stats'):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='wins', aliases=['loses', 'winrate'], help='Prints a players wins')
    @commands.guild_only()
    async def wins(self, ctx, member: discord.Member = None):

        if member is None:
            player_id = database_operation.get_player_id(database.db_connection, str(ctx.author), ctx.guild.id)[0]
            name = ctx.author.display_name
        else:
            player_id = database_operation.get_player_id(database.db_connection, str(member), ctx.guild.id)[0]
            name = member.display_name
        player_wins = database_operation.get_player_wins(database.db_connection, player_id)
        player_loses = database_operation.get_player_loses(database.db_connection, player_id)

        if player_wins == 0:
            player_winrate = 0
        else:
            player_winrate = 100 * (player_wins / (player_wins + player_loses))

        await code_message(ctx, f'{name}\n'
                                f'Wins: {player_wins}'
                                f'\nLoses: {player_loses}'
                                f'\nWinrate: {player_winrate}%')

    @commands.command(name='leaderboard',
                      help='Will list top 10 players by winrate, or give position of member on leaderboard')
    @commands.guild_only()
    async def leaderboard(self, ctx, *, members: discord.Member = None):

        player_info = database_operation.get_player_info_all_by_server(database.db_connection, ctx.guild.id)

        players = []

        for user in ctx.guild.members:
            if database_operation.get_player_id(database.db_connection, str(user), ctx.guild.id) != 0:
                player_data = database_operation.get_player_id(database.db_connection, str(user), ctx.guild.id)
                if player_data[4] == 0:
                    winrate = 0
                elif player_data[5] == 0:
                    winrate = 100
                else:
                    winrate = 100 * (player_data[4] / (player_data[4] + player_data[5]))

                players.append((player_data[1], player_data[4], player_data[5], winrate))

        players.sort(key=lambda players: players[3], reverse=True)

        if members is not None:
            for player in players:
                if player[0] == str(members):
                    await code_message(ctx, f'{members.display_name} is rank #{players.index(player) + 1}, '
                                            f'with a win-rate of {player[3]}%')
            return

        text = "```Leaderboard top 10 win-rate\n\n"

        for player in players[0:10]:
            text += (f'#{players.index(player) + 1}. {player[0]}: %.0f' % player[3]) + '%\n'
        text += "```"

        await code_message(ctx, text)
