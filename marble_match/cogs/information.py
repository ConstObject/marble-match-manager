import logging
from urllib.request import urlopen

import discord
from discord.ext import commands

import utils.discord_utils as du

logger = logging.getLogger(f'marble_match.{__name__}')


class InfoCog(commands.Cog, name='Information'):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='info', help='Prints latest version info')
    async def info(self, ctx: commands.Context):
        url_results = urlopen('https://constobject.github.io/change_log')
        text = str(url_results.read().decode('utf-8'))
        await du.code_message(ctx, text)

    @commands.command(name='bug', help='Prints link to submit bug report')
    async def bug(self, ctx: commands.Context):
        embed = discord.Embed(title='Bug Report', url='https://github.com/ConstObject/marble-match-manager/issues/new',
                              description='Submit a bug report here, or dm Sophia', colour=discord.Colour.red())
        await ctx.send(embed=embed)

    @commands.command(name='idea', help='Prints link to submit an idea or feature')
    async def idea(self, ctx: commands.Context):
        embed = discord.Embed(title='Idea/Feature',
                              url=f'https://docs.google.com/forms/d/e/'
                                  f'1FAIpQLSf6_YTifMPgkX-0sjckxNH9zTe-GR6PhjAXcJJcYmEa13wWcw/viewform?entry.1915960491='
                                  f'{ctx.author.name}#{ctx.author.discriminator}',
                              description='Form to submit features/ideas',
                              colour=discord.Colour.dark_purple())
        await ctx.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(InfoCog(bot))
