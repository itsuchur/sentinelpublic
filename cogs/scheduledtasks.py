from discord.ext import commands
from discord.ext import tasks
import discord

from bot import Sentinel

class ScheduledTasks(commands.Cog):
    __slots__ = ('bot')

    def __init__(self, bot):
        self.bot: Sentinel = bot
        self.counting_servers.start()

    @tasks.loop(minutes=360)
    async def counting_servers(self) -> None:
        await self.bot.wait_until_ready()
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"over {len(self.bot.guilds)} servers"))
        

    async def cog_unload(self):
            self.counting_servers.cancel()

async def setup(bot):
    await bot.add_cog(ScheduledTasks(bot))