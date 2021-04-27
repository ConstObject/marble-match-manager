import discord
import database
import database_operation


async def code_message(ctx, text, color=0):
    await ctx.send(f'```\n{text}```')


def get_member_by_player_id(ctx, connection, player_id):

    player_info = database_operation.get_player_info(connection, player_id)

    if player_info is None:
        return 0

    for member in ctx.guild.members:
        if str(member) == player_info[1]:
            return member

    return 0
