from tortoise import Tortoise
from .models import Event
import discord
import logging

logger = logging.getLogger('db')


async def init():
    logger.debug('Init start')
    await Tortoise.init(
        db_url='sqlite://../db.sqlite3',
        modules={'models': ['db.models']}
    )

    await Tortoise.generate_schemas(safe=True)

    logger.info('Connected')

async def close():
    logger.info('Closing connection')
    await Tortoise.close_connections()