from __future__ import annotations

from typing import TYPE_CHECKING, Any

import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 

import config

import asyncpg
from discord.ext import commands
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import Engine
from bot import Sentinel

async def async_sqlalchemy() -> None:
    return create_async_engine(
        config.postgresql_sqlalchemy_docker,
        # if you don't plan to use docker comment the line above and uncomment the line below ( # 25)
        # config.postgresql_sqlalchemy,
        echo=True,
    )

async def create_pool() -> asyncpg.Pool:

    return await asyncpg.create_pool(
        config.postgresql_docker,
        # if you don't plan to use docker comment the line above and uncomment the line below ( # 34)
        # config.postgresql
        command_timeout=60,
        max_size=20,
        min_size=20,
    )  # type: ignore

class PostgresDriver(commands.Context):
    bot: Sentinel

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.engine: Engine = self.bot.engine

    @property
    def db(self):
        return self.engine  # type: ignore