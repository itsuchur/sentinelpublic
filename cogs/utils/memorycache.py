import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 

import config

from redis import asyncio as aioredis


async def create_redis_pool():
    return aioredis.from_url(config.redis)  # host.docker.internal // redis://redis:6379