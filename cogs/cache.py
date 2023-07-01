# -*- coding: utf-8 -*-

#   from .utils import database
import datetime
import discord
import logging
from discord.ext import commands, tasks
#   from discord.ext import tasks

from bot import Sentinel

log = logging.getLogger(__name__)

class RedisCache(commands.Cog):
    __slots__ = ('bot')

    def __init__(self, bot):
        self.bot: Sentinel = bot
        self.find_keys_older_than_5_minutes.start()

    @tasks.loop(minutes=5)
    async def find_keys_older_than_5_minutes(self):
        await self.bot.wait_until_ready()
        # Connect to Redis
        async with self.bot.memcache.client() as redisConn:

            # Get the current timestamp
            current_time = datetime.datetime.now()

            # Process each key
            async for key in redisConn.scan_iter(match='*:users:banned'):
                timestamp_key = key + ":time"
                timestamp = await redisConn.get(timestamp_key)

                # Check if the timestamp is older than 5 minutes
                if timestamp is not None:

                    timestamp = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")

                    time_difference = current_time - timestamp

                    five_minutes = datetime.timedelta(minutes=5)

                    if time_difference >= five_minutes:

                        server_id = key.split(":")[0]
                        value = await redisConn.lrange(key, 0, -1)

                        converted_to_integers = []

                        for user_id in value:
                            converted_to_integers.append(int(user_id))

                        await redisConn.delete(key, key + ":time")

                        await self.store_in_postgresql(server_id, timestamp, converted_to_integers)

    async def store_in_postgresql(self, server_id, last_updated, value):
        # Establish a connection to your PostgreSQL database
        async with self.bot.pool.acquire() as connection:

            # Perform the necessary PostgreSQL operations (e.g., inserting data into a table)
            log_id = await connection.fetchval('INSERT INTO t_logs (guild_id, raid_time, raiders_id) VALUES ($1, $2, $3) RETURNING id;', int(server_id), last_updated, value)

        log.info(f"Added new entry to the table t_logs. Entry ID: {log_id}. Server ID associated with the entry: "
                 f"{server_id}. Sending Discord alert...")

        await self.send_discord_notification(server_id, log_id)

    async def send_discord_notification(self, guild_id, log_id):

        embed = discord.Embed(title=f"Spam Raid Summary",
                              description=f"The userbot raid against this server has been repelled. For more information about the raid, please visit https://logs.itsuchur.dev/id={log_id}.",
                              color=0xed4337, timestamp=discord.utils.utcnow())
        embed.add_field(name='Useful links',
                        value='[Technical Support](https://discord.gg/invite/TVaNvzRu3T) \n [Send Feedback](https://forms.gle/KzHgXC7c16zPWhgo7)',
                        inline=False)
        embed.set_footer(text=f"Sentinel Bot | {self.bot.version}")

        async with self.bot.memcache.client() as redisConn:
            notification_channel = await redisConn.hget(guild_id, "guild_notification_channel")

        guild = self.bot.get_guild(int(guild_id))

        try:

            notification_channel = guild.get_channel(int(notification_channel))

            alert = await notification_channel.send(embed=embed)

        except (discord.HTTPException, discord.NotFound): # happen more than one can imagine :( we still would like
            # to log required data so finally clause has been added
            # the exception raises if the bot has no ability to post messages/embeds in notification channel

            pass

        finally:

            log.info(f"Discord alert about repelled userbot raid against server {guild.id} has been sent. ID of an entry associated with the userbot: {log_id}. Notification sent to channel {notification_channel.id}. ID of message (alert): {alert.id}")

    async def cog_unload(self):
        self.find_keys_older_than_5_minutes.cancel()

async def setup(bot):
    await bot.add_cog(RedisCache(bot))