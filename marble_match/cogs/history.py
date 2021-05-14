import asyncio
import math
import datetime
import logging
from typing import Union

import pytz
import discord
from discord.ext import commands

from database.database_setup import DbHandler
import utils.discord_utils as du
import utils.account as acc
import utils.matches as ma
import utils.bets as bets
import utils.exception as exception

logger = logging.getLogger(f'marble_match.{__name__}')


class HistoryCog(commands.Cog, name='History'):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def utc_to_est(date: datetime.datetime):
        """Returns datetime converted from utc to est

        **Arguments**
        - `<date>` utc date to be converted to est

        """
        date2 = date.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Eastern'))
        return pytz.timezone('US/Eastern').normalize(date2)

    def generate_match_text(self, match: ma.Match) -> str:
        return_text = ''
        # Append match amount
        return_text += f'{match.amount}\t'
        # If challenger is winner, append crown
        if match.challenger.id == match.winner.id:
            return_text += f'♕'
        # Append challenger display name and vs
        return_text += f'{match.challenger.nickname}\t vs \t'
        # If recipient is winner, append crown
        if match.recipient.id == match.winner.id:
            return_text += f'♕'
        # Append recipient display name
        return_text += f'{match.recipient.nickname}\t'
        # Append game[format]
        return_text += f'{match.full_game}\t'
        # Append match time
        return_text += f'{self.utc_to_est(match.match_time).strftime("%x %X")}\n'

        return return_text

    def generate_bet_text(self, bet: bets.Bet):
        return_text = ''
        # Append bet amount
        return_text += f'{bet.amount}\t'
        # Append bet_target
        return_text += f'{bet.bet_target.nickname}\t'
        # Append won or lost
        if bet.bet_target.id == bet.winner.id:
            return_text += 'Won\t'
        else:
            return_text += 'Lost\t'
        # Append bet_time
        return_text += f'{self.utc_to_est(bet.bet_time).strftime("%x %X")}\n'

        return return_text

    @commands.command(name='match_history', help='Prints out a users match history')
    @commands.guild_only()
    async def match_history(self, ctx: commands.Context, member: Union[discord.Member, str] = None,
                            vs: Union[discord.Member, str] = None):
        """Show match history of user.

        Example:
             - `$match_history @Sophia'
             - `$match_history @Ness'
             - `$match_history @Sophia @Ness'

        **Arguments**

        - `<member>` The user to show the match history of. If omitted, defaults to your own history.
        - `<vs>` The user to limit the match history to only games with them

        """
        logger.debug(f'match_history: {member}, {vs}')

        # Declare player2 as none for failsafe with ma.get_matches_all
        player2 = None

        # Check if member is None, if it is, set member to ctx.author
        if not member:
            member = ctx.author
        # Check if vs exists, get player2 if it does
        if vs:
            player2 = acc.get_account(ctx, DbHandler.db_cnc, vs)

        # Get player1 and their match history
        player1 = acc.get_account(ctx, DbHandler.db_cnc, member)
        match_history = ma.get_matches_all(ctx, player1, player2, True)

        # Check if match_history is not 0
        if not match_history:
            await du.code_message(ctx, 'No match history')
            return

        # Instantiate text and match_list to be appended later
        text = ''
        match_list = match_history

        # Set pages to amount of match_list/10 in an even amount, cur_page to last page, and active to true
        text = ''
        pages = math.ceil(len(match_list)/10)
        cur_page = pages-1
        # Used to loop waiting for a react
        active = True

        # Generate page from match_list
        for i in range(cur_page*10, (cur_page*10) + 10):
            if i < len(match_list):
                text += self.generate_match_text(match_list[i])  # text += str(match_list[i])

        # If pages is greater than one, add a page counter, if not set active to False
        if pages > 1:
            text += f'Page {cur_page+1} of {pages}\n'
        else:
            active = False

        # Create message with return of du.code_message
        message = await du.code_message(ctx, text)

        # If pages greater than one, add reaction controls
        if pages > 1:
            await message.add_reaction('\U00002B05')  # ⬅️
            await message.add_reaction('\U000027A1')  # ➡️

        # Method to check if react is the correction with the correct user
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['\U00002B05', '\U000027A1']

        # While loop
        while active:
            try:
                # page set to start of codeblock
                page = '```\n'
                # wait till we get a reaction, fill reaction, user with output of 'reaction_add'
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)
                # If reaction is left and cur_page is greater than 0
                if str(reaction.emoji) == '\U00002B05' and cur_page > 0:  # ⬅️️
                    # Set current page to one less than current
                    cur_page -= 1

                    # For range of pages for current list append match_list to page
                    for i in range(cur_page*10, cur_page*10 + 10):
                        page += self.generate_match_text(match_list[i])  # match_list[i]

                    # Add page counter and edit message with page
                    page += f'Page {cur_page+1} of {pages}\n```'
                    await message.edit(content=page)

                    # Remove users reaction
                    await message.remove_reaction(reaction, user)

                # If reaction is right and cur_page is less than pages-1
                elif str(reaction.emoji) == '\U000027A1' and cur_page < pages-1:  # ➡️
                    # Set current page to one more than current
                    cur_page += 1

                    # For range of pages for current list append match_list to page
                    for i in range(cur_page*10, cur_page*10 + 10):
                        if i < len(match_list):
                            page += self.generate_match_text(match_list[i])  # match_list[i]

                    # Add page counter and edit message with page
                    page += f'Page {cur_page+1} of {pages}\n```'
                    await message.edit(content=page)

                    # Remove users reaction
                    await message.remove_reaction(reaction, user)
                else:
                    # Remove reaction if it's anything else
                    await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                # When 'reaction_add' throws exception, set active to False to end loop
                active = False
                # Get cached message to remove reactions
                cached_msg = discord.utils.get(self.bot.cached_messages, id=message.id)
                for reactions in cached_msg.reactions:
                    await reactions.remove(self.bot.user)

    @match_history.error
    async def generic_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await du.code_message(ctx, f"You're missing required argument: {error.param.name}", 3)
            await ctx.send_help('match_history')
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

    @commands.command(name='bet_history', help='Prints out a users bet history')
    @commands.guild_only()
    async def bet_history(self, ctx, member: Union[discord.Member, str] = None,
                          bet_target: Union[discord.Member, str] = None):
        """Prints bet history of user

        Examples:
             - `$bet_history @Sophia'
             - `$bet_history @Ness'
             - `$bet_history @Sophia @Ness'

        **Arguments**

        - `<member>` The user to who's bet history you want to print. If omitted defaults to your own history.
        - '<bet_target>' The user you want to limit bets on to.

        """
        logger.debug(f'bet_history: {member}, {bet_target}')

        # Declare bet_target_acc as failsafe for bets.get_bet_all
        bet_target_acc = None
        # If member is None set member to ctx.author
        if not member:
            member = ctx.author
        # If bet_target is not None, get bet_target info for specific search
        if bet_target:
            bet_target_acc = acc.get_account(ctx, DbHandler.db_cnc, bet_target)

        # Get bettor info and bet_history
        bettor = acc.get_account(ctx, DbHandler.db_cnc, member)
        bet_history = bets.get_bet_all(ctx, bettor, bet_target_acc, True)

        # Check if bet_history is filled
        if not bet_history:
            await du.code_message(ctx, 'No bet history')
            return

        # Create variables to be appended
        text = ''
        bet_list = bet_history
        # Set pages to bet_list/10 even, cur_page to pages-1 and active to True
        pages = math.ceil(len(bet_list)/10)
        cur_page = pages-1
        active = True

        # Generate first page to be displayed with cur_page
        for i in range(cur_page*10, (cur_page*10) + 10):
            if i < len(bet_list):
                text += self.generate_bet_text(bet_list[i])

        # If pages is greater than one, append a page counter
        if pages > 1:
            text += f'Page {cur_page+1} of {pages}\n'
        else:
            active = False

        # Send message
        message = await du.code_message(ctx, text)

        # If pages is greater than one add reactions for control
        if pages > 1:
            await message.add_reaction('\U00002B05')
            await message.add_reaction('\U000027A1')

        # Function to check if reaction = ctx.author
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['\U00002B05', '\U000027A1']

        # loop for reaction controls
        while active:
            try:
                # Set page to start of codeblock
                page = '```\n'
                # wait till we get a reaction, fill reaction, user with output of 'reaction_add'
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=check)
                # Check if reaction is left, and cur_page greater than zero
                if str(reaction.emoji) == '\U00002B05' and cur_page > 0:  # ⬅️
                    # Set cur_page to current value minus one
                    cur_page -= 1

                    # Generate current page with cur_page
                    for i in range(cur_page*10, cur_page*10 + 10):
                        page += self.generate_bet_text(bet_list[i])  # bet_list[i]

                    # Append page counter and edit message with page
                    page += f'Page {cur_page+1} of {pages}\n```'
                    await message.edit(content=page)
                    # Remove user reaction
                    await message.remove_reaction(reaction, user)
                # Check if reaction is right, and cur_page less than pages-1
                elif str(reaction.emoji) == '\U000027A1' and cur_page < pages-1:  # ➡️
                    # Set cur_page to current value plus one
                    cur_page += 1

                    # Generate current page with cur_page
                    for i in range(cur_page*10, cur_page*10 + 10):
                        if i < len(bet_list):
                            page += self.generate_bet_text(bet_list[i])  # bet_list[i]

                    # Append page counter and edit message with page
                    page += f'Page {cur_page+1} of {pages}\n```'
                    await message.edit(content=page)
                    # Remove user reaction
                    await message.remove_reaction(reaction, user)
                else:
                    await message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                # When 'reaction_add' gets a timeout, set active to false to end loop
                active = False
                # Get cached message to remove all reactions
                cached_msg = discord.utils.get(self.bot.cached_messages, id=message.id)
                for reactions in cached_msg.reactions:
                    await reactions.remove(self.bot.user)

    @bet_history.error
    async def generic_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await du.code_message(ctx, f"You're missing required argument: {error.param.name}", 3)
            await ctx.send_help('bet_history')
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
    bot.add_cog(HistoryCog(bot))
