from __future__ import annotations
from typing import TypedDict

import logging
from logging.handlers import RotatingFileHandler
import asyncio
import sys
import discord
import click
import contextlib
from cogs.utils import db, memorycache

from bot import Sentinel

try:
    import uvloop  # type: ignore
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

class RemoveNoise(logging.Filter):
    def __init__(self):
        super().__init__(name='discord.state')

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelname == 'WARNING' and 'referencing an unknown' in record.msg:
            return False
        return True

@contextlib.contextmanager
def setup_logging():
    log = logging.getLogger()

    try:
        discord.utils.setup_logging()
        # __enter__
        max_bytes = 32 * 1024 * 1024  # 32 MiB
        logging.getLogger('discord').setLevel(logging.INFO)
        logging.getLogger('discord.http').setLevel(logging.WARNING)
        logging.getLogger('discord.state').addFilter(RemoveNoise())

        log.setLevel(logging.INFO)
        handler = RotatingFileHandler(filename='sentinel.log', encoding='utf-8', mode='w', maxBytes=max_bytes, backupCount=5)
        dt_fmt = '%Y-%m-%d %H:%M:%S'
        fmt = logging.Formatter('[{asctime}] [{levelname:<7}] {name}: {message}', dt_fmt, style='{')
        handler.setFormatter(fmt)
        log.addHandler(handler)

        yield
    finally:
        # __exit__
        handlers = log.handlers[:]
        for hdlr in handlers:
            hdlr.close()
            log.removeHandler(hdlr)

async def run_bot():
    log = logging.getLogger()
    try:
        engine = await db.async_sqlalchemy()
        pool = await db.create_pool()
        memcache = await memorycache.create_redis_pool()
    except Exception:
        click.echo('Could not set up PostgreSQL or Redis. Exiting.', file=sys.stderr)
        log.exception('Could not set up PostgreSQL or Redis. Exiting.')
        return

    async with Sentinel() as bot:
        bot.engine = engine
        bot.pool = pool
        bot.memcache = memcache
        await bot.start()

@click.group(invoke_without_command=True, options_metavar='[options]')
@click.pass_context
def main(ctx):
    """Launches the bot."""
    if ctx.invoked_subcommand is None:
        with setup_logging():
            asyncio.run(run_bot())

if __name__ == '__main__':
    main()

