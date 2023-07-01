# -*- coding: utf-8 -*-

from __future__ import annotations
from typing import Dict

import datetime
import discord
import logging
from discord.ext import commands
from discord.utils import format_dt

from sqlalchemy import select

from cogs.utils import models

from bot import Sentinel

# dummy sql request
# SELECT member_id from t_users WHERE CAST (member_created_at AS TIMESTAMP WITH TIME ZONE) BETWEEN 2023-05-19 15:30:00 AND 2023-05-19 18:30:00 AND member_joined_at >= NOW() - interval '30 minutes' AND guild_id = 1234567890 AND is_whitelisted = FALSE ORDER BY member_id DESC;

log = logging.getLogger(__name__)

class Antiraid(commands.Cog):
    __slots__ = ('bot')

    def __init__(self, bot):
        self.bot: Sentinel = bot

    async def cog_unload(self):
        return super().cog_unload()

    async def get_guild_params(self, guild_id: int, member_created_at: datetime.datetime) -> Dict:

        """Getting server's settings from Redis cache"""
        async with self.bot.memcache.client() as redisConn:
            guild_params = await redisConn.hgetall(guild_id)

        guild_params = {
            "guild_id": guild_id,
            "guild_interval": guild_params["guild_interval"],
            "guild_threshold": guild_params["guild_min_members"],
            "guild_hours": guild_params["guild_hours"],
            "guild_notification_channel": guild_params["guild_notification_channel"]
        }

        guild_params = dict((k, int(v)) for k, v in guild_params.items())  # converting str from Redis to int

        await self.verification(guild_params, member_created_at)

    async def verification(self, guild_params: Dict, member_created_at: datetime.datetime) -> None:

        minus_hours = member_created_at - datetime.timedelta(hours=guild_params.get("guild_hours"))
        plus_hours = member_created_at + datetime.timedelta(hours=guild_params.get("guild_hours"))

        async with self.bot.pool.acquire() as connection:

            query = f"""SELECT member_id from t_users WHERE CAST (member_created_at AS TIMESTAMP WITH TIME ZONE) 
            BETWEEN $1 AND $2 AND member_joined_at >= NOW() - interval '{guild_params.get("guild_interval")} minutes' 
            AND guild_id = $3 AND is_whitelisted = FALSE ORDER BY member_id DESC; """

            query = await connection.fetch(query, minus_hours, plus_hours, guild_params.get("guild_id"))

            query = [r['member_id'] for r in query]

        if len(query) >= guild_params.get("guild_threshold"):  # if len of the query exceed the limit set by server's admin then proceed with execution of the script

            guild = self.bot.get_guild(guild_params.get("guild_id"))

            redis_key = f"{guild.id}:users:banned" # creating a redis key to use later to associate the key with the server

            redis_key_timestamp = f"{guild.id}:users:banned:time"

            channel = guild.get_channel(guild_params.get("guild_notification_channel"))

            for suspicious_account in query:

                try:

                    suspicious_account = self.bot.get_user(int(suspicious_account))

                    async with self.bot.memcache.client() as redisConn:

                        # banned_users = redisConn.lrange(redis_key, 0, -1)

                        if await redisConn.lpos(redis_key, suspicious_account.id) is not None: # if redis found the user's ID in a list of previously banned users, then jump to next iteration. Otherwise proceed with further execution of the script

                            continue

                    # if suspicious_account in guild.members:

                    await guild.ban(user=discord.Object(id=suspicious_account.id), reason="ANTI-RAID: suspicious or spam account.")

                    async with self.bot.memcache.client() as redisConn:

                        await redisConn.rpush(redis_key, suspicious_account.id) # adding id to the list of banned users to reduce amount of calls to Discord's API

                        await redisConn.set(redis_key_timestamp, str(datetime.datetime.now()))
                        
                        # await redisConn.expire(redis_key, 3600) # setting an expire time for the key (server's ID:users:banned) (1 hour)

                    if channel in guild.channels: # sending an alert to server's moderators given the server has designated alert channel

                        """Sending discord.Embed"""
                        embed = discord.Embed(title=f"{suspicious_account} | Spam Raid",
                                                description=f"Spam activity detected. The account is now banned.",
                                                color=0xed4337,
                                                timestamp=discord.utils.utcnow())
                        embed.set_author(name=f"{suspicious_account.id} | Spam Raid",
                                            icon_url=suspicious_account.display_avatar.url)
                        embed.set_thumbnail(url=suspicious_account.display_avatar.url)
                        embed.add_field(name="ID", value=f"{suspicious_account.id}", inline=False)
                        embed.add_field(name="Created at",
                                        value=f"{format_dt(suspicious_account.created_at, style='f')} ({format_dt(suspicious_account.created_at, style='R')})",
                                        inline=False)
                        embed.add_field(name='Useful links', value='[Technical Support](https://discord.gg/invite/TVaNvzRu3T) \n [Send Feedback](https://forms.gle/KzHgXC7c16zPWhgo7)', inline=False)
                        embed.set_footer(text=f"Sentinel Bot | {self.bot.version}")

                        await channel.send(embed=embed)

                    else:
                        continue

                    # else:
                    #    continue

                except Exception as e: # discord.NotFound
                    log.warn(f"{e}\nAdditional info:\nServer ID: {guild_params.get('guild_id')}")
                    continue


async def setup(bot):
    await bot.add_cog(Antiraid(bot))
