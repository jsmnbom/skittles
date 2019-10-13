import sys
from discord.ext import commands
import discord
import logging

# https://gist.github.com/EvieePy/7822af90858ef65012ea500bcecf1612


class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, 'on_error'):
            return

        ignored = (commands.CommandNotFound, commands.UserInputError)
        error = getattr(error, 'original', error)

        if isinstance(error, ignored):
            return

        elif isinstance(error, commands.DisabledCommand):
            return await ctx.send(f'{ctx.command} has been disabled.',
                                  delete_after=5)

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.author.send(
                    f'{ctx.command} can not be used in Direct Messages.')
            except:
                pass

        elif isinstance(error, commands.MissingAnyRole):
            return await ctx.send(str(error), delete_after=5)

        elif isinstance(error, commands.BadArgument):
            if ctx.command.qualified_name == 'tag list':
                return await ctx.send(
                    'I could not find that member. Please try again.',
                    delete_after=5)

        logging.error('Ignoring exception in command {}:'.format(ctx.command),
                      exc_info=error)
