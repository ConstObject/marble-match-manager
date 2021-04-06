import discord
import database
import database_operation
from discord_utils import code_message
from discord.ext import commands


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
            await code_message(ctx, 'You\'re a terrible person who made Soph have to program this.')
            return

        database_operation.update_marble_count(database.db_connection,
                                               database_operation.get_player_id(database.db_connection, str(member),
                                                                                ctx.guild.id)[0],
                                               marbles)
        await code_message(ctx, f'Set {member.display_name}\'s marbles to {str(marbles)}')

    @commands.command(name='add_marbles', help='Will add to the users marble bank')
    @commands.guild_only()
    @commands.has_role('Admin')
    async def add_marbles(self, ctx, member: discord.Member, marbles: int):

        if marbles < 1:
            await code_message(ctx, 'You cannot add non positive numbers to a users marble bank')
            return

        player_id = database_operation.get_player_id(database.db_connection, str(member), ctx.guild.id)[0]
        old_marbles = database_operation.get_marble_count(database.db_connection, player_id)

        database_operation.add_marbles(database.db_connection, player_id, marbles)

        await code_message(ctx, f'{ctx.author.display_name} has added {str(marbles)} to {member.display_name}\'s bank.'
                                f'\nTheir new balance is {str(old_marbles + marbles)}!')

    @commands.command(name='subtract_marbles', help='Will subtract from the users marble bank')
    @commands.guild_only()
    @commands.has_role('Admin')
    async def add_marbles(self, ctx, member: discord.Member, marbles: int):

        if marbles < 1:
            await code_message(ctx, 'You cannot subtract non positive numbers to a users marble bank')
            return

        player_id = database_operation.get_player_id(database.db_connection, str(member), ctx.guild.id)[0]

        database_operation.subtract_marbles(database.db_connection, player_id, marbles)

        balance = database_operation.get_marble_count(database.db_connection, player_id)
        await code_message(ctx, f'{ctx.author.display_name} has removed {marbles} from {member.display_name}\'s bank.'
                                f'\nTheir new balance is {balance}!')

    @commands.command(name='marbles', help='Prints their marble count')
    @commands.guild_only()
    async def balance(self, ctx, member: discord.Member = None):
        if member is None:
            player_id = database_operation.get_player_id(database.db_connection, str(ctx.author), ctx.guild.id)[0]
            await code_message(ctx,
                               f'You have {database_operation.get_marble_count(database.db_connection, player_id)}'
                               f' marbles.')
        else:
            player_id = database_operation.get_player_id(database.db_connection, str(member), ctx.guild.id)[0]
            await code_message(ctx,
                               f'They have {database_operation.get_marble_count(database.db_connection, player_id)} '
                               f'marbles.')

    @commands.command(name='transfer', help='Transfers marbles from your bank to theirs')
    @commands.guild_only()
    async def transfer(self, ctx, member: discord.Member, marbles: int):
        if ctx.author == member:
            await code_message(ctx, 'You cannot send marbles to yourself')
            return

        if marbles < 1:
            await code_message(ctx, 'You cannot send non positive amounts of marbles')
            return

        player_id1 = database_operation.get_player_id(database.db_connection, str(ctx.author), ctx.guild.id)[0]
        player_id2 = database_operation.get_player_id(database.db_connection, str(member), ctx.guild.id)[0]
        player1_marbles = database_operation.get_marble_count(database.db_connection, player_id1)

        if player1_marbles < marbles:
            await code_message(ctx, 'You don\'t have enough marbles for this transaction')
            return

        player2_marbles = database_operation.get_marble_count(database.db_connection, player_id2)

        database_operation.transfer_marbles(database.db_connection, player_id1, player_id2, marbles)

        await code_message(ctx, f'Marbles transferred! Your new balances are:'
                                f'\n{ctx.author.display_name}: {str(player1_marbles - marbles)} marbles'
                                f'\n{member.display_name}: {str(player2_marbles + marbles)} marbles')
