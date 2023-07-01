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

SOL_ROLES_TO_CHECK = [766136598579380285, 585536737455898626]

SOL_ROLE_TO_GIVE = 1070910334421971015

SOL_GUILD_ID = 210643527472906241

class SoL(commands.Cog):
    __slots__ = ('bot')

    def __init__(self, bot):
        self.bot: Sentinel = bot

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """The user got a new role or lost a role. Checking..."""
        guild = self.bot.get_guild(SOL_GUILD_ID)
        role_to_give = guild.get_role(SOL_ROLE_TO_GIVE)

        # Check for gained roles
        gained_roles = [role for role in after.roles if role not in before.roles]
        for new_role in gained_roles:
            if new_role.id in SOL_ROLES_TO_CHECK:
                await after.add_roles(role_to_give)

        # Check for lost roles
        lost_roles = [role for role in before.roles if role not in after.roles]
        for lost_role in lost_roles:
            if lost_role.id in SOL_ROLES_TO_CHECK:
                await after.remove_roles(role_to_give)


async def setup(bot):
    await bot.add_cog(SoL(bot))