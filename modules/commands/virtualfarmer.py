import discord
import asyncio
import modules
import logging
from discord.ext import commands


class VirtualFarmer(commands.Cog):
    def __init__(self, bot: modules.Bot):
        self.bot = bot
        self.data = {}
        self.virtual_farmer: discord.User | None = None
        self.farm_channel: discord.TextChannel | None = None
        self.slash_command: dict[str, discord.SlashCommand | None] = {
            "farm": None
        }

async def setup(bot: modules.Bot):
    await bot.add_cog(VirtualFarmer(bot))
