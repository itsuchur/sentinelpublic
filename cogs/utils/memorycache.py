import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 

import config

from redis import asyncio as aioredis


async def create_redis_pool():
    return aioredis.from_url(config.redis_docker)
    # if you don't plan to use docker comment the line above and uncomment the line below ( # 17)
    # return aioredis.from_url(config.redis)