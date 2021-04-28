import discord
import database
import database_operation
import discord_utils as du
from discord.ext import commands
import numpy as np


class EconCog(commands.Cog, name='Marbles'):

    def __init__(self, bot):
        self.bot = bot

    # def testing(self):
    #     print('testing')

    @commands.command(name='set_marbles', help='Will set the users marble count to a new number')
    @commands.guild_only()
    @commands.has_role('Admin')
    async def set_marbles(self, ctx, member: discord.Member, marbles: int):

        if marbles < 0:
            await du.code_message(ctx, 'You cannot set a users marbles to any negative number')
            return

        database_operation.update_marble_count(database.db_connection, du.get_id_by_member(ctx, database.db_connection,
                                                                                           member), marbles)
        await du.code_message(ctx, f'Set {member.display_name}\'s marbles to {str(marbles)}')

    @commands.command(name='add_marbles', help='Will add to the users marble bank')
    @commands.guild_only()
    @commands.has_role('Admin')
    async def add_marbles(self, ctx, member: discord.Member, marbles: int):

        if marbles < 1:
            await du.code_message(ctx, 'You cannot add non positive numbers to a users marble bank')
            return

        player_id = du.get_id_by_member(ctx, database.db_connection, member)

        database_operation.add_marbles(database.db_connection, player_id, marbles)

        balance = database_operation.get_marble_count(database.db_connection, player_id)
        await du.code_message(ctx, f'{ctx.author.display_name} has added {marbles} to {member.display_name}\'s bank.'
                                   f'\nTheir new balance is {balance}!')

    @commands.command(name='subtract_marbles', help='Will subtract from the users marble bank')
    @commands.guild_only()
    @commands.has_role('Admin')
    async def sub_marbles(self, ctx, member: discord.Member, marbles: int):

        if marbles < 1:
            await du.code_message(ctx, 'You cannot subtract non positive numbers to a users marble bank')
            return

        player_id = du.get_id_by_member(ctx, database.db_connection, member)

        database_operation.subtract_marbles(database.db_connection, player_id, marbles)

        balance = database_operation.get_marble_count(database.db_connection, player_id)
        await du.code_message(ctx, f'{ctx.author.display_name} has removed {marbles} from {member.display_name}\'s bank.'
                                   f'\nTheir new balance is {balance}!')

    @commands.command(name='marbles', help='Prints their marble count')
    @commands.guild_only()
    async def balance(self, ctx, member: discord.Member = None):
        if member is None:
            player_id = du.get_id_by_member(ctx, database.db_connection, ctx.author)
            await du.code_message(ctx,
                                  f'You have {database_operation.get_marble_count(database.db_connection, player_id)}'
                                  f' marbles.')
        else:
            player_id = du.get_id_by_member(database.db_connection, database.db_connection, member)
            await du.code_message(ctx,
                                  f'They have {database_operation.get_marble_count(database.db_connection, player_id)} '
                                  f'marbles.')

    @commands.command(name='transfer', help='Transfers marbles from your bank to theirs')
    @commands.guild_only()
    async def transfer(self, ctx, member: discord.Member, marbles: int):
        if ctx.author == member:
            await du.code_message(ctx, 'You cannot send marbles to yourself')
            return

        if marbles < 1:
            await du.code_message(ctx, 'You cannot send non positive amounts of marbles')
            return

        player_id1 = du.get_id_by_member(ctx, database.db_connection, ctx.author)
        player_id2 = du.get_id_by_member(ctx, database.db_connection, member)
        player1_marbles = database_operation.get_marble_count(database.db_connection, player_id1)

        if player1_marbles < marbles:
            await du.code_message(ctx, 'You don\'t have enough marbles for this transaction')
            return

        player2_marbles = database_operation.get_marble_count(database.db_connection, player_id2)

        database_operation.transfer_marbles(database.db_connection, player_id1, player_id2, marbles)

        await du.code_message(ctx, f'Marbles transferred! Your new balances are:'
                                   f'\n{ctx.author.display_name}: {str(player1_marbles - marbles)} marbles'
                                   f'\n{member.display_name}: {str(player2_marbles + marbles)} marbles')

    @commands.command(name='economy', help='Summery of the server economy')
    @commands.guild_only()
    async def summery(self, ctx):
        players = database_operation.get_player_info_all_by_server(database.db_connection, ctx.guild.id)
        marbles = 0
        for user in players:
            marbles += user[2]

        await du.code_message(ctx, f'There are currently {marbles} marbles in circulation')

    @commands.command(name='summery', help='Prints a more detailed summery of the server economy')
    @commands.guild_only()
    async def ex_summery(self, ctx):
        count = 0
        sum_marbles = 0
        marbles = []
        players = database_operation.get_player_info_all_by_server(database.db_connection, ctx.guild.id)
        for user in players:
            sum_marbles += user[2]
            marbles.append(float(user[2]))
            count += 1

        # TODO: Add other calculations for server economy

        # Gini coefficient
        array = np.array(marbles)
        array = array.flatten()
        if np.amin(array) < 0:
            array -= np.amin(array)
        array += 0.0000001
        array = np.sort(array)
        index = np.arange(1, array.shape[0] + 1)
        n = array.shape[0]
        gini = ((np.sum((2 * index - n - 1) * array)) / (n * np.sum(array)))

        await du.code_message(ctx, f'There are currently {sum_marbles} marbles in circulation\n'
                                f'The current mean marble count is {int(sum_marbles / count)}\n'
                                f'Inequality index is {gini}\n')


def setup(bot):
    bot.add_cog(EconCog(bot))
