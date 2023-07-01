# -*- coding: utf-8 -*-

from discord.ext import commands
from discord.utils import format_dt
from enum import Enum
import discord
import sys

from bot import Sentinel

import logging

log = logging.getLogger(__name__)

class ActionTypes(Enum): 
    AUTOBAN_SETTING = 1         
    INTERVAL_SETTING = 2
    HOURS_SETTING = 3
    THRESHOLD_SETTING = 4
    CHANNEL_SETTING = 5

class Commands(commands.Cog):
    __slots__ = ('bot')

    def __init__(self, bot):
        self.bot: Sentinel = bot
        self.tree = self.bot.tree

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def faq(self, ctx):
        embed = discord.Embed(title="List of available commands", color=0xed4337)
        embed.add_field(name="General Information", value=f"The bot is tracking accounts that mass-joined the server "
                                                          f"within a short time span.\nThe bot bans raiders "
                                                          f"automatically given that auto-ban mode is enabled.",
                        inline=False)
        embed.add_field(name="st?autoban on/off", value="Switch to auto-ban mode. In this mode the bot automatically "
                                                        "bans suspicious accounts, relying on default parameters or "
                                                        "parameters set by `server owner` and members with `Ban "
                                                        "Members` permissions.\nExample: `st?autoban on`.\nTo exit "
                                                        "this mode, invoke `st?autoban off` command.", inline=False)
        embed.add_field(name="st?setinterval", value=f"Change default time interval (30 minutes).\nThe time interval "
                                                     f"is used to form a list of accounts, which joined the server "
                                                     f"within given time interval and who met all other criteria.",
                        inline=False)
        embed.add_field(name="st?sethours", value=f"Change default hours (6 hours).\nThese hours is search parameter "
                                                  f"allowing the bot search for accounts that were created between "
                                                  f"the given hour (onwards and backwards).", inline=False)
        embed.add_field(name="st?setthreshold", value="Set minimum number of recently joined members that trigger "
                                                      "antiraid mechanism.\nExample: `st?setthreshold 3`",
                        inline=False)
        embed.add_field(name="st?setchannel", value="Change channel where bot will send ban notifications. Please "
                                                    "note that the bot creates private notification channel "
                                                    "automatically upon joining new server.\nExample: `st?setchannel "
                                                    "#NewChannel`", inline=False)
        embed.add_field(name="st?urlfilter on/off", value="[`This is experimental feature. Proceed with caution.`] "
                                                          "Enable or disable URL filter to automatically remove "
                                                          "fraudulent links and ban poster.\nExample: `st?urlfilter "
                                                          "on`.\nTo disable the URL filter, invoke `st?urlfilter off` "
                                                          "command.", inline=False)
        embed.set_footer(text=f"Sentinel Bot | {self.bot.version}")
        await ctx.send(embed=embed)
  
    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def autoban(self, ctx, parameter: str):
        if parameter == 'on':
            async with self.bot.memcache.client() as redisConn:
                await redisConn.hset(ctx.guild.id, "guild_autoban", "1")
            async with self.bot.pool.acquire() as connection:
                async with connection.transaction():
                    query = "UPDATE t_guilds SET guild_autoban = TRUE WHERE guild_id = $1;"
                    await connection.execute(query, ctx.guild.id)

                    query = "INSERT INTO t_actionlog (guild_id, member_id, action_type, action_taken_at) VALUES ($1, $2, $3, NOW());"

                    await connection.execute(query, ctx.guild.id, ctx.author.id, 1)

            await ctx.send("Auto-ban mode is now **on**. Please invoke `st?autoban off` to exit this mode.")

            log.info(f"Action alert. {ctx.author.id} turned on autoban mode on {ctx.guild.id}.")

        elif parameter == 'off':
            async with self.bot.memcache.client() as redisConn:
                await redisConn.hset(ctx.guild.id, "guild_autoban", "0")
            async with self.bot.pool.acquire() as connection:
                async with connection.transaction():
                    query = "UPDATE t_guilds SET guild_autoban = FALSE WHERE guild_id = $1;"
                    await connection.execute(query, ctx.guild.id)   # check

                    query = "INSERT INTO t_actionlog (guild_id, member_id, action_type, action_taken_at) VALUES ($1, $2, $3, NOW());"

                    await connection.execute(query, ctx.guild.id, ctx.author.id, 1)
            await ctx.send("Auto-ban mode is now **off**. Please invoke `st?autoban on` to activate auto-ban.")

            log.info(f"Action alert. {ctx.author.id} turned off autoban mode on {ctx.guild.id}.")

        else:
            await ctx.send("Invalid argument provided. Please try again. Only `on` and `off` are considered to be "
                           "valid arguments. Example: `st?autoban off`.")
            
            log.info(f"Action alert. {ctx.author.id}'s attempt to change autoban settings on {ctx.guild.id} failed.")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def setinterval(self, ctx, new_interval: str):
        if new_interval.isdigit():
            new_interval = int(new_interval)
            if new_interval < 1 or new_interval > 60:
                await ctx.send("New interval can't be less than 1 minute or greater than 60 minutes.")
            else:
                async with self.bot.memcache.client() as redisConn:
                    await redisConn.hset(ctx.guild.id, "guild_interval", str(new_interval))
                async with self.bot.pool.acquire() as connection:
                    async with connection.transaction():
                        query = "UPDATE t_guilds SET guild_interval = $1 WHERE guild_id = $2;"
                        await connection.execute(query, new_interval, ctx.guild.id)  # check

                        query = "INSERT INTO t_actionlog (guild_id, member_id, action_type, action_taken_at) VALUES ($1, $2, $3, NOW());"

                        await connection.execute(query, ctx.guild.id, ctx.author.id, 2)
                await ctx.send("New time interval set.")
        else:
            await ctx.send("Only integers are allowed. Please try again.")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def sethours(self, ctx, new_hours: str):
        if new_hours.isdigit():
            new_hours = int(new_hours)
            if new_hours < 1 or new_hours > 24:
                await ctx.send("New value can't be less than 1 hour or greater than 24 hours.")
            else:
                async with self.bot.memcache.client() as redisConn:
                    await redisConn.hset(ctx.guild.id, "guild_hours", str(new_hours))
                async with self.bot.pool.acquire() as connection:
                    async with connection.transaction():
                        query = "UPDATE t_guilds SET guild_hours = $1 WHERE guild_id = $2;"
                        await connection.execute(query, new_hours, ctx.guild.id)  # check

                        query = "INSERT INTO t_actionlog (guild_id, member_id, action_type, action_taken_at) VALUES ($1, $2, $3, NOW());"

                        await connection.execute(query, ctx.guild.id, ctx.author.id, 3)
                await ctx.send("New time difference in hours set.")
        else:
            await ctx.send("Only integers are allowed. Please try again.")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def sethreshold(self, ctx, new_threshold: str):
        if new_threshold.isdigit():
            new_threshold = int(new_threshold)
            if new_threshold < 2 or new_threshold > 10:
                await ctx.send("Number of recently joined members that would trigger antiraid system can't be less than 2 or greater than 10.")
            else:
                async with self.bot.memcache.client() as redisConn:
                    await redisConn.hset(ctx.guild.id, "guild_min_members", str(new_threshold))
                async with self.bot.pool.acquire() as connection:
                    async with connection.transaction():
                        query = "UPDATE t_guilds SET guild_min_members = $1 WHERE guild_id = $2;"
                        await connection.execute(query, new_threshold, ctx.guild.id)  # check

                        query = "INSERT INTO t_actionlog (guild_id, member_id, action_type, action_taken_at) VALUES ($1, $2, $3, NOW());"

                        await connection.execute(query, ctx.guild.id, ctx.author.id, 4)
                await ctx.send("New threshold of recently joined members set.")
        else:
            await ctx.send("Only integers are allowed. Please try again.")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def setchannel(self, ctx, channel: discord.TextChannel):  # if don't exist INSERT 1 as member for tech reasons
        async with self.bot.memcache.client() as redisConn:
                await redisConn.hset(ctx.guild.id, "guild_notification_channel", str(channel.id))
        async with self.bot.pool.acquire() as connection:
            async with connection.transaction():
                query = "UPDATE t_guilds SET guild_notification_channel = $1 WHERE guild_id = $2;"
                await connection.execute(query, channel.id, ctx.guild.id)

                query = "INSERT INTO t_actionlog (guild_id, member_id, action_type, action_taken_at) VALUES ($1, $2, $3, NOW());"

                await connection.execute(query, ctx.guild.id, ctx.author.id, 5)
        await ctx.send(f"Now bot will send ban notifications to {channel.mention}.")

    @setchannel.error
    async def setchannel_error(self, ctx, error):
        if isinstance(error, commands.errors.ChannelNotFound):
            await ctx.send("No such channel found in this server.")

    @commands.command(hidden=True)
    @commands.guild_only()
    async def reload_ext(self, ctx, ext_name: str):
        if ctx.author.id == 173477542823460864:
            await self.bot.reload_extension(f"cogs.{ext_name}")
            await ctx.send(f"✅ The cog {ext_name} reloaded.")
        else:
            return

    @commands.command(hidden=True)
    @commands.guild_only()
    async def reboot(self, ctx):
        if ctx.author.id == 173477542823460864:
            await ctx.send("✅")
            await self.bot.close()
            sys.exit(0)
        else:
            return await ctx.send("https://open.spotify.com/track/3ARUWZ4hryYXhp6X7KHcaD?si=e9347fc50dad41e9")

    @commands.command(hidden=True)
    @commands.guild_only()
    async def bandomain(self, ctx, domain: str):
        if ctx.author.id == 173477542823460864:
            async with self.bot.memcache.client() as redisConn:
                await redisConn.hset(domain, "safe", "0")
            async with self.bot.pool.acquire() as connection:
                query = "INSERT INTO t_domains (domain, safe) VALUES ($1, FALSE) ON CONFLICT (domain) DO UPDATE SET safe = FALSE"
                await connection.execute(query, domain)
            await ctx.message.delete()
            await ctx.send(f"The domain name {domain} added to the list of banned domains.")
        else:
            return

    @commands.command(hidden=True)
    @commands.guild_only()
    async def unbandomain(self, ctx, domain: str):
        if ctx.author.id == 173477542823460864:
            async with self.bot.memcache.client() as redisConn:
                await redisConn.hset(domain, "safe", "1")
            async with self.bot.pool.acquire() as connection:
                query = "INSERT INTO t_domains (domain, safe) VALUES ($1, TRUE) ON CONFLICT (domain) DO UPDATE SET safe = TRUE"
                await connection.execute(query, domain)
            await ctx.message.delete()
            await ctx.send(f"The domain name {domain} removed from the list of banned domains.")
        else:
            return

    @commands.command(hidden=True)
    async def say(self, ctx, messagetosay: str):
        if ctx.author.id == 173477542823460864:
            wowheadModChannel = self.bot.get_channel(299346847439257601)
            # message = str(ctx.message.content)
            botmessage = ctx.message.content.split(" ")[1:]
            await wowheadModChannel.send(" ".join(botmessage))

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def whitelist(self, ctx, user_id: str):
        async with self.bot.pool.acquire() as connection:
            query = "UPDATE t_users SET is_whitelisted = TRUE WHERE member_id = $1 AND guild_id = $2"
            await connection.execute(query, int(user_id), ctx.guild.id)
        await ctx.send(f"Member with ID {user_id} is now whitelisted.")

    @commands.command(hidden=True)
    @commands.guild_only()
    async def sync_all(self, ctx):
        if ctx.author.id == 173477542823460864:
            cmds = await self.bot.tree.sync()
            print(cmds)
            await ctx.channel.send("✅")

    @commands.command(hidden=True)
    @commands.guild_only()
    async def sync_guild(self, ctx):
        if ctx.author.id == 173477542823460864:
            await self.bot.tree.sync(guild=ctx.guild)
            await ctx.channel.send("✅")

    
    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def actionlog(self, ctx, number_of_actions: int):
        async with self.bot.pool.acquire() as connection:
            query = "SELECT member_id, action_type, action_taken_at FROM t_actionlog WHERE guild_id = $1 ORDER BY action_taken_at DESC LIMIT $2;"

            query = await connection.fetch(query, ctx.guild.id, number_of_actions)

            embed = discord.Embed(title=f"List of last {number_of_actions} actions performed by server moderators", color=0xed4337)

            for value in query:

                performer = self.bot.get_user(value[0])

                type_of_taken_action = ActionTypes(value[1]).name

                action_taken_at = value[2]

                embed.add_field(name=f"{performer.mention} changed {type_of_taken_action} at {format_dt(action_taken_at, style='f')}", value="\u200B", inline=False)

            embed.set_footer(text=f"Sentinel Bot | {self.bot.version}")

            await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.guild_only()
    async def remove_redis_key(self, ctx, key):
        if ctx.author.id == 173477542823460864:
            async with self.bot.memcache.client() as redisConn:
                await redisConn.delete(key)
            await ctx.send("✅")

    @commands.command(hidden=True)
    @commands.guild_only()
    async def debug(self, ctx, key):
        if ctx.author.id == 173477542823460864:
            async with self.bot.memcache.client() as redisConn:
                redis_status = await redisConn.ping()
                if redis_status == "PONG":
                    redis_ok = "Connection to Redis is active."
        await ctx.send(f"""Redis connection: {redis_ok}.
        Latency: {round(self.bot.latency * 1000)} ms.""")

    """import asyncpg

async def print_latency():
    conn = await asyncpg.connect(database="mydb", user="postgres", password="mypassword")
    query = "EXPLAIN SELECT * FROM mytable WHERE id = 5"
    result = await conn.fetchval(query)
    execution_time = result.split("Execution time:")[1].split("ms")[0].strip()
    print(execution_time)
    await conn.close()

await print_latency()
"""


async def setup(bot):
    await bot.add_cog(Commands(bot))