import discord
from discord.ext import commands
from discord.utils import format_dt

from views import WowheadQuickActionsView

from bot import Sentinel

WOWHEAD_SERVER = discord.Object(id=107362567793422336)
MODERATOR_CHANNEL = 299346847439257601
MODLOGS_CHANNEL = 406250614012772352

WEBHOOK_CHANNELS = [612116478539464704, 1117253837099638935, 1117252244916670474]

class WowheadExclusive(commands.Cog):
    __slots__ = ('bot')

    def __init__(self, bot):
        self.bot: Sentinel = bot
        self.ctx_menu = discord.app_commands.ContextMenu(
            name='Report to Wowhead moderators',
            callback=self.reported_message,
        )
        self.bot.tree.add_command(self.ctx_menu)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)

    # You can add checks too
    # @app_commands.checks.has_permissions(ban_members=True)
    @discord.app_commands.guilds(WOWHEAD_SERVER)
    async def reported_message(self, interaction: discord.Interaction, message: discord.Message) -> None:

        async with self.bot.memcache.client() as redisConn:
            result = await redisConn.get(f"{interaction.user.id}:wowhead:blocked")
            if result == "1":
                return await interaction.response.send_message("You're temporarily blocked from filing reports using this system. Please try again later.", ephemeral=True)

        guild = self.bot.get_guild(107362567793422336)

        channel = guild.get_channel(MODERATOR_CHANNEL)

        embed = discord.Embed(title=f"A report submitted by {interaction.user}",
                                                  color=0xed4337,
                                                  timestamp=discord.utils.utcnow())
        embed.add_field(name="Content of the reported message", value=f"{message.content}", inline=False)
        embed.add_field(name="Channel the reported message posted in", value=f"{message.channel.mention}", inline=False)
        embed.add_field(name="Link to the reported message", value=f"{message.jump_url}", inline=False)
        embed.add_field(name="The reported message posted", value=f"{format_dt(message.created_at, style='R')}", inline=False)
        embed.add_field(name="Author of the reported message",
                        value=f'{message.author.mention} ({message.author.id})',
                        inline=False)
        embed.set_footer(text=f"Sentinel Bot | {self.bot.version}")

        view = WowheadQuickActionsView()

        await channel.send(embed=embed, view=view)

        await interaction.response.send_message("Thank you for your report. Our moderators will review it shortly.", ephemeral=True)

        await view.wait()

        if view.value == 1:
            await message.delete()
        elif view.value == 2:
            user_to_ban = await self.bot.fetch_user(message.author.id)
            await guild.ban(user=discord.Object(id=user_to_ban.id), reason=f"Quick action taken by {view.mod_action_taken_by}.", delete_message_seconds=604800)

            modlogs_channel = guild.get_channel(MODLOGS_CHANNEL)

            await modlogs_channel.send(f"{user_to_ban.mention} has been banned from the server by "
                                       f"{view.mod_action_taken_by.mention}. All messages posted by the banned user in "
                                       f"the last 7 days have been deleted.", allow_mentions = False)

            # await guild.ban(message.author, reason=f"Quick action taken by {view.interaction_user}.", delete_message_days=1)
        elif view.value == 3:
            async with self.bot.memcache.client() as redisConn:
                await redisConn.setex(f"{interaction.user.id}:wowhead:blocked", 21600, "1") # blocking Discord user from making further reports for 6 hours
        elif view.value == 4:
            return

    @commands.Cog.listener()
    async def on_message(self, message):

        # PUBLISHING WOWHEAD NEWS FUNCTIONALITY

        if message.channel.id in WEBHOOK_CHANNELS:

            await message.publish()

async def setup(bot):
    await bot.add_cog(WowheadExclusive(bot))