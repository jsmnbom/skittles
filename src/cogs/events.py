import discord
from discord.ext import commands
from datetime import datetime
from dateutil import parser
import aiohttp
import io
from PIL import Image, ImageOps, ImageEnhance
import textwrap
from slugify import slugify
import asyncio

import db



class CancelledException(Exception):
    pass


class EventValueConverter(commands.Converter):
    async def convert(self, ctx, argument):
        if argument in ('desc', 'description'):
            return 'description'
        elif argument == 'title':
            return 'title'
        elif argument == 'when':
            return 'when'
        elif argument == 'where':
            return 'where'
        elif argument in ('img', 'image'):
            return 'image'
        raise commands.BadArgument


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    @commands.has_any_role('Bestyrelse')
    async def events(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.bot.send_help(ctx, 'events')

    async def send_wait_for_reply(self, ctx, text):
        sent_msg = await ctx.send(text + ' *(send a ❌ to cancel.)*')

        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author

        received_msg = await self.bot.wait_for('message', check=check)

        await sent_msg.delete()

        if received_msg.content == '❌':
            raise CancelledException

        return received_msg

    async def process_image(self, ctx, url, output):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                buffer = io.BytesIO(await resp.read())
                try:
                    with Image.open(buffer) as bg:
                        bg = ImageOps.fit(bg, (1000, 500))
                        enhancer = ImageEnhance.Brightness(bg)
                        bg = enhancer.enhance(0.8)
                        logo = Image.open('cogs/logo.png', 'r')
                        offset = ((bg.width - logo.width),
                                  (bg.height - logo.height))
                        bg.paste(logo, offset, logo)
                        bg.save(output, format="PNG")
                        output.seek(0)
                except IOError:
                    pass

    @events.command()
    @commands.has_any_role('Bestyrelse')
    async def new(self, ctx):
        event = await db.Event.create()

        title_msg = await self.send_wait_for_reply(
            ctx,
            f'`{event.id}`: {ctx.author.mention}, please write a title for the event.'
        )
        event.title = title_msg.content.strip()

        description_msg = await self.send_wait_for_reply(
            ctx,
            f'`{event.id}`: {ctx.author.mention}, please write a description for the event.'
        )
        event.description = description_msg.content.strip()

        when_msg = await self.send_wait_for_reply(
            ctx, f'`{event.id}`: {ctx.author.mention}, when is the event?')

        default_when = datetime.now().replace(hour=19,
                                              minute=0,
                                              second=0,
                                              microsecond=0)
        when = None
        while when is None:
            try:
                when = parser.parse(when_msg.content,
                                    ignoretz=True,
                                    dayfirst=True,
                                    default=default_when)
            except (ValueError, OverflowError):
                when_msg = await self.send_wait_for_reply(
                    ctx,
                    f'`{event.id}`: {ctx.author.mention}, time and/or date not understood, try again.'
                )
        event.when = when

        where_msg = await self.send_wait_for_reply(
            ctx,
            f'`{event.id}`: {ctx.author.mention}, where is the event? (send a 🌈 for "Sappho, Mejlgade 71, 8000 Aarhus C)'
        )
        where = where_msg.content.strip()
        if where == '🌈':
            where = 'Sappho, Mejlgade 71, 8000 Aarhus C'
        event.where = where

        image_msg = await self.send_wait_for_reply(
            ctx,
            f'`{event.id}`: {ctx.author.mention}, please send an image or an url to a image to use for the event.'
        )
        if image_msg.attachments:
            raw_image_url = image_msg.attachments[0].url
        else:
            raw_image_url = image_msg.content.strip()
        with io.BytesIO() as image_io:
            await self.process_image(ctx, raw_image_url, image_io)

            embed = event.embed
            image_filename = slugify(event.title,
                                     regex_pattern=r'[^-a-z0-9\-æøåÆØÅ]+')
            embed.set_image(url=f"attachment://{image_filename}.png")
            sent_embed_msg = await ctx.send(
                f'Event created! Event id: `{event.id}`.\nPreview embed (do not delete):',
                embed=embed,
                file=discord.File(image_io, f'{image_filename}.png'))

        event.image_url = sent_embed_msg.embeds[0].image.url
        await event.save()

    @events.command(usage=[
        '<event_id> title <new_title>',
        '<event_id> description <new_description>',
        '<event_id> when <new_when>', '<event_id> where <new_where>',
        '<event_id> image [new_image_url]'
    ])
    @commands.has_any_role('Bestyrelse')
    async def edit(self,
                   ctx,
                   event_id: int = None,
                   what: EventValueConverter = None,
                   *,
                   new_value: str = None):
        if event_id is None or what is None or (what != 'image'
                                                and new_value is None):
            await self.bot.send_help(ctx, 'events edit')
            return

        event = await db.Event.get(id=event_id)

        if what == 'title':
            event.title = new_value
        elif what == 'description':
            event.description = new_value
        elif what == 'when':
            try:
                when = parser.parse(new_value,
                                    ignoretz=True,
                                    dayfirst=True,
                                    default=datetime.now().replace(
                                        hour=19,
                                        minute=0,
                                        second=0,
                                        microsecond=0))
            except (ValueError, OverflowError):
                await ctx.send(
                    f'{ctx.author.mention}, time and/or date not understood.')
                return
            event.when = when
        elif what == 'where':
            event.where = new_value
        elif what == 'image':
            if ctx.message.attachments:
                raw_image_url = ctx.message.attachments[0].url
            else:
                raw_image_url = new_value.strip()
            with io.BytesIO() as image_io:
                await self.process_image(ctx, raw_image_url, image_io)

                embed = event.embed
                image_filename = slugify(event.title,
                                         regex_pattern=r'[^-a-z0-9\-æøåÆØÅ]+')
                embed.set_image(url=f"attachment://{image_filename}.png")
                sent_embed_msg = await ctx.send(
                    f'Event updated! Event id: `{event.id}`.\nPreview embed (do not delete):',
                    embed=embed,
                    file=discord.File(image_io, f'{image_filename}.png'))
            event.image_url = sent_embed_msg.embeds[0].image.url
            await event.save()
            return

        await event.save()

        await ctx.send('Event updated!\nPreview embed (do not delete):',
                       embed=event.embed)

        for [chan_id, msg_id] in event.posted:
            try:
                channel = ctx.bot.get_channel(chan_id)
                message = await channel.fetch_message(msg_id)
                await message.edit(embed=event.embed)
            except discord.NotFound:
                pass

    @events.command()
    async def post(self, ctx, event_id: int, channel: discord.TextChannel):
        event = await db.Event.get(id=event_id)

        msg = await channel.send(embed=event.embed)

        event.posted.append([channel.id, msg.id])
        await event.save()

        await msg.add_reaction('😍')
        await asyncio.sleep(0.5)
        await msg.add_reaction('👀')
