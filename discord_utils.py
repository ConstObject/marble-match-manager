import discord


async def code_message(ctx, text):
    await ctx.send(f'```\n{text}```')
