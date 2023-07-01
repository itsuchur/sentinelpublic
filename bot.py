from __future__ import annotations

from discord.ext import commands
import sqlalchemy
import discord

import logging

import aiohttp

from typing import TYPE_CHECKING, Any, AsyncIterator, Callable, Coroutine, Iterable, Optional, Union

import asyncpg
import config
from redis import asyncio as aioredis

log = logging.getLogger(__name__)

initial_extensions = (
    'cogs.commands',
    'cogs.antiraid',
    'cogs.listeners',
    'cogs.slashcommands',
    'cogs.scheduledtasks',
    'cogs.wowhead',
    'cogs.cache',
    'cogs.views',
    'cogs.sol'
)

class Sentinel(commands.Bot):
    user: discord.ClientUser
    engine: sqlalchemy.Engine
    pool: asyncpg.Pool
    memcache: aioredis.Redis
    bot_app_info: discord.AppInfo

    def __init__(self):
        allowed_mentions = discord.AllowedMentions(roles=False, everyone=False, users=True)
        intents = discord.Intents(
            guilds=True,
            members=True,
            bans=True,
            messages=True,
            message_content=True,
        )
        super().__init__(
            command_prefix="st?",
            description="a custom antiraid bot",
            pm_help=None,
            help_attrs=dict(hidden=True),
            chunk_guilds_at_startup=False,
            heartbeat_timeout=150.0,
            allowed_mentions=allowed_mentions,
            intents=intents,
            enable_debug_events=True,
        )

        self.client_id: str = config.client_id
        self.version: str = 'v. 7.0'

    async def setup_hook(self):

        self.session = aiohttp.ClientSession()

        self.bot_app_info = await self.application_info()
        self.owner_id = self.bot_app_info.owner.id

        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
                log.info(f"An extension {extension} successfully loaded.")
            except Exception as e:
                log.exception(f'Failed to load an extension {extension}. Error: {e}.')

        await self.load_server_settings_to_memory()

    @property
    def owner(self) -> discord.User:
        return self.bot_app_info.owner

    async def load_server_settings_to_memory(self):

        async with self.pool.acquire() as sql_connection:
            query = "SELECT * FROM t_guilds"
            query = await sql_connection.fetch(query)

        # self.servers_count = len(query[0])

        async with self.memcache.client() as redis_connection:
            for each_server in query:
                # each_server_to_dict = [dict[x] for x in each_server]

                each_server_to_dict = {
                    "guild_id": each_server[0],  # 0
                    "guild_autoban": int(each_server[1]),
                    "guild_interval": each_server[2],
                    "guild_hours": each_server[3],
                    "guild_min_members": each_server[4],
                    "guild_notification_channel": each_server[5],
                    "guild_bot_present": int(each_server[6]),
                    "guild_url_filter": int(each_server[7])  # 7
                }

                await redis_connection.hset(each_server[0], mapping=each_server_to_dict)

            log.info("Settings have been cached.")

    async def on_ready(self):
        log.info('Ready: %s (ID: %s)', self.user, self.user.id)

    async def process_commands(self, message: discord.Message):
        ctx = await self.get_context(message)

        if ctx.command is None:
            return
        
        await self.invoke(ctx)

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        await self.process_commands(message)

    async def close(self) -> None:
        await super().close()
        await self.session.close() # closing aiohttp connection

        # closing Postgres pools

        await self.pool.close() # close and clean-up pooled connections to Postgres created by Asyncpg lib. To be
        # replaced w/ SQLAlchemy
        await self.engine.dispose() # close and clean-up pooled connections to Postgres created by SQLAlchemy

        # closing Redis pool
        self.memcache.close()
        await self.memcache.wait_closed()

    async def start(self) -> None:
        await super().start(config.token, reconnect=True)

    @property
    def config(self):
        return __import__('config')
