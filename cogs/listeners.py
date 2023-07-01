# -*- coding: utf-8 -*-

#   from .utils import database
import discord
from discord.ext import commands
#   from discord.ext import tasks

from cogs.utils import models

from sqlalchemy import delete

from bot import Sentinel

import logging

log = logging.getLogger(__name__)

class Listeners(commands.Cog):
    __slots__ = ('bot')

    def __init__(self, bot):
        self.bot: Sentinel = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Defines what the bot does when a member joins the server"""

        if member.bot == True:
            return

        async with self.bot.pool.acquire() as connection:
            query = "INSERT INTO t_users(guild_id, member_id, member_created_at, member_joined_at) VALUES($1, $2, $3, $4) ON CONFLICT (guild_id, member_id) DO UPDATE SET member_joined_at = EXCLUDED.member_joined_at;"

            await connection.execute(query, member.guild.id, member.id, member.created_at, member.joined_at)

        guild_id = member.guild.id
        member_created_at = member.created_at

        anti_raid = self.bot.get_cog('Antiraid')

        async with self.bot.memcache.client() as redisConn:
            autoban_mode = await redisConn.hget(guild_id, "guild_autoban")

        """Checking whether or not autoban is enabled on server the user just joined"""

        if anti_raid is not None and int(autoban_mode) == 1: # explicitly converting str (since Redis return a string) to int for comparison
            await anti_raid.get_guild_params(guild_id, member_created_at)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """Defines what the bot does when member leaves the server.
        Here we're telling PostgreSQL to update its records. """

        async with self.bot.pool.acquire() as connection:
            query = "UPDATE t_users SET member_left_at = NOW() WHERE guild_id = $1 AND member_id = $2;"
            await connection.execute(query, member.guild.id, member.id)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):

        t_guild = models.Guild.__table__

        overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True),
                }

        channel = await guild.create_text_channel("sentinel", overwrites=overwrites)

        # guild = models.Guild(guild_id=guild.id, guild_notification_channel=channel.id, guild_bot_present=True)

        async with self.bot.engine.connect() as conn:
            await conn.execute(t_guild.insert().values(
            guild_id=guild.id,
            guild_autoban=False,
            guild_interval=30,
            guild_hours=6,
            guild_min_members=2,
            guild_notification_channel=channel.id,
            guild_bot_present=True,
            guild_url_filter=False
        ))
            await conn.commit()

        async with self.bot.memcache.client() as redisConn:
            new_server = {"guild_id":guild.id, 
                         "guild_autoban":0, 
                         "guild_interval":30, 
                         "guild_hours":6, 
                         "guild_min_members":2,"guild_notification_channel":channel.id, "guild_bot_present":1,
                         "guild_url_filter":0
                         }
            await redisConn.hmset(guild.id, new_server)

        log.info(f"Added an entry to Postgresql db. Reason: bot joined the guild {guild.id}")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """
        Deleting all records associated with the guild both from the database and Redis cache
        """

        t_guild = models.Guild.__table__

        async with self.bot.engine.connect() as conn:
            # stmt = delete(t_guild).where(t_guild.c.guild_id == guild_id)
            await conn.execute(delete(t_guild).where(t_guild.c.guild_id == guild.id))
            await conn.commit()

        async with self.bot.memcache.client() as redisConn:
            await redisConn.delete(guild.id)

        log.info(f"Deleted an entry from Postgresql. Reason: bot left the guild {guild.id}")


async def setup(bot):
    await bot.add_cog(Listeners(bot))