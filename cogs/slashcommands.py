import datetime
import dateparser
import discord
from discord import app_commands
from discord.app_commands import Choice, checks
from discord.ext.commands import Bot, Cog
from enum import Enum
from typing import Literal
from discord.utils import format_dt
import os

from bot import Sentinel

class ActionTypes(Enum): 
    AUTOBAN_SETTING = 1         
    INTERVAL_SETTING = 2
    HOURS_SETTING = 3
    THRESHOLD_SETTING = 4
    CHANNEL_SETTING = 5

class SlashCommands(Cog):
    def __init__(self, bot):
        self.bot: Sentinel = bot

    @app_commands.command(name="nickname", description="Change Discord nickname on Wowhead's Discord server. You can change nickname once per 31 days.")
    @app_commands.guilds(discord.Object(id=107362567793422336))
    async def nickname(self, interaction: discord.Interaction, new_username: str):
        async with self.bot.memcache.client() as redisConn:
            result = await redisConn.get(f"107362567793422336:users:newusername:{interaction.user.id}")
            if result == "True":
                ttl = await redisConn.ttl(f"107362567793422336:users:newusername:{interaction.user.id}")

                current_time = datetime.datetime.now()

                # Create a timedelta object using the time difference in seconds
                timedelta = datetime.timedelta(seconds=ttl)

                # Add the timedelta to the current time to get the time difference
                time_difference = current_time + timedelta

                # Get the timedelta between the current time and the time difference
                timedelta = time_difference - current_time

                # Get the number of days in the timedelta
                days = timedelta.days

                return await interaction.response.send_message(f"You already changed your nickname in the last 31 days. You may change your nickname again in {days} days.", ephemeral=True)

        old_username = interaction.user.display_name

        await interaction.user.edit(nick=new_username, reason="The nickname changed per user's request.")

        async with self.bot.memcache.client() as redisConn:
            await redisConn.setex(f"107362567793422336:users:newusername:{interaction.user.id}", 2678400, "True")

        await interaction.response.send_message("New nickname set. Please note you won't be able to change the nickname again in 31 days.", ephemeral=True)

        guild = self.bot.get_guild(107362567793422336)

        channel = guild.get_channel(406250614012772352)

        embed = discord.Embed(title="Nickname Change", color=0xed4337, timestamp=discord.utils.utcnow())
        embed.add_field(name='A user has changed their nickname', value=f'User ID: {interaction.user.id}.\nOld nickname: {old_username}\nNew nickname: {new_username}')

        embed.set_footer(text=f"Sentinel Bot | {self.bot.version}")

        await channel.send(embed=embed)

    # @cog_ext.cog_slash(name="setinterval", description="Change designated interval between new join Events to look for.")  #   interaction.user.guild_permissions
    @app_commands.command(name="setinterval", description="Change designated interval between new join Events to look for.")
    @checks.has_permissions(ban_members=True)
    async def setinterval(self, interaction: discord.Interaction, interval: int):
        #   if ctx.message.channel.permissions_for(interaction.user).ban_members:
        if interval < 1 or interval > 60:
            return await interaction.response.send_message("New interval can't be less than 1 minute or greater than 60 minutes.", ephemeral=True)
        else:
            async with self.bot.memcache.client() as redisConn:
                await redisConn.hset(interaction.guild.id, "guild_interval", str(interval))
            async with self.bot.pool.acquire() as connection:
                async with connection.transaction():
                    query = "UPDATE t_guilds SET guild_interval = $1 WHERE guild_id = $2;"
                    await connection.execute(query, interval, interaction.guild.id)  # check
                    query = "INSERT INTO t_actionlog (guild_id, member_id, action_type, action_taken_at) VALUES ($1, $2, $3, NOW());"

                    await connection.execute(query, interaction.guild.id, interaction.user.id, 2)
            await interaction.response.send_message("New time interval set.")

    @app_commands.command(name="sethours", description="Change designated hour difference to look for.")  # interaction.user.guild_permissions
    @checks.has_permissions(ban_members=True)
    async def sethours(self, interaction: discord.Interaction, hours: int):
        #   if ctx.message.channel.permissions_for(interaction.user).ban_members:
        if hours < 1 or hours > 24:
            return await interaction.response.send_message("Hours to look for can't be less than 1 hour or greater than 24 hours.", ephemeral=True)
        else:
            async with self.bot.memcache.client() as redisConn:
                await redisConn.hset(interaction.guild.id, "guild_hours", str(hours))
            async with self.bot.pool.acquire() as connection:
                async with connection.transaction():
                    query = "UPDATE t_guilds SET guild_hours = $1 WHERE guild_id = $2;"
                    await connection.execute(query, hours, interaction.guild.id)  # check

                    query = "INSERT INTO t_actionlog (guild_id, member_id, action_type, action_taken_at) VALUES ($1, $2, $3, NOW());"

                    await connection.execute(query, interaction.guild.id, interaction.user.id, 3)
            await interaction.response.send_message("New time difference to look for (in hours) set.")

    @app_commands.command(name="sethreshold", description="Change threshold of newly joined members that would trigger antispam mechanism.")  # interaction.user.guild_permissions
    @checks.has_permissions(ban_members=True)
    async def setthreshold(self, interaction: discord.Interaction, threshold: int):
            if threshold < 2 or threshold > 50:
                return await interaction.response.send_message("Number of recently joined members that trigger antiraid mechanism can't be less than 2 or greater than 50.", ephemeral=True)
            else:
                async with self.bot.memcache.client() as redisConn:
                    await redisConn.hset(interaction.guild.id, "guild_min_members", str(threshold))
                async with self.bot.pool.acquire() as connection:
                    async with connection.transaction():
                        query = "UPDATE t_guilds SET guild_min_members = $1 WHERE guild_id = $2;"
                        await connection.execute(query, threshold, interaction.guild.id)  # check

                        query = "INSERT INTO t_actionlog (guild_id, member_id, action_type, action_taken_at) VALUES ($1, $2, $3, NOW());"

                        await connection.execute(query, interaction.guild.id, interaction.user.id, 4)
                await interaction.response.send_message("New threshold of recently joined members set.")

    @app_commands.command(name="setchannel", description="Change channel for Sentinel's ban notifications. The value must be ID of the new channel.")  # interaction.user.guild_permissions
    @checks.has_permissions(administrator=True)
    async def setchannel(self, interaction: discord.Interaction, channel: str):
        # if interaction.user.guild_permissions.administrator:
        channel = discord.utils.get(interaction.guild.channels, id=int(channel))
        if channel is not None:
            async with self.bot.memcache.client() as redisConn:
                await redisConn.hset(interaction.guild.id, "guild_notification_channel", str(channel.id))
            async with self.bot.pool.acquire() as connection:
                async with connection.transaction():
                    query = "UPDATE t_guilds SET guild_notification_channel = $1 WHERE guild_id = $2;"
                    await connection.execute(query, channel.id, interaction.guild.id)

                    query = "INSERT INTO t_actionlog (guild_id, member_id, action_type, action_taken_at) VALUES ($1, $2, $3, NOW());"

                    await connection.execute(query, interaction.guild.id, interaction.user.id, 5)
            await interaction.response.send_message(f"Now bot will send ban notifications to {channel.mention}.")
        else:
            return await interaction.response.send_message("Incorrect channel ID was provided. Please make sure the Sentinel have an access to this channel and try again.", ephemeral=True)
        # else:
        #    return await interaction.response.send_message("You don't have required permissions. Please contact your server administrator to change this parameter.", ephemeral=True)

    @app_commands.command(name='autoban', description="Turn on or turn off auto-ban mode.")
    @checks.has_permissions(ban_members=True)
    async def autoban(self, interaction: discord.Interaction, options: Literal['off', 'on']):
        if options == "on":
            async with self.bot.memcache.client() as redisConn:
                await redisConn.hset(interaction.guild.id, "guild_autoban", "1")
            async with self.bot.pool.acquire() as connection:
                async with connection.transaction():
                    query = "UPDATE t_guilds SET guild_autoban = TRUE WHERE guild_id = $1;"
                    await connection.execute(query, interaction.guild.id)
                    query = "INSERT INTO t_actionlog (guild_id, member_id, action_type, action_taken_at) VALUES ($1, $2, $3, NOW());"

                    await connection.execute(query, interaction.guild.id, interaction.user.id, 1)
            await interaction.response.send_message("Auto-ban mode is now **enabled**. Use the slash command `/autoban off` to disable the auto-ban mode.")
        else:
            async with self.bot.memcache.client() as redisConn:
                await redisConn.hset(interaction.guild.id, "guild_autoban", "0")
            async with self.bot.pool.acquire() as connection:
                query = "UPDATE t_guilds SET guild_autoban = FALSE WHERE guild_id = $1;"
                await connection.execute(query, interaction.guild.id)  # check
                query = "INSERT INTO t_actionlog (guild_id, member_id, action_type, action_taken_at) VALUES ($1, $2, $3, NOW());"

                await connection.execute(query, interaction.guild.id, interaction.user.id, 1)
            await interaction.response.send_message("Auto-ban mode is now **disabled**. Use the slash command `/autoban on` to re-enable it.")


    @app_commands.command(name="faq", description="Show list of available commands.")  # interaction.user.guild_permissions
    async def faq(self, interaction: discord.Interaction):
        embed = discord.Embed(title="List of Available Commands", color=0xed4337)
        embed.add_field(name="General Information",
                        value=f"The bot is tracking accounts that mass-joined the server within a short time span.\nThe bot will ban raiders automatically if auto-ban mode is on.",
                        inline=False)
        embed.add_field(name="/autoban on/off",
                        value="""This command is used to toggle the bot's auto-ban mode on or off. When auto-ban mode is on, the bot will automatically ban suspicious accounts that meet the criteria set by the server owner or members with "Ban Members" permissions. To turn auto-ban mode on, use the command `/autoban on`. To turn it off, use the command `/autoban off`.""",
                        inline=False)
        embed.add_field(name="/setinterval",
                        value=f"This command is used to change the default time interval (30 minutes) used by the bot to identify suspicious accounts. The time interval is used to form a list of accounts which joined the server within the given time interval and who met all other criteria. To change the time interval, use the command `/setinterval <time in minutes>`.",
                        inline=False)
        embed.add_field(name="/sethours",
                        value=f"This command is used to change the default range of hours (6 hours) used by the bot to identify suspicious accounts. The hours range is a search parameter that allows the bot to search for accounts that were created between the given hour (onwards and backwards). To change the hours range, use the command `/sethours <hours>`.",
                        inline=False)
        embed.add_field(name="/setthreshold",
                        value="This command is used to set the minimum number of recently joined members that trigger the antiraid mechanism. The antiraid mechanism is triggered when the bot detects a sudden influx of suspicious accounts. To set the minimum number of recently joined members, use the command `/setthreshold <number>`.",
                        inline=False)
        embed.add_field(name="/setchannel",
                        value="This command is used to change the channel where the bot will send ban notifications. By default, the bot creates a private notification channel upon joining a new server. To change the notification channel, use the command `/setchannel <channel id>`.",
                        inline=False)
        embed.add_field(name="/whojoined",
                        value="Get a list of Discord users who joined the server within a specified time range. The bot will try to parse the dates from the user's input.\nExample: `/whojoined February 1, 2023 3:00 PST February 16, 2023 14:00 PST`",
                        inline=False)
        embed.add_field(name="/actionlog",
                        value="Get a list of actions performed by server moderators that affect the bot's functionality, such as changing the time interval, hours, threshold, or notification channel. This can help server owners or administrators track changes made to the bot's configuration and ensure that the antiraid system is properly set up.",
                        inline=False)
        embed.set_footer(text=f"Sentinel Bot | {self.bot.version}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="actionlog", description="Check the logs of actions performed by moderators.")  # interaction.user.guild_permissions
    @checks.has_permissions(ban_members=True)
    async def actionlog(self, interaction: discord.Interaction, number_of_actions: int):
        async with self.bot.pool.acquire() as connection:
            query = "SELECT member_id, action_type, action_taken_at FROM t_actionlog WHERE guild_id = $1 ORDER BY action_taken_at DESC LIMIT $2;"

            query = await connection.fetch(query, interaction.guild.id, number_of_actions)

            embed = discord.Embed(title=f"List of last {number_of_actions} actions performed by server moderators", color=0xed4337)

            for value in query:

                performer = self.bot.get_user(value[0])

                type_of_taken_action = ActionTypes(value[1]).name

                action_taken_at = value[2]

                embed.add_field(name=f"{performer.mention} changed {type_of_taken_action} at {format_dt(action_taken_at, style='f')}", value="\u200B", inline=False)

            embed.set_footer(text=f"Sentinel Bot | {self.bot.version}")

            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="whojoined", description="Get a list of users' ID who joined the server between the specified time periods.")  # interaction.user.guild_permissions
    @checks.has_permissions(ban_members=True)
    async def whojoined(self, interaction: discord.Interaction, search_from: str, search_until: str):
        search_from = dateparser.parse(search_from, settings={'TIMEZONE': 'UTC'})
        search_until = dateparser.parse(search_until, settings={'TIMEZONE': 'UTC'})

        await interaction.response.defer() # required to avoid timeout of 3 secs set by Discord raising 404 Error: Command Not Found. See https://discordpy.readthedocs.io/en/stable/interactions/api.html?highlight=defer#discord.InteractionResponse.defer

        async with self.bot.pool.acquire() as connection:
            select_query = "SELECT member_id FROM t_users WHERE guild_id = $1 AND member_joined_at>=$2 AND member_joined_at < $3 ORDER BY member_joined_at ASC;" # limit as a test

            found_ids = await connection.fetch(select_query, interaction.guild.id, search_from, search_until)

            list_to_insert = []

            for found_id in found_ids:
                list_to_insert.append(found_id[0])
                
            insert_query = """INSERT INTO t_reports (guild_id, search_initiated_by_id, search_initiated_by_name, search_initiated_at, search_from, search_until, found_ids) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id;"""

            # Here we're using fetchval() method to get an auto-incremented ID of the report after executing the query.

            report_id = await connection.fetchval(insert_query, interaction.guild.id, interaction.user.id, interaction.user.name, datetime.datetime.now(), search_from, search_until, list_to_insert)

            print(f"Inserted row with ID: {report_id}")

            await interaction.followup.send(f"The requested report is ready. Please visit https://logs.itsuchur.dev/reports/id={report_id} to learn more.")
        

async def setup(bot):
    await bot.add_cog(SlashCommands(bot))