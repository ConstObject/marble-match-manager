import logging
from typing import Union

import discord
from discord.ext import commands
import numpy as np

import database.database_operation as database_operation
from database.database_setup import DbHandler
import utils.discord_utils as du
import utils.account as acc
import utils.exception as exception

logger = logging.getLogger(f'marble_match.{__name__}')


class EconCog(commands.Cog, name='Marbles'):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # def testing(self):
    #     print('testing')

    @commands.command(name='set_marbles', help='Will set the users marble count to a new number')
    @commands.guild_only()
    @commands.has_role('Admin')
    async def set_marbles(self, ctx: commands.Context, member: Union[discord.Member, str], marbles: int):
        """Sets a users marbles to a specified amount

        Examples:
            - `$set_marbles @Sophia 10`
            - `$set_marbles @Ness 0`

        **Arguments**

        - `<ctx>` The context used to send confirmations.
        - `<member>` The user who's marbles you want to set.
        - `<marbles>` Amount to set users.

        """
        logger.debug(f'set_marbles: {member}, {marbles}')

        account = acc.get_account(ctx, DbHandler.db_cnc, member)

        if marbles < 0:
            await du.code_message(ctx, 'You cannot set a users marbles to any negative number')
            return

        account.marbles = marbles

        await du.code_message(ctx, f'Set {account.nickname}\'s marbles to {account.marbles}')

    @commands.command(name='add_marbles', help='Will add to the users marble bank')
    @commands.guild_only()
    @commands.has_role('Admin')
    async def add_marbles(self, ctx: commands.Context, member: Union[discord.Member, str], marbles: int):
        """Add marbles to a users bank

        Examples:
            - `$add_marbles @Sophia 10`
            - `$add_marbles @Ness 5`

        **Arguments**

        - `<ctx>` The context used to send confirmations.
        - `<member>` User you want to add marbles to.
        - `<marbles>` Amount to add to users bank.

        """
        logger.debug(f'add_marbles: {member}, {marbles}')

        if marbles < 1:
            await du.code_message(ctx, 'You cannot add non positive numbers to a users marble bank')
            return

        account = acc.get_account(ctx, DbHandler.db_cnc, member)

        account.marbles += marbles

        await du.code_message(ctx, f'Added {marbles} to {account.nickname}\'s bank.'
                                   f'\nTheir new balance is {account.marbles}!')

    @commands.command(name='subtract_marbles', help='Will subtract from the users marble bank')
    @commands.guild_only()
    @commands.has_role('Admin')
    async def sub_marbles(self, ctx: commands.Context, member: Union[discord.Member, str], marbles: int):
        """Subtracts marbles from a users bank

        Examples:
            - `$subtract_marbles @Sophia 10`
            - `$subtract_marbles @Ness 1`

        **Arguments**

        - `<ctx>` The context used to send confirmations.
        - `<member>` The member you'd like to subtract marbles from.
        - `<marbles>` Amount of marbles to subtract.

        """
        logger.debug(f'subtract_marbles: {member}, {marbles}')

        if marbles < 1:
            await du.code_message(ctx, 'You cannot subtract non positive numbers to a users marble bank')
            return

        account = acc.get_account(ctx, DbHandler.db_cnc, member)

        account.marbles -= marbles

        await du.code_message(ctx, f'Removed {marbles} from '
                                   f'{account.nickname}\'s bank.'
                                   f'\nTheir new balance is {account.marbles}!')

    @commands.command(name='marbles', help='Prints their marble count')
    @commands.guild_only()
    async def balance(self, ctx: commands.Context, member: Union[discord.Member, str] = None):
        """Prints a users marble balance

        Examples:
            - `$marbles @Sophia`
            - `$marbles`

        **Arguments**

        - `<ctx>` The context used to send confirmations.
        - `<member>` The member who's marble count you want to see. If omitted defaults to your own marbles.

        """
        logger.debug(f'marbles: {member}')

        if member is None:
            account = acc.get_account(ctx, DbHandler.db_cnc, ctx.author)
        else:
            account = acc.get_account(ctx, DbHandler.db_cnc, member)

        logger.debug(f'account: {account}')

        await du.code_message(ctx, f"{account.nickname} has {account.marbles} marbles")

    @commands.command(name='transfer', help='Transfers marbles from your bank to theirs')
    @commands.guild_only()
    async def transfer(self, ctx: commands.Context, member: Union[discord.Member, str], marbles: int):
        """Transfers marbles from your bank to another users bank

        Examples:
            - `$transfer @Sophia 10`
            - `$transfer @Ness 5`

        **Arguments**

        - `<ctx>` The context used to send confirmations.
        - `<member>` User you want to transfer marbles to.
        - `<marbles>` Amount to transfer to a user from your bank

        """
        logger.debug(f'transfer: {member}, {marbles}')

        if marbles < 1:
            await du.code_message(ctx, 'You cannot send non positive amounts of marbles')
            return

        author_account = acc.get_account(ctx, DbHandler.db_cnc, ctx.author)
        target_account = acc.get_account(ctx, DbHandler.db_cnc, member)
        logger.debug(f'author_account: {author_account}, target_account: {target_account}')

        # Check if author account and member account are not the same
        if author_account == target_account:
            await du.code_message(ctx, 'You cannot send marbles to yourself')
            return

        if author_account.marbles < marbles:
            await du.code_message(ctx, 'You don\'t have enough marbles for this transaction')
            return

        author_account.marbles -= marbles
        target_account.marbles += marbles

        await du.code_message(ctx, f'Marbles transferred! Your new balances are:'
                                   f'\n{author_account.nickname}: {author_account.marbles} marbles'
                                   f'\n{target_account.nickname}: {target_account.marbles} marbles')

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


def setup(bot):
    bot.add_cog(EconCog(bot))
