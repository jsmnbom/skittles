from tortoise.models import Model
from tortoise import fields
import discord
import urllib.parse


class Event(Model):
    id = fields.BigIntField(pk=True)
    description = fields.TextField(null=True)
    when = fields.DatetimeField(null=True)
    title = fields.CharField(max_length=256, null=True)
    image_url = fields.CharField(max_length=256, null=True)
    where = fields.CharField(max_length=256, null=True)
    posted = fields.JSONField(default=[])

    def __str__(self):
        return 'Event[{}]'.format(self.id)

    @property
    def embed(self):
        embed = discord.Embed()
        #embed.set_author(name='LGBT Ungdom Aarhus')
        if self.title:
            embed.title = self.title
        if self.description:
            embed.description = self.description + '\n\u200b'
        if self.when:
            embed.add_field(
                name='Dato', value=self.when.strftime('%a, %-d %B'))
            embed.add_field(name='Tidspunkt',
                            value=self.when.strftime('%H:%M'))
        if self.where:
            where_url = f'https://www.google.com/maps/search/{urllib.parse.quote_plus(self.where)}'
            embed.add_field(name='Sted', value=f'[{self.where}]({where_url})')
            embed.add_field(name='\u200b', value='\u200b')
        if self.image_url:
            embed.set_image(url=self.image_url)
        embed.add_field(name='\u200b', value='\u200b')
        embed.add_field(name='Kommer du?',
                        value='Klik på :heart_eyes: under beskeden!', inline=False)
        embed.add_field(name='Interesseret? (modtag besked når vi nærmer os)',
                        value='Klik på :eyes: under beskeden!', inline=False)
        return embed
