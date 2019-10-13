import db
import cogs
from dotenv import load_dotenv
import os
import discord
from discord.ext import commands
import asyncio

import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

load_dotenv()


class SkittlesContext(commands.Context):
    pass


class SkittlesBot(commands.Bot):
    class Help(discord.ext.commands.DefaultHelpCommand):
        def __init__(self):
            super().__init__()
            self.no_category = 'Other'

        def get_command_signature(self, command):
            parent = command.full_parent_name
            if len(command.aliases) > 0:
                aliases = '|'.join(command.aliases)
                fmt = '[%s|%s]' % (command.name, aliases)
                if parent:
                    fmt = parent + ' ' + fmt
                alias = fmt
            else:
                alias = command.name if not parent else parent + ' ' + command.name

            if command.signature is str:
                return '%s%s %s' % (self.clean_prefix, alias,
                                    command.signature)
            else:
                return '\n'.join('%s%s %s' %
                                 (self.clean_prefix, alias, signature)
                                 for signature in command.signature)

    def __init__(self):
        super().__init__(command_prefix='|', help_command=self.Help())

        self.loop.create_task(self.db_task())

        for cog in map(cogs.__dict__.get, cogs.__all__):
            self.add_cog(cog(self))

    async def on_ready(self):
        logging.info('Logged in as %s (%s) ', self.user.name, bot.user.id)
        await self.change_presence(status=discord.Status.online,
                                   activity=discord.Game("|help"))

    async def db_task(self):
        try:
            await db.init()
            while not self.is_closed():
                await asyncio.sleep(60)
        finally:
            await db.close()

    async def get_context(self, message):
        return await super().get_context(message, cls=SkittlesContext)

    async def on_message(self, message):
        await self.invoke(await self.get_context(message))

    async def send_help(self, ctx, help_subcommand=''):
        new_msg = ctx.message
        new_msg.content = '{}help {}'.format(await self.get_prefix(new_msg),
                                             help_subcommand)
        new_ctx = await self.get_context(new_msg)
        await self.invoke(new_ctx)


if __name__ == '__main__':
    bot = SkittlesBot()
    bot.run(os.getenv('DISCORD_BOT_TOKEN'))
