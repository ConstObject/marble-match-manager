import discord
from discord.ext import commands
import numpy as np

import database.database_operation as database_operation
from database.database_setup import DbHandler
import utils.discord_utils as du
import utils.exception as exception


class EconCog(commands.Cog, name='Marbles'):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # def testing(self):
    #     print('testing')

    @commands.command(name='set_marbles', help='Will set the users marble count to a new number')
    @commands.guild_only()
    @commands.has_role('Admin')
    async def set_marbles(self, ctx: commands.Context, member: discord.Member, marbles: int):
        """Sets a users marbles to a specified amount

        Examples:
            - `$set_marbles @Sophia 10`
            - `$set_marbles @Ness 0`

        **Arguments**

        - `<ctx>` The context used to send confirmations.
        - `<member>` The user who's marbles you want to set.
        - `<marbles>` Amount to set users.

        """

        if marbles < 0:
            await du.code_message(ctx, 'You cannot set a users marbles to any negative number')
            return

        database_operation.update_marble_count(DbHandler.db_cnc,
                                               du.get_id_by_member(ctx, DbHandler.db_cnc, member), marbles)
        await du.code_message(ctx, f'Set {member.display_name}\'s marbles to {str(marbles)}')

    @set_marbles.error
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

    @commands.command(name='add_marbles', help='Will add to the users marble bank')
    @commands.guild_only()
    @commands.has_role('Admin')
    async def add_marbles(self, ctx: commands.Context, member: discord.Member, marbles: int):
        """Add marbles to a users bank

        Examples:
            - `$add_marbles @Sophia 10`
            - `$add_marbles @Ness 5`

        **Arguments**

        - `<ctx>` The context used to send confirmations.
        - `<member>` User you want to add marbles to.
        - `<marbles>` Amount to add to users bank.

        """

        if marbles < 1:
            await du.code_message(ctx, 'You cannot add non positive numbers to a users marble bank')
            return

        player_id = du.get_id_by_member(ctx, DbHandler.db_cnc, member)

        database_operation.add_marbles(DbHandler.db_cnc, player_id, marbles)

        balance = database_operation.get_marble_count(DbHandler.db_cnc, player_id)
        await du.code_message(ctx, f'{ctx.author.display_name} has added {marbles} to {member.display_name}\'s bank.'
                                   f'\nTheir new balance is {balance}!')

    @add_marbles.error
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

    @commands.command(name='subtract_marbles', help='Will subtract from the users marble bank')
    @commands.guild_only()
    @commands.has_role('Admin')
    async def sub_marbles(self, ctx: commands.Context, member: discord.Member, marbles: int):
        """Subtracts marbles from a users bank

        Examples:
            - `$subtract_marbles @Sophia 10`
            - `$subtract_marbles @Ness 1`

        **Arguments**

        - `<ctx>` The context used to send confirmations.
        - `<member>` The member you'd like to subtract marbles from.
        - `<marbles>` Amount of marbles to subtract.

        """

        if marbles < 1:
            await du.code_message(ctx, 'You cannot subtract non positive numbers to a users marble bank')
            return

        player_id = du.get_id_by_member(ctx, DbHandler.db_cnc, member)

        database_operation.subtract_marbles(DbHandler.db_cnc, player_id, marbles)

        balance = database_operation.get_marble_count(DbHandler.db_cnc, player_id)
        await du.code_message(ctx, f'{ctx.author.display_name} has removed {marbles} from '
                                   f'{member.display_name}\'s bank.'
                                   f'\nTheir new balance is {balance}!')

    @sub_marbles.error
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

    @commands.command(name='marbles', help='Prints their marble count')
    @commands.guild_only()
    async def balance(self, ctx: commands.Context, member: discord.Member = None):
        """Prints a users marble balance

        Examples:
            - `$marbles @Sophia`
            - `$marbles`

        **Arguments**

        - `<ctx>` The context used to send confirmations.
        - `<member>` The member who's marble count you want to see. If omitted defaults to your own marbles.

        """

        if member is None:
            player_id = du.get_id_by_member(ctx, DbHandler.db_cnc, ctx.author)
            await du.code_message(ctx,
                                  f'You have '
                                  f'{database_operation.get_marble_count(DbHandler.db_cnc, player_id)} '
                                  f'marbles.')
        else:
            player_id = du.get_id_by_member(ctx, DbHandler.db_cnc, member)
            await du.code_message(ctx,
                                  f'They have '
                                  f'{database_operation.get_marble_count(DbHandler.db_cnc, player_id)} '
                                  f'marbles.')

    @balance.error
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

    @commands.command(name='transfer', help='Transfers marbles from your bank to theirs')
    @commands.guild_only()
    async def transfer(self, ctx: commands.Context, member: discord.Member, marbles: int):
        """Transfers marbles from your bank to another users bank

        Examples:
            - `$transfer @Sophia 10`
            - `$transfer @Ness 5`

        **Arguments**

        - `<ctx>` The context used to send confirmations.
        - `<member>` User you want to transfer marbles to.
        - `<marbles>` Amount to transfer to a user from your bank

        """

        if ctx.author == member:
            await du.code_message(ctx, 'You cannot send marbles to yourself')
            return

        if marbles < 1:
            await du.code_message(ctx, 'You cannot send non positive amounts of marbles')
            return

        player_id1 = du.get_id_by_member(ctx, DbHandler.db_cnc, ctx.author)
        player_id2 = du.get_id_by_member(ctx, DbHandler.db_cnc, member)
        player1_marbles = database_operation.get_marble_count(DbHandler.db_cnc, player_id1)

        if player1_marbles < marbles:
            await du.code_message(ctx, 'You don\'t have enough marbles for this transaction')
            return

        player2_marbles = database_operation.get_marble_count(DbHandler.db_cnc, player_id2)

        database_operation.transfer_marbles(DbHandler.db_cnc, player_id1, player_id2, marbles)

        await du.code_message(ctx, f'Marbles transferred! Your new balances are:'
                                   f'\n{ctx.author.display_name}: {str(player1_marbles - marbles)} marbles'
                                   f'\n{member.display_name}: {str(player2_marbles + marbles)} marbles')

    @transfer.error
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

    @commands.command(name='economy', help='Summery of the server economy')
    @commands.guild_only()
    async def summery(self, ctx: commands.Context):
        """Prints a simple summery of the server economy

        Examples:
            - `$economy`

        **Arguments**

        - `<ctx>` The context used to get server information.

        """

        players = database_operation.get_player_info_all_by_server(DbHandler.db_cnc, ctx.guild.id)
        marbles = 0
        for user in players:
            marbles += user[2]

        await du.code_message(ctx, f'There are currently {marbles} marbles in circulation')

    @summery.error
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

    @commands.command(name='summery', help='Prints a more detailed summery of the server economy')
    @commands.guild_only()
    async def ex_summery(self, ctx: commands.Context):
        """Prints a detailed summery of the server economy

        Examples:
            - `$summery`

        **Arguments**

        - `<ctx>` The context used to get server information.

        """

        count = 0
        sum_marbles = 0
        marbles = []
        players = database_operation.get_player_info_all_by_server(DbHandler.db_cnc, ctx.guild.id)
        for user in players:
            sum_marbles += user[2]
            marbles.append(np.float64(user[2]))
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
                                   f'Inequality index is {gini:.4f}\n')

    @ex_summery.error
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
    bot.add_cog(EconCog(bot))
