import logging

import discord
from discord.ext import commands

import database.database_operation as database_operation
from database.database_setup import DbHandler
import utils.discord_utils as du
import utils.account as acc
import utils.matches as ma
import utils.bets as bets
import utils.exception as exception

logger = logging.getLogger(f'marble_match.{__name__}')


class BetCog(commands.Cog, name='Bets'):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='bet', help='Place a bet on a match, updates bets, if marbles is 0 it will delete your bet')
    @commands.guild_only()
    async def bet(self, ctx, bet_target: discord.Member, match_id: int, marbles: int):
        """Places a bet on a active and not started match

        Example:
            - `$bet @Sophia 12 5`
            - `$bet @Ness 12 0`

        **Arguments**

        - `<winner>` The player you think will win the match.
        - `<match_id>` The id of the match you'd like to bet on
        - `<marbles>` Amount of marbles you'd like to bet on the match.
        """
        logger.debug(f'bet: {bet_target}, {match_id}, {marbles}')

        # Check if marbles is less than 0, return if not
        if marbles < 0:
            await du.code_message(ctx, 'Marbles cannot be negative')
            return

        # Get winner id and better id
        bet_target_id = du.get_id_by_member(ctx, DbHandler.db_cnc, bet_target)
        bettor_id = du.get_id_by_member(ctx, DbHandler.db_cnc, ctx.author)
        logger.debug(f'bet_target_id: {bet_target_id}, bettor_id: {bettor_id}')

        # Get bettor/bet_target_id accounts
        bettor_acc = acc.get_account_from_db(ctx, DbHandler.db_cnc, bettor_id)
        bet_target_acc = acc.get_account_from_db(ctx, DbHandler.db_cnc, bet_target_id)
        logger.debug(f'bettor: {bettor_acc}, bet_target: {bet_target_acc}')

        # Check if marble count for bettor is greater than marbles
        if bettor_acc.marbles < marbles:
            await du.code_message(ctx, f'You do not have enough marbles for this bet\n'
                                       f'You have {bettor_acc.marbles} and need {marbles}')
            return

        # Get match_info and validate
        match_info = ma.get_match(ctx, match_id)  # database_operation.get_match_info_by_id(DbHandler.db_cnc, match_id)
        if not match_info:
            await du.code_message(ctx, 'Invalid match id')
            return

        # Check if match is started
        if match_info.active:
            await du.code_message(ctx, 'Match has started and betting is closed')
            return

        # Check if match is accepted
        if not match_info.accepted:
            await du.code_message(ctx, 'You can only bet on matches that both players have accepted')
            return

        # Check to make sure person placing bet is not in the match
        if match_info.challenger == bettor_id or match_info.recipient == bettor_id:
            await du.code_message(ctx, 'You cannot bet on matches you are in')

        # Check to make sure bet_target_id is in match
        if match_info.challenger.id != bet_target_id:
            if match_info.recipient.id != bet_target_id:
                await du.code_message(ctx, 'Player is not in this match')
                return

        # Get bet_id if exists,
        bet_id = database_operation.find_bet(DbHandler.db_cnc, match_id, bettor_id)

        # If bet exists, and marbles is zero delete bet
        if bet_id != 0:
            # Get bet with bet_id if it's not zero
            bet_info = bets.get_bet(ctx, bet_id)

            if marbles == 0:
                # Delete bet, and return marbles to bettor
                bet_info.delete_bet()
                bettor_acc.marbles += bet_info.amount
                await du.code_message(ctx, 'Bet deleted')
                return

            # Update bet
            # Add marbles back to user, then subtract the new amount
            bettor_acc.marbles += bet_info.amount
            bettor_acc.marbles -= marbles
            bet_info.bet_target = bet_target_acc
            bet_info.amount = marbles
            await du.code_message(ctx, 'Bet updated')
            return

        # Return if marbles is less than 1
        if marbles < 1:
            await du.code_message(ctx, 'Cannot be zero')
            return

        # Create bet
        bets.create_bet(ctx, None, marbles, match_info, bettor_acc, bet_target_acc)

        await du.code_message(ctx, 'Bet submitted')

    @bet.error
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
    bot.add_cog(BetCog(bot))
