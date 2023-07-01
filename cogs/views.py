from discord.ext import commands
from typing import Optional

import discord

from bot import Sentinel

# Define a simple View that gives us a confirmation menu
class ConfirmationView(discord.ui.View):
    def __init__(self, *, timeout: float, author_id: int, delete_after: bool) -> None:
        super().__init__(timeout=timeout)
        self.value: Optional[bool] = None
        self.delete_after: bool = delete_after
        self.author_id: int = author_id
        self.message: Optional[discord.Message] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and interaction.user.id == self.author_id:
            return True
        else:
            await interaction.response.send_message('This confirmation dialog is not for you.', ephemeral=True)
            return False

    async def on_timeout(self) -> None:
        if self.delete_after and self.message:
            await self.message.delete()

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_response()

        self.stop()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_response()

        self.stop()

class WowheadQuickActionsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout = None)
        self.value = None

    async def disabling_buttons(self):
        for i in self.children:
            i.disabled = True

    @discord.ui.button(label='🗑️ Delete the reported message', style=discord.ButtonStyle.red, custom_id="qa:kick")
    async def qa_kick(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message(content=f'The reported message deleted by {interaction.user.mention}.', allowed_mentions=None)
            self.value = 1
            self.stop()
            await self.disabling_buttons()
            await interaction.message.edit(view=self)

    @discord.ui.button(label='🔨 Ban the author of the reported message', style=discord.ButtonStyle.red, custom_id="qa:ban")
    async def qa_ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message(content=f'Author of the reported message is now banned from the server by {interaction.user.mention}.', allowed_mentions=None)
            self.mod_action_taken_by = interaction.user
            self.value = 2
            self.stop()
            await self.disabling_buttons()
            await interaction.message.edit(view=self)

    @discord.ui.button(label='🛑 Stop receiving further reports from this user (6h)', style=discord.ButtonStyle.blurple, custom_id="qa:timeout")
    async def qa_timeout(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message(content=f"The user submitted the report is now blocked from filing reports using this system for the next 6 hours. The action taken by {interaction.user.mention}.", allowed_mentions=None)
            self.value = 3
            self.stop()
            await self.disabling_buttons()
            await interaction.message.edit(view=self)

    @discord.ui.button(label='✔️ Mark as resolved/ignored', style=discord.ButtonStyle.green, custom_id="qa:resolved")
    async def qa_resolved(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message(content=f"The report marked as resolved/ignored by {interaction.user.mention}.", allowed_mentions=None)
            self.value = 4
            self.stop()
            await self.disabling_buttons()
            await interaction.message.edit(view=self)

"""Main module"""
class Views(commands.Cog):
    __slots__ = ('bot')

    def __init__(self, bot):
        self.bot: Sentinel = bot

async def setup(bot):
    await bot.add_cog(Views(bot))